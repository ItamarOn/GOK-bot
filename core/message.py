import requests

from config import GREEN_ID, GREEN_TOKEN, ENVIRONMENT, logger


def green_send_message(chat_id: str, text: str, reply_to: str = None):
    prefix = "dev: \n" if ENVIRONMENT == "DEV" else ""
    url = f"https://api.green-api.com/waInstance{GREEN_ID}/sendMessage/{GREEN_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": prefix + text
    }
    if reply_to:
        payload["quotedMessageId"] = reply_to

    logger.info(f"Response: {payload}")

    response = requests.post(url, json=payload)
    if not response.ok:
        logger.error(f"Bad response from Green - payload:{payload} - response:{response}")
    logger.info(response.__dict__)  # try!!!!


def is_green_available():
    url = f"https://api.green-api.com/waInstance{GREEN_ID}/getStatusInstance/{GREEN_TOKEN}"
    response = requests.get(url)
    if response.ok:
        status_instance = response.json().get('statusInstance', 'offline')
        logger.info(f"Green API statusInstance: {status_instance}")
        return status_instance == "online"
    return False
