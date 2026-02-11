import requests
import asyncio

from config import GREEN_ID, GREEN_TOKEN, ENVIRONMENT, logger
from utils.redis_manager import db

async def green_send_message(chat_id: str, text: str, reply_to: str = None):
    prefix = "dev: \n" if ENVIRONMENT == "DEV" else ""
    url = f"https://api.green-api.com/waInstance{GREEN_ID}/sendMessage/{GREEN_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": prefix + text
    }
    if reply_to:
        payload["quotedMessageId"] = reply_to

    logger.info(f"Response: {payload}")

    def _send():
        return requests.post(url, json=payload, timeout=30)

    response = await asyncio.to_thread(_send)

    if not response.ok:
        logger.error(f"Bad response from Green - payload:{payload} - response:{response}")

    logger.info(f"status_code: {response.status_code}, response: {response.text}")
    await db.track_sent_message(is_group=chat_id.endswith("@g.us"))


def is_green_available():
    url = f"https://api.green-api.com/waInstance{GREEN_ID}/getStatusInstance/{GREEN_TOKEN}"
    response = requests.get(url)
    if response.ok:
        status_instance = response.json().get('statusInstance', 'offline')
        logger.info(f"Green API statusInstance: {status_instance}")
        return status_instance == "online"
    return False
