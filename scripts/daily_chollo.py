import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = "@CholloCesta"

def main():
    titulo = "🔥 ¡OFERTA ESTRELLA DEL DÍA EN AMAZON! 🔥"
    descripcion = "¡Producto top ventas con descuento flash exclusivo hoy en Amazon España! Unidades muy limitadas."
    url_original = "https://www.amazon.es/dp/B08N5WRWNW"
    url_afiliado = f"{url_original}?tag=chollocesta-21"
    
    mensaje = (
        f"<b>{titulo}</b>\n\n"
        f"{descripcion}\n\n"
        f"🛒 <b>Cómpralo aquí:</b>\n"
        f"👉 <a href='{url_afiliado}'>Ver oferta en Amazon</a>\n\n"
        f"🔔 <i>Precio y disponibilidad sujetos a cambios. ¡Chollo Cesta!</i>"
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
