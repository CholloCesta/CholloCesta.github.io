import json
import os
import sys
from scripts.paapi_client import get_paapi_client

if __name__ == "__main__":
    asins = ["B0753XG51W", "B00O9S4Z2S"]
    ak = os.environ.get("PAAPI_ACCESS_KEY")
    sk = os.environ.get("PAAPI_SECRET_KEY")
    
    if not ak or not sk:
        # Usamos valores por defecto seguros si no hay vars de entorno
        ak = "TU_KEY_REAL"
        sk = "TU_SECRET_REAL"
        
    client = get_paapi_client(ak, sk, "chollocesta-21")
    print("Consultando Amazon...")
    
    # Aquí puedes añadir tu lógica final
    os.makedirs("data", exist_ok=True)
    with open("data/productos_paapi.json", "w", encoding="utf-8") as f:
        json.dump({"Items": []}, f, indent=2)
    print("✅ Archivo data/productos_paapi.json creado con éxito.")
