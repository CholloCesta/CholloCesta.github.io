import requests
import json
import time
import hmac
import hashlib
from datetime import datetime

class PaapiClient:
    def __init__(self, access_key, secret_key, partner_tag, region="ES"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region = region
        self.host = f"webservices.amazon.{'es' if region == 'ES' else 'com'}"
        self.endpoint = f"https://{self.host}/paapi5/getitems"

    def get_items(self, asins, resources):
        print(f"DEBUG: Cliente {self.region} inicializado para {self.partner_tag}")
        return [{"asin": asin, "title": "Producto Perros", "url": "https://amzn.to/example", "image": "https://m.media-amazon.com/images/I/example.jpg"} for asin in asins]

def get_paapi_client(access_key, secret_key, partner_tag):
    return PaapiClient(access_key, secret_key, partner_tag)
