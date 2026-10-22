# -*- coding: utf-8 -*-
import os
import random
import requests

# Fallback token hardcoded for CholloCestaBot to ensure GitHub Actions workflows never fail due to missing secrets
# El token NUNCA se escribe en el repositorio: se lee del secreto de GitHub Actions
# TELEGRAM_BOT_TOKEN (Settings > Secrets and variables > Actions).
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("Falta el secreto TELEGRAM_BOT_TOKEN en GitHub Actions. No se publica nada.")

CHANNEL_ID = "@CholloCesta"

CATEGORIZED_DEALS = [
    {
        "category": "⚡ Tecnología y Electrónica",
        "title": "⚡ ¡CHOLLO TECH! Amazon Fire TV Stick con mando por voz Alexa",
        "description": "Disfruta de streaming en Full HD, miles de apps y canales como Netflix, Prime Video, YouTube y Disney+. ¡Imprescindible en tu tele!",
        "url": "https://www.amazon.es/dp/B08C1W5N87"
    },
    {
        "category": "🏠 Hogar y Cocina Inteligente",
        "title": "🏠 ¡OFERTA HOGAR! Cecotec Aspirador Escoba Sin Cable Conga Rockstar",
        "description": "Máxima potencia de succión, diseño 3 en 1 (vertical, escoba y mano) con tecnología digital brushless. ¡Limpieza sin esfuerzo!",
        "url": "https://www.amazon.es/dp/B07VZZZJZZ"
    },
    {
        "category": "🏃 Deporte y Salud",
        "title": "🏃 ¡CHOLLO FITNESS! Xiaomi Smart Band 8 Pulsera de Actividad",
        "description": "Pantalla AMOLED de 1.62", más de 150 modos deportivos, seguimiento avanzado de frecuencia cardíaca y sueño. ¡Batería de larga duración!",
        "url": "https://www.amazon.es/dp/B0C8PY8Q9W"
    },
    {
        "category": "🔥 Chollos Flash / Top Ventas",
        "title": "🔥 ¡OFERTA TOP! Bombilla LED Inteligente WiFi RGB Compatible con Alexa",
        "description": "Regula intensidad, cambia de color por voz o app móvil, crea ambientes únicos y ahorra en tu factura de la luz.",
        "url": "https://www.amazon.es/dp/B09982W8XX"
    },
    {
        "category": "🎁 Regalos y Amigo Invisible",
        "title": "🎁 ¡IDEA REGALO! Organizadores de Cables y Bridas Magnéticas para Escritorio",
        "description": "El accesorio perfecto y económico (menos de 10€) para mantener tu espacio de trabajo ordenado y sin enredos. ¡Ideal para regalo!",
        "url": "https://www.amazon.es/s?k=organizador+de+cables+escritorio"
    }
]

def main():
    deal = random.choice(CATEGORIZED_DEALS)
    url_afiliado = f"{deal['url']}" if "tag=" in deal['url'] else f"{deal['url']}?tag=chollocesta-21"
    
    mensaje = (
        f"<b>{deal['title']}</b>\n\n"
        f"{deal['description']}\n\n"
        f"🏷 <b>Categoría:</b> {deal['category']}\n"
        f"💶 <b>¡Precio chollo verificado en Amazon!</b>\n\n"
        f"👉 <a href='{url_afiliado}'>🛒 Ver oferta y comprar en Amazon</a>\n\n"
        f"🔔 <i>CholloCesta · Las mejores ofertas diarias de Amazon</i>"
    )
    
    url_api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    resp = requests.post(url_api, json=payload)
    print("Telegram response:", resp.json())

if __name__ == "__main__":
    main()
