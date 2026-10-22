#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Descarga los logotipos de marca desde Wikimedia Commons y guarda sus atribuciones.

Uso:  python scripts/fetch_logos.py
Salida: img/marcas/<slug>.<ext>  y  data/marcas.json

Los logotipos se usan de forma meramente identificativa (indicar a qué marca
pertenece cada producto). Cada archivo conserva su licencia y autoría.
"""
import base64, json, os, re, sys, time
import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "CholloCestaBot/1.0 (https://chollocesta.github.io/)"}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(RAIZ, "img", "marcas")

# slug -> (archivo en Commons, marca visible)
LOGOS = {
    "airwick": ("Air Wick logo.png", "Air Wick"),
    "amazon": ("Amazon 2024.svg", "Amazon"),
    "anker": ("Anker logo.svg", "Anker"),
    "apple": ("Apple logo black.svg", "Apple"),
    "asus": ("ASUS Corporate Logo.svg", "ASUS"),
    "beautyofjoseon": ("Joseon logo (soj.ooO).png", "Beauty of Joseon"),
    "cerave": ("CeraVe logo.png", "CeraVe"),
    "cetaphil": ("Cetaphil Thailand Logo.png", "Cetaphil"),
    "colgate": ("Colgate logo.svg", "Colgate"),
    "coosur": ("Coosur 500x500.png", "Coosur"),
    "eucerin": ("Eucerin logo.svg", "Eucerin"),
    "garnier": ("Garnier wordmark.svg", "Garnier"),
    "google": ("Pixel 2 wordmark.svg", "Google Pixel"),
    "hawaiiantropic": ("Hawaiian Tropic brand logo.svg", "Hawaiian Tropic"),
    "headshoulders": ("Head&shoulders-Logo.svg", "Head & Shoulders"),
    "hp": ("HP logo 2012.svg", "HP"),
    "huggies": ("Huggies logo.svg", "Huggies"),
    "institutoespanol": ("Instituto Español (logo).png", "Instituto Español"),
    "jbl": ("JBL logo.svg", "JBL"),
    "laneige": ("LANEIGE 신규로고 하늘.jpg", "Laneige"),
    "laroche-posay": ("La Roche-Posay (brand).svg", "La Roche-Posay"),
    "lenovo": ("Lenovo-Logo.svg", "Lenovo"),
    "lg": ("LG Electronics logo.png", "LG"),
    "logitech": ("Logitech logo.svg", "Logitech"),
    "lor": ("L'OR logo.png", "L'OR"),
    "loreal": ("L'Oréal logo.svg", "L'Oréal Paris"),
    "marshall": ("Marshall logo.svg", "Marshall"),
    "nescafe": ("Nescafe dolcegusto logo.png", "Nescafé Dolce Gusto"),
    "nespresso": ("Nespresso logo.png", "Nespresso"),
    "nivea": ("NIVEA logo 2021.svg", "NIVEA"),
    "oralb": ("Oral-B logo.svg", "Oral-B"),
    "pantene": ("Pantene.svg", "Pantene"),
    "poco": ("Poco Logo Transparent.png", "POCO"),
    "samsung": ("Samsung logo.svg", "Samsung"),
    "sonos": ("Sonos (Unternehmen) logo.svg", "Sonos"),
    "sony": ("Sony logo.svg", "Sony"),
    "starbucks": ("Starbucks-wordmark-green.svg", "Starbucks"),
    "ue": ("Ultimate Ears logo.png", "Ultimate Ears"),
    "vichy": ("Logo Vichy mon amour.jpg", "Vichy"),
    "xiaomi": ("Xiaomi logo (2021-).svg", "Xiaomi"),
}

LICENCIAS = {
    "Public domain": "https://en.wikipedia.org/wiki/Public_domain",
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 2.5": "https://creativecommons.org/licenses/by/2.5/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 2.0": "https://creativecommons.org/licenses/by-sa/2.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
}


def main():
    os.makedirs(DIR, exist_ok=True)
    s = requests.Session(); s.headers.update(UA)
    catalogo = {}
    titles = ["File:" + v[0] for v in LOGOS.values()]
    for i in range(0, len(titles), 30):
        r = s.get(API, params={
            "action": "query", "format": "json", "titles": "|".join(titles[i:i+30]),
            "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 480}, timeout=60)
        r.raise_for_status()
        paginas = r.json().get("query", {}).get("pages", {})
        info = {}
        for p in paginas.values():
            if "imageinfo" not in p:
                continue
            ii = p["imageinfo"][0]; em = ii.get("extmetadata", {})
            info[p["title"].replace("File:", "")] = {
                "lic": em.get("LicenseShortName", {}).get("value", "?"),
                "autor": re.sub(r"<[^>]+>", "", em.get("Artist", {}).get("value", "") or "").strip()[:80],
                "url": ii.get("descriptionurl"), "thumb": ii.get("thumburl"), "raw": ii.get("url"),
            }
        for slug, (titulo, marca) in LOGOS.items():
            d = info.get(titulo)
            if not d:
                print("  [aviso] no encontrado:", titulo); continue
            destino = os.path.join(DIR, slug + os.path.splitext(d["raw"])[1])
            if not os.path.isfile(destino):
                rr = s.get(d["thumb"] or d["raw"], timeout=90)
                rr.raise_for_status()
                with open(destino, "wb") as f:
                    f.write(rr.content)
                print("  descargado:", os.path.basename(destino))
            catalogo[slug] = {"marca": marca, "archivo": "img/marcas/" + os.path.basename(destino),
                               "licencia": d["lic"], "autor": d["autor"] or "Wikimedia Commons",
                               "fuente": d["url"]}
        time.sleep(1.5)
    ruta = os.path.join(RAIZ, "data", "marcas.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)
    print("Catálogo escrito en", ruta, "-", len(catalogo), "marcas")


if __name__ == "__main__":
    main()
