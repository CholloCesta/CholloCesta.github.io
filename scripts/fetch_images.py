# -*- coding: utf-8 -*-
"""
CholloCesta · Descargador de imágenes con licencia libre
-------------------------------------------------------
Descarga imágenes para las fichas de producto usando WIKIMEDIA COMMONS
(repositorio de archivos libres con licencia Creative Commons / dominio público).

NO se descargan imágenes de Amazon: reutilizar las fotos de catálogo de
Amazon vulnera las condiciones del Programa de Afiliados y las directrices
de marca de Amazon. Aquí sólo se usan imágenes libres, con su autoría y
licencia registradas para poder citarlas correctamente.

Uso:  python3 scripts/fetch_images.py
Salida: img/*.jpg , data/imagenes.json , creditos-imagenes.html
"""
import json
import os
import re
import time
import unicodedata
import requests

ESTILO_PRODUCTO = {"lavavajillas"}

UA = "CholloCestaBot/1.0 (https://chollocesta.github.io; 2025generation@gmail.com)"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG_DIR = os.path.join(ROOT, "img")
DATA_DIR = os.path.join(ROOT, "data")

# Licencias permitidas: uso comercial permitido, siempre con atribución.
LICENSE_OK = ("cc0", "public domain", "cc by", "cc-by", "pd-", "attribution")
LICENSE_URL = {
    "cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "cc by 2.0": "https://creativecommons.org/licenses/by/2.0/",
    "cc by 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "cc by 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "cc by-sa 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "cc by-sa 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "cc by-sa 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
}

# categoria -> (consulta en Commons, texto alternativo, titulo visible)
CATEGORIAS = {
    "smartwatch":    ("smartwatch wrist watch",     "Reloj inteligente",              "Reloj inteligente"),
    "movil":         ("smartphone mobile phone",    "Teléfono móvil",                 "Móvil"),
    "portatil":      ("laptop computer notebook",   "Portátil",                       "Portátil"),
    "auriculares":   ("headphones earbuds wireless","Auriculares inalámbricos",       "Auriculares"),
    "altavoz":       ("bluetooth speaker portable", "Altavoz Bluetooth",              "Altavoz"),
    "aspirador":     ("robot vacuum cleaner",       "Robot aspirador",                "Robot aspirador"),
    "secador":       ("hair dryer",                 "Secador de pelo",                "Secador de pelo"),
    "champu":        ("shampoo bottle hair care",   "Champú",                         "Champú"),
    "crema":         ("cosmetic cream jar moisturizer", "Crema cosmética",             "Cosmética"),
    "serum":         ("face serum skincare bottle", "Sérum facial",                   "Sérum facial"),
    "perfume":       ("perfume fragrance bottle",    "Perfume",                        "Perfume"),
    "ambientador":   ("diffuser reed incense home fragrance", "Ambientador",         "Ambientador"),
    "lavavajillas":  ("Finish Quantum",              "Envase de Finish Quantum, pastillas de lavavajillas de la misma gama", "Pastillas de lavavajillas"),
    "lavadora":      ("washing machine laundry",    "Lavadora",                       "Lavadora"),
    "detergente":    ("laundry detergent",          "Detergente",                     "Detergente"),
    "limpieza":      ("cleaning spray products",    "Productos de limpieza",          "Limpieza"),
    "capsulas-cafe": ("coffee capsules",             "Cápsulas de café",               "Cápsulas de café"),
    "cafe-molido":   ("ground coffee beans",        "Café molido en granos",           "Café molido"),
    "barista":       ("espresso machine coffee",    "Cafetera de espresso",            "Cafetera"),
    "aceite":        ("olive oil bottle",           "Aceite de oliva",                "Aceite de oliva"),
    "panales":       ("baby diapers nappy",         "Pañales para bebé",              "Pañales"),
    "toallitas":     ("baby wipes",                 "Toallitas para bebé",            "Toallitas"),
    "dientes":       ("toothpaste toothbrush",      "Pasta de dientes",               "Higiene dental"),
    "fitness":       ("dumbbell gym fitness",       "Equipo de fitness",              "Fitness en casa"),
    "regalo":        ("gift box present",           "Caja de regalo",                 "Regalo"),
}


def slug(txt):
    t = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-zA-Z0-9]+", "-", t)).strip("-").lower()


def clean_html(txt):
    if not txt:
        return ""
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = txt.replace("&amp;", "&").replace("&quot;", '"').replace("&#039;", "'")
    return re.sub(r"\s+", " ", txt).strip()


def license_ok(name):
    n = (name or "").lower()
    if not n:
        return False
    if "fair use" in n or "non-free" in n:
        return False
    return any(k in n for k in LICENSE_OK)


def search_commons(query, limit=8):
    r = requests.get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": "filetype:bitmap " + query, "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 1200,
    }, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    pages = (r.json().get("query") or {}).get("pages") or {}
    res = []
    for p in pages.values():
        info = (p.get("imageinfo") or [{}])[0]
        if not info.get("url"):
            continue
        if (info.get("mime") or "") not in ("image/jpeg", "image/png"):
            continue
        em = info.get("extmetadata") or {}

        def g(k):
            return (em.get(k) or {}).get("value", "")
        w, h = info.get("width") or 0, info.get("height") or 0
        if w < 900 or h < 600:          # calidad mínima
            continue
        res.append({
            "titulo": re.sub(r"^File:", "", p.get("title") or ""),
            "url": info.get("thumburl") or info.get("url"),
            "original": info.get("url"),
            "licencia": clean_html(g("LicenseShortName")),
            "licencia_url": g("LicenseUrl") or LICENSE_URL.get(clean_html(g("LicenseShortName")).lower(), ""),
            "autor": clean_html(g("Artist")) or "Wikimedia Commons",
            "fuente": info.get("descriptionurl") or "",
        })
    return res


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    catalogo = {}
    for cat, (query, alt, titulo) in CATEGORIAS.items():
        try:
            res = search_commons(query)
        except Exception as e:
            print("ERROR", cat, e)
            continue
        elegidas = [x for x in res if license_ok(x["licencia"])]
        if not elegidas:
            print("SIN LICENCIA OK:", cat, "->", [x["licencia"] for x in res[:4]])
            continue
        elegido = elegidas[0]
        fname = cat + ".jpg"
        destino = os.path.join(IMG_DIR, fname)
        try:
            img = requests.get(elegido["url"], headers={"User-Agent": UA}, timeout=60)
            if img.status_code != 200 or len(img.content) < 5000:
                print("DESCARGA KO", cat, img.status_code)
                continue
            with open(destino, "wb") as f:
                f.write(img.content)
        except Exception as e:
            print("ERROR descarga", cat, e)
            continue
        catalogo[cat] = {
            "archivo": "img/" + fname,
            "estilo": "producto" if cat in ESTILO_PRODUCTO else "",
            "titulo": titulo,
            "alt": alt,
            "autor": elegido["autor"],
            "licencia": elegido["licencia"],
            "licencia_url": elegido["licencia_url"],
            "fuente": elegido["fuente"],
            "titulo_original": elegido["titulo"],
        }
        print("OK", cat, "<-", elegido["titulo"][:50], "|", elegido["licencia"])
        time.sleep(0.4)

    with open(os.path.join(DATA_DIR, "imagenes.json"), "w") as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)
    print("Total categorías con imagen:", len(catalogo))


if __name__ == "__main__":
    main()
