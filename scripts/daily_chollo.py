# -*- coding: utf-8 -*-
import os
import random
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise SystemExit("Falta el secreto TELEGRAM_BOT_TOKEN en GitHub Actions.")

CHANNEL_ID = "@CholloCesta"

CATEGORIZED_DEALS = [
    {
        "category": "Tecnologia y Electronica",
        "title": "CHOLLO TECH! Amazon Fire TV Stick con mando por voz Alexa",
        "description": "Disfruta de streaming en Full HD, miles de apps y canales. Imprescindible en tu tele!",
        "url": "https://www.amazon.es/dp/B08C1W5N87"
    },
    {
        "category": "Hogar y Cocina Inteligente",
        "title": "OFERTA HOGAR! Cecotec Aspirador Escoba Sin Cable Conga Rockstar",
        "description": "Maxima potencia de succion, diseno 3 en 1. Limpieza sin esfuerzo!",
        "url": "https://www.amazon.es/dp/B07VZZZJZZ"
    },
    {
        "category": "Deporte y Salud",
        "title": "CHOLLO FITNESS! Xiaomi Smart Band 8 Pulsera de Actividad",
        "description": "Pantalla AMOLED de 1.62 Pulgadas, mas de 150 modos deportivos. Bateria de larga duracion!",
        "url": "https://www.amazon.es/dp/B0C8PY8Q9W"
    }
]

def main():
    deal = random.choice(CATEGORIZED_DEALS)
    url_afiliado = f"{deal['url']}?tag=chollocesta-21"
    
    mensaje = (
        f"<b>{deal['title']}</b>\n\n"
        f"{deal['description']}\n\n"
        f"🏷 <b>Categoria:</b> {deal['category']}\n"
        f"👉 <a href='{url_afiliado}'>🛒 Ver oferta y comprar en Amazon</a>"
    )
    
    url_api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    
    resp = requests.post(url_api, json=payload)
    print("Telegram response:", resp.json())

if __name__ == "__main__":
    main()
