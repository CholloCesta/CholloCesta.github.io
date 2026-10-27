import json
import os
import sys
sys.path.append(os.getcwd())
from scripts.paapi_client import get_paapi_client

OUTPUT_FILE = "data/productos_paapi.json"

if __name__ == "__main__":
    asins = ["B0753XG51W", "B00O9S4Z2S"]
    ak = os.environ.get("PAAPI_ACCESS_KEY")
    sk = os.environ.get("PAAPI_SECRET_KEY")
    
    if not ak or not sk:
        print("❌ Error: PAAPI_ACCESS_KEY y PAAPI_SECRET_KEY no configurados.")
        sys.exit(1)
        
    client = get_paapi_client(ak, sk, "chollocesta-21")
    print("Consultando Amazon...")
    data = client.get_items(asins, resources=["ItemInfo.Title", "Images.Primary.Large"])
    
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Archivo {OUTPUT_FILE} creado con éxito.")
