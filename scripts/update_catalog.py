#!/usr/bin/env python3
"""Actualiza datos del catálogo con Creators API; no publica respuestas de error."""
import json
import os
import re
import sys
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = os.getenv('PAAPI_MARKETPLACE', 'www.amazon.es')
PARTNER = os.getenv('PAAPI_PARTNER_TAG', 'chollocesta-21')
ID = os.getenv('CREATORS_API_CREDENTIAL_ID', '').strip()
SECRET = os.getenv('CREATORS_API_CREDENTIAL_SECRET', '').strip()
VERSION = os.getenv('CREATORS_API_VERSION', '').strip()
PRODUCTS = {'perros': ['B0753XG51W', 'B00O9S4Z2S'], 'gatos': ['B07P8Y34X9', 'B07H8XZL42']}
RESOURCES = ['itemInfo.title', 'images.primary.large']


def request(url, **kwargs):
    for attempt in range(4):
        try:
            response = requests.post(url, timeout=30, **kwargs)
        except requests.RequestException as exc:
            raise RuntimeError(f'Error de conexión con Amazon: {type(exc).__name__}') from None
        if response.status_code not in (429, 500, 502, 503, 504) or attempt == 3:
            break
        time.sleep(2 ** attempt)
    try:
        body = response.json()
    except ValueError:
        raise RuntimeError(f'Amazon devolvió HTTP {response.status_code} sin JSON válido') from None
    if not isinstance(body, dict):
        raise RuntimeError('Amazon devolvió un formato de respuesta inesperado')
    if not response.ok:
        # No imprimir secretos, tokens, cabeceras ni el cuerpo completo.
        reason = body.get('reason') or body.get('type') or body.get('error') or 'sin detalle'
        reason = re.sub(r'[^a-zA-Z0-9_.-]', '', str(reason))[:80]
        raise RuntimeError(f'Amazon devolvió HTTP {response.status_code}: {reason}')
    return body


def main():
    if not ID or not SECRET or not VERSION:
        raise RuntimeError('Faltan los secretos CREATORS_API_CREDENTIAL_ID, CREATORS_API_CREDENTIAL_SECRET o CREATORS_API_VERSION')
    match = re.search(r'(?<!\d)(3\.[123])(?!\d)', VERSION)
    if not match:
        raise RuntimeError('La versión de credencial de Creators API no es válida (3.1, 3.2 o 3.3)')
    host = {'3.1':'api.amazon.com', '3.2':'api.amazon.co.uk', '3.3':'api.amazon.co.jp'}[match.group(1)]
    token = request('https://' + host + '/auth/o2/token', json={
        'grant_type':'client_credentials', 'client_id':ID, 'client_secret':SECRET,
        'scope':'creatorsapi::default',
    }).get('access_token')
    if not token:
        raise RuntimeError('Amazon no devolvió un token de acceso')
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type':'application/json', 'x-marketplace': MARKETPLACE}
    common = {'marketplace':MARKETPLACE, 'partnerTag':PARTNER, 'resources':RESOURCES}
    results = {}
    for category, asins in PRODUCTS.items():
        body = request('https://creatorsapi.amazon/catalog/v1/getItems', headers=headers, json={
            **common, 'itemIds':asins, 'itemIdType':'ASIN',
        })
        if body.get('errors') or not (body.get('itemsResult') or {}).get('items'):
            raise RuntimeError('Amazon no devolvió productos válidos para ' + category)
        items = body['itemsResult']['items']
        products = []
        for item in items:
            title = ((item.get('itemInfo') or {}).get('title') or {}).get('displayValue')
            image = (((item.get('images') or {}).get('primary') or {}).get('large') or {}).get('url')
            url = item.get('detailPageURL')
            if title and image and url:
                products.append({'title': title, 'image': image, 'url': url, 'asin': item.get('asin')})
        if not products:
            raise RuntimeError('Amazon no devolvió datos completos para ' + category)
        results[f'productos_{category}.json'] = products
        time.sleep(1)
    body = request('https://creatorsapi.amazon/catalog/v1/searchItems', headers=headers, json={
        **common, 'keywords':'oferta flash gadget', 'itemCount':4,
    })
    if body.get('errors') or not (body.get('searchResult') or {}).get('items'):
        raise RuntimeError('Amazon no devolvió resultados válidos para la búsqueda de productos')
    # Es una búsqueda, no una verificación de ofertas flash ni de precios.
    results['flash_deals.json'] = body
    out = ROOT / 'data'
    out.mkdir(exist_ok=True)
    for name, data in results.items():
        (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('Actualizado:', name)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        sys.exit(1)
