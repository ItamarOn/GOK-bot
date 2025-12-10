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
    if not response.ok:
        logger.error(f"Bad response from Green - payload:{payload} - response:{response}")

    log_msg_preview = text.split('\n', 1)[0]
    logger.info(f"Green response: {response.status_code} `{log_msg_preview}`")
