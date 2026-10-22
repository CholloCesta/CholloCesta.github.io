# -*- coding: utf-8 -*-
"""
CholloCesta · Inyecta las imágenes de licencia libre en las fichas
---------------------------------------------------------------
- Sustituye cualquier imagen hotlinkeada de Amazon (m.media-amazon.com)
  por la imagen de categoría local con licencia Creative Commons.
- Sustituye los placeholders (via.placeholder.com) por imágenes reales.
- Inserta la imagen de categoría en las tarjetas de producto.
- Añade el pie de foto con la atribución y el enlace a la página de créditos.
- Añade el enlace "Créditos de imágenes" al pie de todas las páginas.

Uso: python3 scripts/apply_images.py [--dir .]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(ROOT, "data", "imagenes.json")

CSS = """
  /* ---- Imágenes de categoría con licencia libre ---- */
  .cat-img{margin:0 0 14px 0;border-radius:12px;overflow:hidden;background:#f3f4f6;border:1px solid #e5e7eb}
  .cat-img img{display:block;width:100%;height:auto;object-fit:cover;aspect-ratio:16/10}
  .cat-img figcaption{font-size:11px;color:#6b7280;padding:6px 9px;line-height:1.4;background:#fff}
  .cat-img figcaption a{color:#0284c7;text-decoration:none}
  .cat-hero{margin:20px 0 26px 0;border-radius:16px;overflow:hidden;border:1px solid #e5e7eb;background:#fff}
  .cat-hero img{display:block;width:100%;height:auto;object-fit:cover;aspect-ratio:16/7}
  .cat-hero figcaption{font-size:12px;color:#6b7280;padding:9px 14px;line-height:1.5}
  .cat-hero figcaption a{color:#0284c7;text-decoration:none}
  /* ---- Imágenes de producto real (foto del producto con licencia libre) ---- */
  .cat-img.product{background:#fff}
  .cat-img.product img{object-fit:contain;background:#fff;aspect-ratio:auto;max-height:240px;padding:12px}
  .cat-hero.product{background:#fff;border-color:#e2e8f0}
  .cat-hero.product img{object-fit:contain;background:#fff;aspect-ratio:auto;max-height:420px;padding:16px}
"""

# página -> (categoría, modo)  modo: cards | hero | none
PAGE_MAP = {
    "smartwatches.html":              ("smartwatch", "cards"),
    "moviles.html":                   ("movil", "cards"),
    "informatica.html":               ("portatil", "cards"),
    "altavoces-bluetooth.html":        ("altavoz", "cards"),
    "aspirador.html":                 ("aspirador", "cards"),
    "secadores.html":                 ("secador", "cards"),
    "champu.html":                    ("champu", "cards"),
    "crema.html":                     ("crema", "cards"),
    "belleza.html":                   ("crema", "cards"),
    "cuidado-facial.html":            ("serum", "cards"),
    "serums-acido-hialuronico.html":  ("serum", "cards"),
    "belleza-serums.html":            ("serum", "cards"),
    "cremas-solares-corporales.html": ("crema", "cards"),
    "cremas-solares-seleccion-completa.html": ("crema", "cards"),
    "ambientador.html":               ("ambientador", "cards"),
    "lavavajillas-1.html":            ("lavavajillas", "cards"),
    "lavadoras-secadoras.html":       ("lavadora", "cards"),
    "limpiar-lavadora.html":          ("lavadora", "cards"),
    "detergente-1.html":              ("detergente", "cards"),
    "limpieza.html":                  ("limpieza", "cards"),
    "cafe-capsula.html":              ("capsulas-cafe", "cards"),
    "cafe-1.html":                    ("cafe-molido", "cards"),
    "cafe-barato.html":               ("cafe-molido", "hero"),
    "aceite-oliva.html":              ("aceite", "cards"),
    "panales-talla-4.html":           ("panales", "cards"),
    "toallitas-humedas-bebe.html":    ("toallitas", "cards"),
    "pasta-dientes.html":             ("dientes", "cards"),
    "entrenamiento-en-casa-fitness.html": ("fitness", "cards"),
    "regalos.html":                   ("regalo", "cards"),
    "electronica.html":               ("altavoz", "hero"),
    "chollocesta_electronica.html":   ("altavoz", "hero"),
    "consumibles.html":               ("limpieza", "hero"),
    "tecnologia.html":                ("movil", "hero"),
    "hogar.html":                     ("limpieza", "hero"),
    "ofertas.html":                   (None, "auto"),
    "index.html":                     (None, "auto"),
}

# palabras clave del nombre del producto -> categoría
KEYWORDS = [
    ("secador", "secador"), ("aspirador", "aspirador"), ("robot", "aspirador"),
    ("auricular", "auriculares"), ("altavoz", "altavoz"), ("speaker", "altavoz"),
    ("smartwatch", "smartwatch"), ("reloj", "smartwatch"), ("wearable", "smartwatch"),
    ("móvil", "movil"), ("movil", "movil"), ("iphone", "movil"), ("smartphone", "movil"),
    ("portátil", "portatil"), ("portatil", "portatil"), ("laptop", "portatil"),
    ("portatiles", "portatil"), ("portátiles", "portatil"), ("monitor", "portatil"),
    ("café", "capsulas-cafe"), ("cafe", "capsulas-cafe"), ("cápsula", "capsulas-cafe"),
    ("capsula", "capsulas-cafe"), ("cafetera", "barista"), ("espresso", "barista"),
    ("champú", "champu"), ("champu", "champu"), ("mascarilla capilar", "champu"),
    ("crema", "crema"), ("sérum", "serum"), ("serum", "serum"), ("hidratante", "crema"),
    ("perfume", "perfume"), ("fragua", "perfume"), ("difusor", "ambientador"),
    ("ambientador", "ambientador"), ("difusores", "ambientador"),
    ("lavavajillas", "lavavajillas"), ("lavadora", "lavadora"), ("secadora", "lavadora"),
    ("detergente", "detergente"), ("limpiador", "limpieza"), ("lejía", "limpieza"),
    ("aceite", "aceite"), ("oliva", "aceite"), ("pañal", "panales"), ("panal", "panales"),
    ("toallita", "toallitas"), ("pasta de dientes", "dientes"), ("dentífrico", "dientes"),
    ("mancuernas", "fitness"), ("fitness", "fitness"), ("regalo", "regalo"),
    ("auriculares", "auriculares"), ("micro", "auriculares"),
]


HERO = {"index.html": "cafe-molido", "ofertas.html": "altavoz"}


def cat_from_text(text):
    t = (text or "").lower()
    for k, c in KEYWORDS:
        if k in t:
            return c
    return None


def figure(cat, img, cls="cat-img"):
    v = img[cat]
    producto = v.get("estilo") == "producto"
    extra = " product" if producto else ""
    cap = ("Imagen del producto de la misma gama (ilustrativa) · " if producto
           else "Imagen ilustrativa de la categoría · ")
    return (
        '<figure class="%s%s">'
        '<img src="%s" alt="%s" loading="lazy" width="640" height="400">'
        '<figcaption>%s'
        '<a href="creditos-imagenes.html">Créditos y licencia</a></figcaption>'
        '</figure>'
    ) % (cls, extra, v["archivo"], v["alt"], cap)


def add_css(html):
    if ".cat-hero.product" in html:
        return html
    # quitar el bloque anterior para no duplicar reglas
    html = re.sub(r"\s*/\* ---- Imágenes de categoría con licencia libre ---- \*/"
                  r".*?\.cat-hero figcaption a\{color:#0284c7;text-decoration:none\}", "", html, flags=re.S)
    m = re.search(r"</style>", html)
    if not m:
        return html
    return html[:m.start()] + CSS + html[m.start():]


def add_footer_link(html):
    if "creditos-imagenes.html" in html and "Créditos de imágenes" in html:
        return html
    # añadir enlace al pie
    m = re.search(r"<footer[^>]*>(.*?)</footer>", html, re.S)
    link = ' <a href="creditos-imagenes.html">Créditos de imágenes</a>'
    if m:
        body = m.group(1)
        new_body = body.replace("</footer>", "") + link + "\n  </footer>"
        return html[:m.start(1)] + new_body + html[m.end(1):]
    # si no hay footer, añadirlo antes de </body>
    if "</body>" in html:
        foot = ('<footer style="margin-top:40px;background:#111827;color:#9ca3af;padding:22px;'
                'text-align:center;font-size:.85rem;border-radius:12px">'
                '<a href="index.html">Inicio</a> · <a href="aviso-legal.html">Aviso Legal</a> · '
                '<a href="politica-privacidad.html">Privacidad</a> · '
                '<a href="afiliados.html">Afiliados</a> · '
                '<a href="creditos-imagenes.html">Créditos de imágenes</a>'
                '</footer>\n</body>')
        return html.replace("</body>", foot)
    return html


def replace_amazon_images(html, cat, img):
    """Sustituye imágenes de Amazon o placeholders por la imagen local."""
    def rep(m):
        try:
            alt = m.group("alt") or ""
        except (IndexError, re.error):
            alt = ""
        return '<img src="%s" alt="%s" loading="lazy" width="640" height="400">' % (
            img[cat]["archivo"], alt or img[cat]["alt"])
    html = re.sub(r'<img\b(?P<attrs>[^>]*?)src="https://m\.media-amazon\.com[^"]*"(?P<attrs2>[^>]*?)/?>',
                  lambda m: rep(m), html, flags=re.I | re.S)
    html = re.sub(r'<img\b(?=[^>]*src="https://via\.placeholder\.com)[^>]*?/?>',
                  lambda m: rep(m), html, flags=re.I | re.S)
    return html


def replace_hotlinked_imgs(html, cat, img):
    """Sustituye cualquier <img> que apunte a Amazon o a un placeholder."""
    if cat not in img:
        return html
    target = img[cat]["archivo"]
    alt_def = img[cat]["alt"]

    def fix_tag(m):
        tag = m.group(0)
        amz = re.search(r'src="([^"]*(?:media-amazon\.com|amzn\.to|images-na\.ssl-images-amazon\.com)[^"]*)"', tag, re.I)
        ph = re.search(r'src="([^"]*via\.placeholder\.com[^"]*)"', tag, re.I)
        if not amz and not ph:
            return tag
        alt = re.search(r'alt="([^"]*)"', tag)
        altv = alt.group(1) if alt and alt.group(1) else alt_def
        return '<img src="%s" alt="%s" loading="lazy" width="640" height="400">' % (target, altv)

    html = re.sub(r'<img\b[^>]*>', fix_tag, html, flags=re.I)
    # limpiar onerror que apunten a placeholders
    html = re.sub(r'\s+onerror="[^"]*via\.placeholder[^"]*"', "", html, flags=re.I)
    return html


def inject_table_rows(html, cat, img):
    """Inserta la imagen de categoría en la primera celda de cada fila de producto."""
    if cat not in img:
        return html
    out = []
    pos = 0
    row = re.compile(r"<tr\b[^>]*>")
    for m in row.finditer(html):
        out.append(html[pos:m.end()])
        nxt = row.search(html, m.end())
        end = nxt.start() if nxt else min(len(html), m.end() + 3000)
        body = html[m.end():end]
        if ("amazon.es" in body or "amzn.to" in body) and "<img" not in body:
            td = re.search(r"<td\b[^>]*>", body)
            if td:
                body = body[:td.end()] + figure(cat, img) + body[td.end():]
        out.append(body)
        pos = end
    out.append(html[pos:])
    return "".join(out)


def inject_cards(html, cat, img):
    """Inserta la imagen de categoría en cada tarjeta de producto."""
    out = []
    pos = 0
    pattern = re.compile(r'<(div|article)\s+class="([^"]*\bcard\b[^"]*)"\s*>')
    for m in pattern.finditer(html):
        out.append(html[pos:m.end()])
        # contenido hasta la siguiente tarjeta
        nxt = pattern.search(html, m.end())
        end = nxt.start() if nxt else min(len(html), m.end() + 4000)
        body = html[m.end():end]
        if ("amazon.es" in body or "amzn.to" in body) and "<img" not in body and cat in img:
            out.append(figure(cat, img))
        pos = m.end()
    out.append(html[pos:])
    return "".join(out)


def inject_hero(html, cat, img):
    if cat not in img:
        return html
    if 'class="cat-hero' in html:
        return html
    m = re.search(r"(<h1[^>]*>.*?</h1>)", html, re.S)
    if not m:
        return html
    hero = figure(cat, img, "cat-hero")
    return html[:m.end()] + "\n  " + hero + html[m.end():]


def inject_auto(html, img):
    """Asigna imagen por producto según el nombre (para index y ofertas)."""
    blocks = re.split(r'(?=<(?:div|article)\s+class="[^"]*\b(?:deal-card|card)\b[^"]*"\s*>)', html)
    out = []
    for b in blocks:
        m = re.search(r'<(?:div|article)\s+class="[^"]*\b(?:deal-card|card)\b[^"]*"\s*>', b)
        if not m:
            out.append(b)
            continue
        title = ""
        for pat in (r'<h[234][^>]*>(.*?)</h[234]>', r'class="card-title"[^>]*>(.*?)<',
                    r'class="card-name"[^>]*>(.*?)<', r'class="name"[^>]*>(.*?)<'):
            tm = re.search(pat, b, re.S)
            if tm:
                title = re.sub(r"<[^>]+>", "", tm.group(1)).strip()
                break
        if not title:
            tm = re.search(r'class="(?:card-title|card-name|name|product)"[^>]*>([^<]{3,80})<', b)
            if tm:
                title = tm.group(1).strip()
        cat = cat_from_text(title)
        if cat and cat in img and "<img" not in b:
            b = b[:m.end()] + figure(cat, img) + b[m.end():]
        out.append(b)
    return "".join(out)


def main():
    with open(IMAGES, encoding="utf-8") as f:
        img = json.load(f)
    d = os.path.join(ROOT, "pages") if os.path.isdir(os.path.join(ROOT, "pages")) else ROOT
    changed = []
    for fname, (cat, mode) in PAGE_MAP.items():
        path = os.path.join(d, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
        orig = html
        if mode == "cards" and cat in img:
            html = replace_hotlinked_imgs(html, cat, img)
            html = inject_cards(html, cat, img)
            html = inject_table_rows(html, cat, img)
        elif mode == "hero":
            html = replace_hotlinked_imgs(html, cat, img) if cat in img else html
            html = inject_hero(html, cat, img)
        elif mode == "auto":
            html = inject_auto(html, img)
            html = replace_hotlinked_imgs(html, "movil", img) if "movil" in img else html
            html = inject_hero(html, HERO.get(fname, "regalo"), img)
        if mode == "cards":
            html = inject_hero(html, cat, img)
        html = add_css(html)
        html = add_footer_link(html)
        if html != orig:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            changed.append(fname)
    print("Páginas actualizadas:", len(changed))
    for c in changed:
        print("  -", c)


if __name__ == "__main__":
    main()
