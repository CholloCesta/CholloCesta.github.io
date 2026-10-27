import json
import os
import sys
sys.path.append(os.getcwd())
from scripts.paapi_client import get_paapi_client

OUTPUT_FILE = "data/flash_deals.json"

if __name__ == "__main__":
    # Búsqueda de productos "Top Ventas" / "Ofertas"
    keywords = "oferta flash gadget"
    ak = os.environ.get("PAAPI_ACCESS_KEY")
    sk = os.environ.get("PAAPI_SECRET_KEY")
    
    if not ak or not sk:
        print("❌ Error: PAAPI_ACCESS_KEY y PAAPI_SECRET_KEY no configurados.")
        sys.exit(1)
        
    client = get_paapi_client(ak, sk, "chollocesta-21")
    print("Buscando chollos flash...")
    
    # Buscamos productos genéricos para refrescar la portada
    data = client.search_items(keywords, item_count=4)
    
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Archivo {OUTPUT_FILE} actualizado con ofertas del día.")
