import requests

from config import GREEN_ID, GREEN_TOKEN, logger


def green_send_message(chat_id: str, text: str, reply_to: str = None):
    url = f"https://api.green-api.com/waInstance{GREEN_ID}/sendMessage/{GREEN_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": text
    }

    if reply_to:
        payload["quotedMessageId"] = reply_to

    logger.debug(f"Green send payload: {payload}")
    response = requests.post(url, json=payload)
    logger.info(f"Green send status: {response.status_code} | {response.text}")
