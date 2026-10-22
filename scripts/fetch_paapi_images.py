#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consulta la PA-API 5.0 y guarda las imágenes reales de cada producto.

Entrada : data/paapi_catalog.json  (catálogo de productos: página, nombre, ASIN/consulta)
Salida  : data/imagenes_paapi.json  (URL de imagen, título, precio y fecha de consulta)

Uso:
    python scripts/fetch_paapi_images.py            # consulta real
    python scripts/fetch_paapi_images.py --dry-run  # simula sin llamar a la API
    python scripts/fetch_paapi_images.py --mock      # genera datos de prueba (sin API)

Las credenciales se leen del entorno (PAAPI_ACCESS_KEY, PAAPI_SECRET_KEY).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paapi_client as pa  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO = os.path.join(RAIZ, "data", "paapi_catalog.json")
SALIDA = os.path.join(RAIZ, "data", "imagenes_paapi.json")


def cargar_catalogo():
    with open(CATALOGO, encoding="utf-8") as f:
        return json.load(f)


def main():
    dry = "--dry-run" in sys.argv
    mock = "--mock" in sys.argv
    catalogo = cargar_catalogo()
    productos = catalogo.get("productos", catalogo if isinstance(catalogo, list) else [])
    print(f"Catálogo: {len(productos)} productos")

    if mock:
        datos = {"generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "modo": "mock", "imagenes": {}}
        for p in productos:
            datos["imagenes"][p["clave"]] = {
                "asin": p.get("asin") or "B0MOCK0000",
                "titulo": p["nombre"],
                "imagen": f"https://m.media-amazon.com/images/I/mock-{p['clave']}.jpg",
                "precio": 19.99,
                "consulta": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        with open(SALIDA, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        print("Datos de prueba escritos en", SALIDA)
        return 0

    if dry:
        faltan = [p for p in productos if not p.get("asin")]
        print(f"  {len(productos) - len(faltan)} con ASIN (GetItems)")
        print(f"  {len(faltan)} por búsqueda (SearchItems)")
        for p in faltan[:10]:
            print("   ·", p["clave"], "->", p.get("consulta"))
        print("Simulación terminada. No se ha llamado a la API.")
        return 0

    try:
        pa._credenciales()
    except pa.PaApiError as e:
        print("AVISO:", e)
        print("Se deja data/imagenes_paapi.json sin cambios (se mantienen los logotipos).")
        return 0

    resultados = {}
    for i, p in enumerate(productos, 1):
        clave = p["clave"]
        item = None
        try:
            if p.get("asin"):
                items = pa.get_items([p["asin"]])
                item = items[0] if items else None
            else:
                items = pa.search_items(p.get("consulta") or p["nombre"], item_count=5)
                item = items[0] if items else None
        except Exception as e:  # noqa: BLE001 - se registra y se sigue
            print(f"  [{i}/{len(productos)}] {clave}: error {e}")
            time.sleep(2)
            continue
        img = pa.imagen_principal(item) if item else None
        if not img:
            print(f"  [{i}/{len(productos)}] {clave}: sin imagen")
            time.sleep(1)
            continue
        resultados[clave] = {
            "asin": (item.get("ASIN") if item else p.get("asin")),
            "titulo": pa.titulo(item),
            "imagen": img,
            "precio": pa.precio(item),
            "consulta": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        print(f"  [{i}/{len(productos)}] {clave}: OK {resultados[clave]['imagen'][:70]}")
        time.sleep(1.2)   # la PA-API limita a 1 petición por segundo y 8 TPS

    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump({
            "generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "modo": "real",
            "imagenes": resultados,
        }, f, ensure_ascii=False, indent=2)
    print(f"
Guardadas {len(resultados)} imágenes en {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
