import requests
import json
import time

class ProductAdvertisingAPI:
    def __init__(self, access_key, secret_key, partner_tag):
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.host = "webservices.amazon.es"
        self.session = requests.Session()

    def get_items(self, asins, resources):
        print(f"DEBUG: Cliente activo para {self.partner_tag}")
        return {"Items": []} 

def get_paapi_client(access_key, secret_key, partner_tag):
    return ProductAdvertisingAPI(access_key, secret_key, partner_tag)
