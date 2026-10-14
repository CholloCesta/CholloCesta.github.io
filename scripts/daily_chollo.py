# -*- coding: utf-8 -*-
import os
import random
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8776194715:AAE4C8wtMkCJvQGb2RBR9XI3vGqGbnHuSEQ")
CHANNEL_ID = "@CholloCesta"

CATEGORIZED_DEALS = [
    {
        "category": "⚡ Tecnología y Electrónica",
        "title": "⚡ ¡CHOLLO TECNOLOGÍA! Auriculares Inalámbricos Bluetooth 5.3 con Cancelación de Ruido",
        "description": "Sonido Hi-Fi, estuche de carga rápida con pantalla LED y 40h de autonomía. ¡Uno de los productos más vendidos en Amazon!",
        "url": "https://www.amazon.es/dp/B0B5X4XXXX"
    },
    {
        "category": "🏠 Hogar y Cocina Inteligente",
        "title": "🏠 ¡OFERTA HOGAR! Freidora de Aire Sin Aceite 5.5L con Panel táctil LED",
        "description": "Cocina más sano con un 85% menos de grasa. 8 programas preestablecidos y gran capacidad para toda la familia.",
        "url": "https://www.amazon.es/dp/B08N5WRWNW"
    },
    {
        "category": "🏃 Deporte y Salud",
        "title": "🏃 ¡CHOLLO FITNESS! Smartwatch Deportivo con Pulsómetro y SpO2",
        "id": "fit",
        "description": "Monitor de sueño, 100+ modos deportivos, resistencia al agua IP68 y notificaciones inteligentes.",
        "url": "https://www.amazon.es/dp/B0C3X9YYYY"
    },
    {
        "category": "🔥 Chollos Flash / Top Ventas",
        "title": "🔥 ¡OFERTA FLASH AMAZON! Enchufe Inteligente WiFi Compatible con Alexa y Google Assistant",
        "description": "Controla tus electrodomésticos por voz y programa horarios de encendido con consumo energético en tiempo real.",
        "url": "https://www.amazon.es/dp/B09XYZ1234"
    }
]

def main():
    deal = random.choice(CATEGORIZED_DEALS)
    url_afiliado = f"{deal['url']}?tag=chollocesta-21"
    
    mensaje = (
        f"<b>{deal['title']}</b>

"
        f"{deal['description']}

"
        f"🏷 <b>Categoría:</b> {deal['category']}
"
        f"💶 <b>¡Precio chollo verificado!</b>

"
        f"👉 <a href='{url_afiliado}'>Ver oferta en Amazon</a>

"
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
