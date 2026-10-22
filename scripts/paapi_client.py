#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cliente de Amazon Product Advertising API 5.0 (PA-API 5.0) con firma AWS SigV4.

Solo biblioteca estandar. La firma se valida contra los vectores oficiales de AWS
("Examples of the complete Signature Version 4 signing process").

Variables de entorno requeridas (nunca se guardan en el repo):
  PAAPI_ACCESS_KEY    clave publica de AWS IAM
  PAAPI_SECRET_KEY    clave secreta de AWS IAM
  PAAPI_PARTNER_TAG   tag de afiliado (por defecto chollocesta-21)
  PAAPI_HOST          host del marketplace (por defecto webservices.amazon.es)
  PAAPI_MARKETPLACE   marketplace (por defecto www.amazon.es)
  PAAPI_REGION        region de firma (por defecto eu-west-1)

Uso:
  from paapi_client import ProductAdvertisingAPI
  api = ProductAdvertisingAPI()
  items = api.get_items(["B00PBX3L7K", "B0BRY29Q4X"])
"""
import datetime
import hashlib
import hmac
import json
import os
import time
import urllib.parse

import requests

# marketplace -> (host, region, marketplace_id)
MARKETPLACES = {
    "www.amazon.es":       ("webservices.amazon.es",       "eu-west-1", "www.amazon.es"),
    "www.amazon.de":       ("webservices.amazon.de",       "eu-west-1", "www.amazon.de"),
    "www.amazon.fr":       ("webservices.amazon.fr",       "eu-west-1", "www.amazon.fr"),
    "www.amazon.it":       ("webservices.amazon.it",       "eu-west-1", "www.amazon.it"),
    "www.amazon.co.uk":    ("webservices.amazon.co.uk",    "eu-west-1", "www.amazon.co.uk"),
    "www.amazon.com":      ("webservices.amazon.com",      "us-east-1", "www.amazon.com"),
    "www.amazon.ca":       ("webservices.amazon.ca",       "us-east-1", "www.amazon.ca"),
    "www.amazon.co.jp":    ("webservices.amazon.co.jp",    "us-west-2", "www.amazon.co.jp"),
}

SERVICE = "ProductAdvertisingAPI"
RESOURCES = "Images.Primary.Large,Images.Primary.Medium,ItemInfo.Title,ItemInfo.Features,Offers.Listings.Price,Offers.Listings.SavingBasis"


def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _quote(s):
    """RFC3986: espacio -> %20 (no '+'), seguro -_.~"""
    return urllib.parse.quote(str(s), safe="-_.~")


def sign_request(method, host, path, query, headers, payload,
                 access_key, secret_key, region, service, amzdate=None):
    """Devuelve (authorization, headers_firmados, canonical_query)."""
    now = amzdate or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    datestamp = now[:8]
    h = {k.lower(): " ".join(str(v).split()) for k, v in headers.items()}
    h["x-amz-date"] = now
    h.setdefault("host", host)
    signed_keys = sorted(h)
    canonical_headers = "".join(f"{k}:{h[k]}\n" for k in signed_keys)
    signed_headers = ";".join(signed_keys)
    canonical_query = "&".join(f"{_quote(k)}={_quote(v)}" for k, v in sorted(query.items()))
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = "\n".join([method, path, canonical_query,
                                    canonical_headers, signed_headers, payload_hash])
    scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(["AWS4-HMAC-SHA256", now, scope,
                                 hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()])
    k = _sign(("AWS4" + secret_key).encode("utf-8"), datestamp)
    k = _sign(k, region)
    k = _sign(k, service)
    k = _sign(k, "aws4_request")
    signature = hmac.new(k, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    authorization = (f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, "
                     f"SignedHeaders={signed_headers}, Signature={signature}")
    return authorization, h, canonical_query


class PAAPIError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class ProductAdvertisingAPI(object):
    def __init__(self, access_key=None, secret_key=None, partner_tag=None,
                 marketplace=None, region=None, host=None, timeout=30):
        self.access_key = access_key or os.environ.get("PAAPI_ACCESS_KEY", "").strip()
        self.secret_key = secret_key or os.environ.get("PAAPI_SECRET_KEY", "").strip()
        self.partner_tag = partner_tag or os.environ.get("PAAPI_PARTNER_TAG", "chollocesta-21").strip()
        marketplace = marketplace or os.environ.get("PAAPI_MARKETPLACE", "www.amazon.es")
        mh = MARKETPLACES.get(marketplace)
        if not mh:
            raise ValueError(f"Marketplace no soportado: {marketplace}")
        self.marketplace_id = mh[2]
        self.host = host or os.environ.get("PAAPI_HOST", mh[0])
        self.region = region or os.environ.get("PAAPI_REGION", mh[1])
        self.timeout = timeout
        if not self.access_key or not self.secret_key:
            raise PAAPIError("CredentialsMissing",
                             "Faltan PAAPI_ACCESS_KEY y/o PAAPI_SECRET_KEY en el entorno")
        self.session = requests.Session()

    # -- interno -------------------------------------------------------
    def _request(self, operation, extra):
        path = "/paapi5/" + operation.lower()
        query = {
            "Operation": operation,
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Marketplace": self.marketplace_id,
        }
        query.update(extra)
        auth, headers, cq = sign_request(
            "GET", self.host, path, query,
            {"accept-encoding": "identity", "user-agent": "CholloCesta/1.0"},
            "", self.access_key, self.secret_key, self.region, SERVICE)
        url = f"https://{self.host}{path}?{cq}"
        r = self.session.get(url, headers=headers, timeout=self.timeout)
        if r.status_code == 200:
            return r.json()
        try:
            body = r.json()
            err = (body.get("Errors") or [{}])[0]
            raise PAAPIError(err.get("Code", f"HTTP{r.status_code}"), err.get("Message", r.text[:300]))
        except ValueError:
            raise PAAPIError(f"HTTP{r.status_code}", r.text[:300])

    # -- publico -------------------------------------------------------
    def get_items(self, asins, resources=RESOURCES):
        """GetItems: hasta 10 ASIN por llamada. Devuelve dict asin -> item."""
        asins = [a for a in dict.fromkeys(asins) if a]
        out = {}
        for i in range(0, len(asins), 10):
            lote = asins[i:i + 10]
            data = self._request("GetItems", {"ItemIds": ",".join(lote), "Resources": resources})
            for res in (data.get("ItemsResult") or {}).get("Items", []) or []:
                asin = res.get("ASIN")
                if asin:
                    out[asin] = res
            if i + 10 < len(asins):
                time.sleep(1.1)   # PA-API limita a ~1 req/s
        return out

    def search_items(self, keywords, item_count=10, search_index="All", resources=RESOURCES):
        """SearchItems por palabras clave (para productos sin ASIN)."""
        data = self._request("SearchItems", {
            "SearchIndex": search_index, "Keywords": keywords,
            "ItemCount": max(1, min(int(item_count), 10)), "Resources": resources})
        return (data.get("SearchResult") or {}).get("Items", []) or []

    # -- utilidades ----------------------------------------------------
    @staticmethod
    def best_image(item):
        """Mejor URL de imagen disponible del item."""
        imgs = (item.get("Images") or {}).get("Primary") or {}
        for key in ("Large", "Medium"):
            v = imgs.get(key)
            if v and v.get("URL"):
                return v["URL"]
        return None

    @staticmethod
    def item_title(item):
        return ((item.get("ItemInfo") or {}).get("Title") or {}).get("DisplayValue", "")

    @staticmethod
    def item_price(item):
        listings = ((item.get("Offers") or {}).get("Listings") or [])
        if not listings:
            return None
        p = (listings[0].get("Price") or {}).get("Amount")
        return p

    def item_url(self, item):
        """URL del producto en el marketplace de la consulta (DetailPageURL de la API)."""
        return item.get("DetailPageURL") or ""


if __name__ == "__main__":
    # Prueba de la firma contra los vectores oficiales de AWS
    import sys
    ak = "AKIDEXAMPLE"
    sk = "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY"
    d = "20150830T123600Z"
    a1, _, _ = sign_request("GET", "example.amazonaws.com", "/", {},
                             {"host": "example.amazonaws.com", "x-amz-date": d}, "",
                             ak, sk, "us-east-1", "service", d)
    e1 = ("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20150830/us-east-1/service/aws4_request, "
          "SignedHeaders=host;x-amz-date, "
          "Signature=5fa00fa31553b73ebf1942676e86291e8372ff2a2260956d9b8aae1d763fbf31")
    a2, _, _ = sign_request("GET", "example.amazonaws.com", "/",
                             {"Param2": "value2", "Param1": "value1"},
                             {"host": "example.amazonaws.com", "x-amz-date": d}, "",
                             ak, sk, "us-east-1", "service", d)
    e2 = ("AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20150830/us-east-1/service/aws4_request, "
          "SignedHeaders=host;x-amz-date, "
          "Signature=b97d918cfa904a5beff61c982a1b6f458b799221646efd99d3219ec94cdf2500")
    ok = (a1 == e1) and (a2 == e2)
    print("Firma SigV4 validada contra los vectores oficiales de AWS:", ok)
    sys.exit(0 if ok else 1)
