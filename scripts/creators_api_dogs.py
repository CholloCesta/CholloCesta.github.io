#!/usr/bin/env python3
"""Fetch a small, factual product-image selection for perros.html via Amazon Creators API."""
import html
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "perros_creators_api.json"
HTML = ROOT / "perros.html"
MARKETPLACE = os.environ.get("PAAPI_MARKETPLACE", "www.amazon.es")
PARTNER_TAG = os.environ.get("PAAPI_PARTNER_TAG", "chollocesta-21")
VERSION = os.environ.get("CREATORS_API_VERSION", "").strip()
CLIENT_ID = os.environ.get("CREATORS_API_CREDENTIAL_ID", "").strip()
CLIENT_SECRET = os.environ.get("CREATORS_API_CREDENTIAL_SECRET", "").strip()

# English resource names are lowerCamelCase per Amazon's Creators API schema.
RESOURCES = ["images.primary.large", "images.primary.medium", "itemInfo.title"]
SEARCHES = [
    ("Alimentación", "pienso completo perro adulto"),
    ("Cuidado e higiene", "champu para perros"),
    ("Accesorios", "arnes perro ajustable"),
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def get_access_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET or not VERSION:
        fail("Faltan secretos CREATORS_API_CREDENTIAL_ID, CREATORS_API_CREDENTIAL_SECRET o CREATORS_API_VERSION en GitHub Actions.")
    # A few mobile views label this field Version but may expose a prefix such as
    # "Version 3.2"; select the OAuth endpoint by the numeric version, never print secrets.
    match = re.search(r"(?:^|[^0-9])(3\.[0-9]+)(?:$|[^0-9])", VERSION)
    if match:
        token_url = "https://api.amazon.co.uk/auth/o2/token"
    elif re.search(r"(?:^|[^0-9])2\.[0-9]+(?:$|[^0-9])", VERSION):
        token_url = "https://api.amazon.com/auth/o2/token"
    else:
        fail("Versión de credencial no reconocida; para Amazon España debe ser la europea (por ejemplo, 3.2). Comprueba el secreto CREATORS_API_VERSION.")
    response = requests.post(token_url, json={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "creatorsapi::default",
    }, timeout=30)
    if response.status_code != 200:
        fail(f"Amazon OAuth devolvió HTTP {response.status_code}; comprueba que las credenciales nuevas y la versión sean correctas.")
    token = response.json().get("access_token")
    if not token:
        fail("Amazon OAuth no devolvió access_token.")
    return token


def search(token: str, category: str, keywords: str) -> dict | None:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-marketplace": MARKETPLACE,
    }
    payload = {
        "keywords": keywords,
        "itemCount": 5,
        "marketplace": MARKETPLACE,
        "partnerTag": PARTNER_TAG,
        "resources": RESOURCES,
    }
    for attempt in range(4):
        response = requests.post("https://creatorsapi.amazon/catalog/v1/searchItems", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            results = response.json().get("searchResult", {}).get("items", [])
            for item in results:
                title = ((item.get("itemInfo") or {}).get("title") or {}).get("displayValue")
                primary = (item.get("images") or {}).get("primary") or {}
                image = (primary.get("large") or primary.get("medium") or {}).get("url")
                url = item.get("detailPageURL")
                if title and image and url and item.get("asin"):
                    return {
                        "category": category,
                        "query": keywords,
                        "asin": item["asin"],
                        "title": title,
                        "image": image,
                        "url": url,
                    }
            print(f"Sin producto con imagen en resultados para {category}.")
            return None
        if response.status_code in (429, 500, 502, 503, 504) and attempt < 3:
            time.sleep(2 ** attempt)
            continue
        # Avoid printing response body: it may contain identifiers or other account metadata.
        fail(f"Creators API devolvió HTTP {response.status_code} en la búsqueda {category}; revisa acceso, marketplace y credenciales.")
    return None


def make_cards(products: list[dict]) -> str:
    cards = []
    for p in products:
        title = html.escape(p["title"], quote=True)
        url = html.escape(p["url"], quote=True)
        image = html.escape(p["image"], quote=True)
        category = html.escape(p["category"])
        cards.append(f'''<article class="product-card">
<a class="product-image-link" href="{url}" target="_blank" rel="nofollow sponsored noopener" aria-label="Ver {title} en Amazon">
<img src="{image}" alt="{title} — imagen oficial de Amazon" loading="lazy" decoding="async" width="300" height="300">
</a>
<span class="label">{category}</span>
<h3>{title}</h3>
<p>Producto localizado mediante Amazon Creators API. Comprueba formato, precio y disponibilidad en la ficha.</p>
<a class="cta" href="{url}" target="_blank" rel="nofollow sponsored noopener">Ver producto en Amazon</a>
</article>''')
    return "\n".join(cards)


def main() -> None:
    token = get_access_token()
    products = []
    for index, (category, keywords) in enumerate(SEARCHES):
        product = search(token, category, keywords)
        if product:
            products.append(product)
        if index < len(SEARCHES) - 1:
            time.sleep(1)
    if not products:
        fail("Creators API no devolvió productos con imagen; no se publicaron imágenes ficticias.")

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    page = HTML.read_text(encoding="utf-8")
    start = "<!-- CREATORS API DOG PRODUCTS START -->"
    end = "<!-- CREATORS API DOG PRODUCTS END -->"
    if start not in page or end not in page:
        fail("No se encuentran los marcadores de inserción en perros.html; no se modificó la página.")
    block = start + "\n" + make_cards(products) + "\n" + end
    left, rest = page.split(start, 1)
    _, right = rest.split(end, 1)
    page = left + block + right
    HTML.write_text(page, encoding="utf-8")
    print(f"Productos de perro con imagen oficial: {len(products)}; datos e imágenes actualizados en perros.html.")


if __name__ == "__main__":
    main()
