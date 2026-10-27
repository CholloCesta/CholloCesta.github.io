import json
import os
import sys
sys.path.append(os.getcwd())
from scripts.paapi_client import get_paapi_client

# Definimos las categorías de Salud con sus búsquedas optimizadas
CATEGORIAS = {
    "dermocosmetica": ["crema hidratante cara", "crema corporal", "protector solar facial"],
    "suplementos": ["vitaminas naturales", "suplementos hierbas"],
    "fisioterapia": ["masajeador cuello", "manta electrica"],
    "monitorizacion": ["bascula inteligente", "tensiometro digital"],
    "ambiente": ["humidificador ultrasonico", "purificador aire"]
}

OUTPUT_DIR = "data"

if __name__ == "__main__":
    ak = os.environ.get("PAAPI_ACCESS_KEY")
    sk = os.environ.get("PAAPI_SECRET_KEY")
    client = get_paapi_client(ak, sk, "chollocesta-21")
    
    for categoria, keywords in CATEGORIAS.items():
        print(f"Buscando tendencias para {categoria}...")
        all_items = []
        for kw in keywords:
            items = client.search_items(kw, item_count=2)
            all_items.extend(items)
        
        output_file = os.path.join(OUTPUT_DIR, f"productos_{categoria}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_items, f, indent=2, ensure_ascii=False)
