from time import time
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response

from engine import check_barcode
from config import logger, GREEN_ID, GREEN_TOKEN
from texts import TEXTS, HELP_KEYWORDS, THANKS_KEYWORDS
from ducplicate_checker import DuplicateChecker

duplicate_checker = DuplicateChecker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown lifecycle for FastAPI"""
    await duplicate_checker.connect()
    logger.info("Redis connected successfully")
    yield
    if duplicate_checker.client:
        await duplicate_checker.client.close()
        logger.info("Redis connection closed")


app = FastAPI(lifespan=lifespan)
# Health Checks
@app.get("/health/redis", tags=["system"])
async def redis_health():
    healthy = await duplicate_checker.ping()
    return {"redis": "ok" if healthy else "unreachable"}

@app.get("/health/redis/count", tags=["system"])
async def redis_keys_count():
    count = await duplicate_checker.count_keys()
    return {"keys": count}


@app.get("/health", tags=["system"])
async def health_check(request: Request):
    client_ip = request.client.host or "unknown"
    logger.debug(f"health_check from {client_ip}")
    return {
        "status": "ok",
        "ip": f"{client_ip}",
        "time": f"{time()}",
    }


@app.post("/webhook-green", tags=["whatsapp"])
async def green_webhook(request: Request):
    data = await request.json()
    logger.debug(f"Green incoming: {data}")

    if data.get("typeWebhook") != "incomingMessageReceived":
        return {"status": "ignored"}

    sender_data = data["senderData"]
    sender = sender_data["sender"]
    msg_data = data["messageData"]
    msg_type = msg_data["typeMessage"]
    msg_id = data["idMessage"]

    # if it is in group chat
    if "@g.us" in sender_data.get("chatId", ""):
        return group_handler(sender_data, msg_data, msg_type, msg_id)

    # ignore duplicates
    if await duplicate_checker.is_duplicate(msg_id):
        logger.info(f"Duplicate message ignored: {msg_id} from {sender}")
        return {"status": "duplicate_ignored"}

    # pic
    if msg_type == "imageMessage":
        image_url = msg_data["fileMessageData"]["downloadUrl"]

        # analyze image
        result = check_barcode(image_url)
        green_send_message(sender, result, reply_to=msg_id)
        return {"status": "image_processed"}

    # text
    if msg_type == "textMessage":
        text = msg_data["textMessageData"]["textMessage"].lower().strip()
        if text in HELP_KEYWORDS:
            logger.info(f"Help message requested from {sender}")
            green_send_message(sender, TEXTS["welcome"])
            return {"status": "help_sent"}


        digits = "".join(filter(str.isdigit, text))
        if digits:
            result = check_barcode(digits, text=True)
            green_send_message(sender, result, reply_to=msg_id)
        elif any(keyword in text for keyword in THANKS_KEYWORDS):
            green_send_message(sender, TEXTS["thanks"], reply_to=msg_id)
        else:
            green_send_message(sender, TEXTS["errors"]["invalid_message"], reply_to=msg_id)

        return {"status": "text_processed"}

    # all the rest
    green_send_message(
        sender,
        TEXTS["errors"]["unsupported_type"],
        reply_to=msg_id
    )
    return {"status": "unsupported"}


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


def group_handler(sender_data, msg_data, msg_type, msg_id):
    actual_sender = sender_data.get("sender", "Unknown")
    group_name = sender_data.get("chatName", "Unknown Group")
    logger.info(f"Group {msg_type} from {group_name}: sender={actual_sender}")

    # reply only for pic with barcode:
    if msg_type == "imageMessage":
        image_url = msg_data["fileMessageData"]["downloadUrl"]

        # analyze image
        result = check_barcode(image_url)
        if result == TEXTS["errors"]["barcode_not_found"] or \
           result == TEXTS["errors"]["unsupported_barcode"]:
            logger.info(f"Group image ignored (no barcode): {msg_id} from {actual_sender} in {group_name}")
            return {"status": "group_image_ignored"}

        green_send_message(sender_data["chatId"], result, reply_to=msg_id)
        return {"status": "group_image_processed"}

    return {"status": "group_ignored"}
