#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cliente mínimo de Amazon Product Advertising API 5.0 (PA-API 5.0).

Firma las peticiones con AWS Signature V4 (servicio "ProductAdvertisingAPI").
No necesita librerías adicionales: sólo `requests`.

Las credenciales NUNCA van en el repositorio. Se leen del entorno:
    PAAPI_ACCESS_KEY    (Access Key ID de Amazon Afiliados)
    PAAPI_SECRET_KEY    (Secret Key)
    PAAPI_PARTNER_TAG   (associate tag, p.ej. chollocesta-21)
    PAAPI_PARTNER_ID    (Partner ID, opcional)
    PAAPI_MARKETPLACE   (por defecto www.amazon.es)
    PAAPI_HOST          (por defecto webservices.amazon.es)
    PAAPI_REGION        (por defecto eu-west-1)
"""
import datetime
import hashlib
import hmac
import json
import os

import requests

SERVICIO = "ProductAdvertisingAPI"
AMAZON_DATE_FMT = "%Y%m%dT%H%M%SZ"


class PaApiError(Exception):
    pass


def _credenciales():
    ak = os.environ.get("PAAPI_ACCESS_KEY", "").strip()
    sk = os.environ.get("PAAPI_SECRET_KEY", "").strip()
    tag = os.environ.get("PAAPI_PARTNER_TAG", "chollocesta-21").strip()
    if not ak or not sk:
        raise PaApiError(
            "Faltan PAAPI_ACCESS_KEY y PAAPI_SECRET_KEY (secretos de GitHub Actions o variables de entorno)."
        )
    return ak, sk, tag


def _clave_firma(secret, fecha, region):
    k = ("AWS4" + secret).encode("utf-8")
    for parte in (fecha, region, SERVICIO, "aws4_request"):
        k = hmac.new(k, parte.encode("utf-8"), hashlib.sha256).digest()
    return k


def _firma(secret, fecha, region, cadena):
    return hmac.new(_clave_firma(secret, fecha, region), cadena.encode("utf-8"), hashlib.sha256).hexdigest()


def _hash_carga(cuerpo):
    return hashlib.sha256(cuerpo.encode("utf-8")).hexdigest()


def peticion(operacion, payload, host=None, region=None, marketplace=None):
    """Envía una operación PA-API (SearchItems, GetItems, ...) y devuelve el JSON."""
    ak, sk, tag = _credenciales()
    host = host or os.environ.get("PAAPI_HOST", "webservices.amazon.es")
    region = region or os.environ.get("PAAPI_REGION", "eu-west-1")
    marketplace = marketplace or os.environ.get("PAAPI_MARKETPLACE", "www.amazon.es")
    ahora = datetime.datetime.utcnow()
    amzdate = ahora.strftime(AMAZON_DATE_FMT)
    fecha = ahora.strftime("%Y%m%d")
    cuerpo = json.dumps(payload, separators=(",", ":"))
    hash_carga = _hash_carga(cuerpo)

    encabezados_a_firmar = {"host": host, "x-amz-date": amzdate, "x-amz-target": operacion}
    canonical = "\n".join(f"{k}:{encabezados_a_firmar[k]}" for k in sorted(encabezados_a_firmar))
    signed_headers = ";".join(sorted(encabezados_a_firmar))
    peticion_canonica = "\n".join([
        "POST", "/", "", canonical, signed_headers, hash_carga,
    ])
    alcance = f"{fecha}/{region}/{SERVICIO}/aws4_request"
    cadena_a_firmar = "\n".join([
        "AWS4-HMAC-SHA256", amzdate, alcance, _hash_carga(peticion_canonica),
    ])
    firma = _firma(sk, fecha, region, cadena_a_firmar)
    autorizacion = (
        f"AWS4-HMAC-SHA256 Credential={ak}/{alcance}, "
        f"SignedHeaders={signed_headers}, Signature={firma}"
    )

    url = f"https://{host}/paapi5/{operacion.lower()}"
    cab = {
        "Content-Encoding": "amz-1.0",
        "Content-Type": "application/json; charset=utf-8",
        "Host": host,
        "User-Agent": "CholloCesta/1.0 (PA-API 5.0)",
        "X-Amz-Date": amzdate,
        "X-Amz-Target": operacion,
        "Authorization": autorizacion,
    }
    r = requests.post(url, data=cuerpo.encode("utf-8"), headers=cab, timeout=30)
    if r.status_code != 200:
        raise PaApiError(f"PA-API {operacion} -> HTTP {r.status_code}: {r.text[:400]}")
    return r.json()


def search_items(keywords, marketplace=None, item_count=10, partner_type="Associates"):
    """Busca productos y devuelve la lista de Items."""
    ak, sk, tag = _credenciales()
    payload = {
        "Keywords": keywords,
        "PartnerTag": tag,
        "PartnerType": partner_type,
        "Marketplace": marketplace or os.environ.get("PAAPI_MARKETPLACE", "www.amazon.es"),
        "ItemCount": item_count,
        "Resources": [
            "Images.Primary.Large", "Images.Primary.Medium",
            "ItemInfo.Title", "ItemInfo.ByLineInfo", "ItemInfo.ManufactureInfo",
            "Offers.Listings.Price", "Offers.Listings.Availability",
        ],
    }
    if os.environ.get("PAAPI_PARTNER_ID", "").strip():
        payload["PartnerId"] = os.environ["PAAPI_PARTNER_ID"].strip()
    datos = peticion("SearchItems", payload)
    return (datos.get("SearchResult") or {}).get("Items") or []


def get_items(asins, marketplace=None, partner_type="Associates"):
    """Obtiene productos por ASIN."""
    ak, sk, tag = _credenciales()
    payload = {
        "ItemIds": list(asins),
        "PartnerTag": tag,
        "PartnerType": partner_type,
        "Marketplace": marketplace or os.environ.get("PAAPI_MARKETPLACE", "www.amazon.es"),
        "Resources": [
            "Images.Primary.Large", "Images.Primary.Medium",
            "ItemInfo.Title", "ItemInfo.ByLineInfo", "ItemInfo.ManufactureInfo",
            "Offers.Listings.Price", "Offers.Listings.Availability",
        ],
    }
    if os.environ.get("PAAPI_PARTNER_ID", "").strip():
        payload["PartnerId"] = os.environ["PAAPI_PARTNER_ID"].strip()
    datos = peticion("GetItems", payload)
    return (datos.get("ItemsResult") or {}).get("Items") or []


def imagen_principal(item):
    """Devuelve la URL de la imagen grande de un Item de PA-API (o None)."""
    try:
        grande = item["Images"]["Primary"]["Large"]
        if grande.get("URL"):
            return grande["URL"]
    except (KeyError, TypeError):
        pass
    try:
        return item["Images"]["Primary"]["Medium"]["URL"]
    except (KeyError, TypeError):
        return None


def titulo(item):
    try:
        return item["ItemInfo"]["Title"]["DisplayValue"]
    except (KeyError, TypeError):
        return None


def precio(item):
    try:
        return item["Offers"]["Listings"][0]["Price"]["Amount"]
    except (KeyError, TypeError, IndexError):
        return None
