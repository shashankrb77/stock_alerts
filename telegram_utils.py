import os
import requests

token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
telegram_api_url = os.getenv("TELEGRAM_API_URL")

def send_telegram_message(message):
    url = f"{telegram_api_url}{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=payload)
    return response.json()


