import json
import os
import sys
sys.path.append(os.getcwd())
from scripts.paapi_client import get_paapi_client

# Definimos las categorías que queremos automatizar
CATEGORIAS = {
    "perros": ["B0753XG51W", "B00O9S4Z2S"],
    "gatos": ["B07P8Y34X9", "B07H8XZL42"]
}

OUTPUT_DIR = "data"

if __name__ == "__main__":
    ak = os.environ.get("PAAPI_ACCESS_KEY")
    sk = os.environ.get("PAAPI_SECRET_KEY")
    
    if not ak or not sk:
        print("❌ Error: PAAPI_ACCESS_KEY y PAAPI_SECRET_KEY no configurados.")
        sys.exit(1)
        
    client = get_paapi_client(ak, sk, "chollocesta-21")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for categoria, asins in CATEGORIAS.items():
        print(f"Consultando Amazon para {categoria}...")
        data = client.get_items(asins, resources=["ItemInfo.Title", "Images.Primary.Large"])
        
        output_file = os.path.join(OUTPUT_DIR, f"productos_{categoria}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Archivo {output_file} creado con éxito.")
