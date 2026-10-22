#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sustituye los logotipos/imagenes de categoria por la FOTO REAL del producto (PA-API 5.0).

Reglas de Amazon que esta script respeta:
  - la imagen se enlaza al producto (envoltorio <a> con el enlace de afiliado),
  - no se reescala con recorte (object-fit: contain, sin distortions),
  - la imagen se sirve desde la URL que devuelve la API (no se almacena ni se copia),
  - se mantiene el pie "Imagen del producto - Amazon" con enlace al producto.

Uso:  python scripts/apply_paapi_images.py [--dry-run]
"""
import argparse, json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(RAIZ, "data", "paapi_imagenes.json")
CATALOGO = os.path.join(RAIZ, "data", "productos_paapi.json")
TAG = os.environ.get("PAAPI_PARTNER_TAG", "chollocesta-21")

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
        print("Sin data/paapi_imagenes.json: ejecuta antes scripts/paapi_fetch_images.py")
        return 2

    total = 0
    for pagina, items in catalogo.items():
        ruta = os.path.join(RAIZ, pagina)
        if not os.path.isfile(ruta):
            continue
        with open(ruta, encoding="utf-8") as f:
            html = f.read()
        original = html
        usados = set()
        for it in items:
            asin = it["asin"]
            if asin in usados:
                continue
            info = datos.get(asin)
            if not info or not info.get("imagen"):
                continue
            usados.add(asin)
            enlace = f"https://www.amazon.es/dp/{asin}?tag={TAG}"
            alt = (info.get("titulo") or it.get("nombre") or asin)[:120]
            fig = (f'<figure class="cat-img paapi">'
                   f'<a href="{enlace}" target="_blank" rel="nofollow sponsored noopener">'
                   f'<img src="{info["imagen"]}" alt="{alt}" loading="lazy"></a>'
                   f'<figcaption>Imagen del producto - Amazon - '
                   f'<a href="{enlace}" target="_blank" rel="nofollow sponsored noopener">Ver el art&iacute;culo</a>'
                   f'</figcaption></figure>')
            # sustituye la figura que sigue al enlace de ese ASIN
            patron = re.compile(
                r'<figure class="cat-img[^"]*">.*?</figure>(?=(?:(?!<figure).)*?' + re.escape(asin) + r')',
                re.S)
            html, n = patron.subn(fig, html, count=1)
            if n == 0:
                # fallback: primera figura de la pagina cuyo bloque contenga el ASIN
                continue
            total += 1
        if html != original:
            if CSS not in html:
                html = html.replace("</style>", CSS + "\n</style>", 1)
            if args.dry_run:
                print(f"[dry-run] {pagina}: {total} productos con foto real (acumulado)")
            else:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"Actualizado {pagina}")
    print("Total productos con foto real de PA-API:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
