import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from paapi_client import get_paapi_client

def _secret(name):
    path = f"/data/user/0/com.niki914.zafiro/files/secrets/{name}"
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read().strip()
    return os.environ.get(name.upper())

ACCESS_KEY = _secret("paapi_access_key")
SECRET_KEY = _secret("paapi_secret_key")
PARTNER_TAG = _secret("paapi_partner_tag")

CATEGORIES = {
    "skincare": ["sérum vitamina c", "crema hidratante cerave"],
    "maquillaje": ["base maquillaje", "labial"]
}

def fetch_products():
    client = get_paapi_client(ACCESS_KEY, SECRET_KEY, PARTNER_TAG)
    all_products = {}
    
    for cat, queries in CATEGORIES.items():
        all_products[cat] = []
        for query in queries:
            print(f"Fetching {query} para {cat} usando API real...")
            try:
                # Llamada real a la API firmada
                result = client.search_items(query)
                all_products[cat].append({"query": query, "result": result})
            except Exception as e:
                print(f"Error fetching {query}: {e}")
                all_products[cat].append({"query": query, "status": "error", "error": str(e)})
    
    os.makedirs("data", exist_ok=True)
    with open("data/belleza_productos.json", "w") as f:
        json.dump(all_products, f, indent=2)
    print("Productos actualizados en data/belleza_productos.json")

if __name__ == "__main__":
    fetch_products()
