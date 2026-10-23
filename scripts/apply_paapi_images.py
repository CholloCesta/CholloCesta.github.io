
import os
import re
import subprocess
from glob import glob

# Función para extraer ASIN de un enlace de Amazon
def extract_asin(url):
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    return match.group(1) if match else None

# Función para obtener la imagen vía paapi_client
def get_image_url(asin):
    # Asumimos que paapi_client.py acepta --asin y devuelve la URL
    result = subprocess.run(['python3', 'scripts/paapi_client.py', '--asin', asin], capture_output=True, text=True)
    return result.stdout.strip()

for md_file in glob('**/*.md', recursive=True):
    with open(md_file, 'r') as f:
        content = f.read()
    
    # Buscar enlaces de Amazon
    links = re.findall(r'\[Ver en Amazon\]\((.*?)\)', content)
    changed = False
    for link in links:
        asin = extract_asin(link)
        if asin:
            image_url = get_image_url(asin)
            if image_url:
                # Reemplazar la imagen anterior por la nueva
                # Asumimos que la imagen está justo antes del enlace
                pattern = re.compile(r'!\[Imagen\]\(.*?\)
- \[Ver en Amazon\]\(' + re.escape(link) + r'\)')
                new_image_block = f'![Imagen]({image_url})\n- [Ver en Amazon]({link})'
                if pattern.search(content):
                    content = pattern.sub(new_image_block, content)
                    changed = True
    
    if changed:
        with open(md_file, 'w') as f:
            f.write(content)
