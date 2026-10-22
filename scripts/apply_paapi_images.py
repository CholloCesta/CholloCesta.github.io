#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sustituye los logotipos / imagenes de categoria por la FOTO REAL del producto (PA-API 5.0).

El emparejado se hace por indice de figura (ver data/productos_paapi.json), no por
busqueda de texto, porque el enlace de Amazon puede ser un enlace corto amzn.to.

Reglas de Amazon que esta script respeta:
  - la imagen se enlaza al producto (envoltorio <a> con el enlace de afiliado),
  - no se recorta ni se distorsiona (object-fit: contain),
  - la imagen se sirve desde la URL que devuelve la API (no se almacena ni se copia),
  - el pie indica "Imagen del producto - Amazon" con enlace al articulo.

Uso:  python scripts/apply_paapi_images.py [--dry-run]
"""
import argparse, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, "data", "paapi_imagenes.json")
CATALOGO = os.path.join(RAIZ, "data", "productos_paapi.json")
TAG = os.environ.get("PAAPI_PARTNER_TAG", "chollocesta-21")

FIG = re.compile(r'<figure class="cat-img[^"]*">.*?</figure>', re.S)

CSS = (
    ".cat-img.paapi{background:#fff;padding:0}"
    ".cat-img.paapi a{display:block;background:#fff}"
    ".cat-img.paapi img{display:block;margin:0 auto;object-fit:contain;background:#fff;"
    "aspect-ratio:auto;max-height:320px;width:auto;max-width:100%;padding:8px}"
    ".cat-img.paapi figcaption{text-align:center;background:#f9fafb}"
)


def cargar(ruta):
    if not os.path.isfile(ruta):
        return {}
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    datos = cargar(DATOS)
    catalogo = cargar(CATALOGO)
    if not datos:
        print("Falta data/paapi_imagenes.json: ejecuta antes scripts/paapi_fetch_images.py")
        return 2
    if not catalogo:
        print("Falta data/productos_paapi.json")
        return 2

    total = 0
    for pagina, items in catalogo.items():
        ruta = os.path.join(RAIZ, pagina)
        if not os.path.isfile(ruta):
            continue
        with open(ruta, encoding="utf-8") as f:
            html = f.read()
        original = html
        for it in items:
            asin = it.get("asin")
            info = datos.get(asin)
            if not info or not info.get("imagen"):
                continue
            idx = it.get("figura")
            if idx is None:
                continue
            figuras = list(FIG.finditer(html))
            if idx >= len(figuras):
                continue
            m = figuras[idx]
            enlace = "https://www.amazon.es/dp/%s?tag=%s" % (asin, TAG)
            alt = (info.get("titulo") or it.get("nombre") or asin)[:120]
            alt = alt.replace('"', "&quot;")
            fig = ('<figure class="cat-img paapi">'
                   '<a href="%s" target="_blank" rel="nofollow sponsored noopener">'
                   '<img src="%s" alt="%s" loading="lazy"></a>'
                   '<figcaption>Imagen del producto - Amazon - '
                   '<a href="%s" target="_blank" rel="nofollow sponsored noopener">Ver el art&iacute;culo</a>'
                   '</figcaption></figure>') % (enlace, info["imagen"], alt, enlace)
            html = html[:m.start()] + fig + html[m.end():]
            total += 1
        if html != original:
            if CSS not in html:
                html = html.replace("</style>", CSS + "\n</style>", 1)
            if args.dry_run:
                print("[dry-run] %s: %d productos con foto real (acumulado %d)" % (pagina, len(items), total))
            else:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(html)
                print("Actualizado", pagina)
    print("Total productos con foto real de PA-API:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
