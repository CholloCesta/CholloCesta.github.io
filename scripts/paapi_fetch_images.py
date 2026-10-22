#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Descarga metadatos e imagenes de producto via PA-API 5.0 y guarda data/paapi_imagenes.json.

Credenciales por variables de entorno (nunca en el repo):
  PAAPI_ACCESS_KEY, PAAPI_SECRET_KEY, PAAPI_PARTNER_TAG, PAAPI_MARKETPLACE

Uso:
  python scripts/paapi_fetch_images.py                      # usa data/productos_paapi.json
  python scripts/paapi_fetch_images.py --asins A1,B2         # ASIN sueltos
  python scripts/paapi_fetch_images.py --search "nombre"     # busca por palabras
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paapi_client import ProductAdvertisingAPI, PAAPIError

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "data", "paapi_imagenes.json")
CATALOGO = os.path.join(RAIZ, "data", "productos_paapi.json")


def cargar_previas():
    if os.path.isfile(SALIDA):
        with open(SALIDA, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar(datos):
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("Guardado", SALIDA, "-", len(datos), "productos")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asins", default="")
    ap.add_argument("--search", default="")
    ap.add_argument("--out", default=SALIDA)
    args = ap.parse_args()

    try:
        api = ProductAdvertisingAPI()
    except Exception as e:
        print("ERROR:", e)
        print("Revisa PAAPI_ACCESS_KEY / PAAPI_SECRET_KEY y que tu cuenta tenga acceso a la PA-API.")
        return 2

    asins = []
    if args.asins:
        asins = [a.strip().upper() for a in args.asins.split(",") if a.strip()]
    elif os.path.isfile(CATALOGO):
        with open(CATALOGO, encoding="utf-8") as f:
            cat = json.load(f)
        for pagina, items in cat.items():
            for it in items:
                asins.append(it["asin"])
    asins = list(dict.fromkeys(asins))
    print("ASIN a consultar:", len(asins))

    datos = cargar_previas()
    nuevos = [a for a in asins if a not in datos]
    if nuevos:
        try:
            items = api.get_items(nuevos)
        except PAAPIError as e:
            print("ERROR PA-API:", e)
            return 3
        for asin, item in items.items():
            url = api.best_image(item)
            datos[asin] = {
                "imagen": url,
                "titulo": api.item_title(item),
                "precio": api.item_price(item),
                "url": item.get("DetailPageURL", ""),
            }
        guardar(datos)

    if args.search:
        try:
            res = api.search_items(args.search, item_count=10)
            for item in res:
                asin = item.get("ASIN")
                if not asin:
                    continue
                datos[asin] = {
                    "imagen": api.best_image(item),
                    "titulo": api.item_title(item),
                    "precio": api.item_price(item),
                    "url": item.get("DetailPageURL", ""),
                }
            guardar(datos)
        except PAAPIError as e:
            print("ERROR PA-API (search):", e)
            return 3

    sin_imagen = [a for a, d in datos.items() if not d.get("imagen")]
    print("Productos con imagen:", sum(1 for d in datos.values() if d.get("imagen")),
          "| sin imagen:", len(sin_imagen))
    return 0


if __name__ == "__main__":
    sys.exit(main())
