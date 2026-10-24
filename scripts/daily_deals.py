
import subprocess
import re
import os

# Lista de ASINs de Belleza a actualizar
asins = {
    "Maybelline New York Maquillaje": "B00B9O8W0W",
    "Garnier Agua Micelar": "B01M3N6L8U",
    "CeraVe Crema Hidratante": "B076G2324X"
}

def get_image_from_paapi(asin):
    # Llama al cliente de la API usando los secretos de entorno
    result = subprocess.run(['python3', 'scripts/paapi_client.py', '--asin', asin], capture_output=True, text=True)
    # Asumimos que paapi_client devuelve la URL de la imagen
    return result.stdout.strip()

# Actualizar el archivo
file_path = "belleza.html"
with open(file_path, 'r') as f:
    content = f.read()

for name, asin in asins.items():
    img_url = get_image_from_paapi(asin)
    if img_url and img_url.startswith('http'):
        # Reemplazar la imagen en el HTML
        pattern = rf'(<img.*?alt="{name}".*?src=").*?(".*?>)'
        content = re.sub(pattern, rf'\1{img_url}\2', content)

with open(file_path, 'w') as f:
    f.write(content)

print("Imágenes actualizadas mediante PA-API.")
