from time import time
import requests
from fastapi import FastAPI, Request, Response

from engine import check_barcode
from config import logger, VERIFY_TOKEN, ACCESS_TOKEN, PHONE_ID
from texts import TEXTS, HELP_KEYWORDS

app = FastAPI()


@app.get("/health_check")
async def health_check(request: Request):
    client_ip = request.client.host or "unknown"
    logger.debug(f"health_check from {client_ip}")
    return {
        "status": "ok",
        "ip": f"{client_ip}",
        "time": f"{time()}",
    }


# GET webhook - only for first Meta verification
@app.get("/webhook")
async def verify_webhook(request: Request):
    logger.debug(f"webhook called")
    logger.debug(f"request:\n{request.__dict__}\n")
    logger.debug(f"VERIFY_TOKEN={VERIFY_TOKEN}")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    client_ip = request.client.host
    logger.debug(f"Webhook verification attempt from {client_ip}")

    # Meta expects a *plain text response* with the challenge
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully ✅")
        return Response(content=str(challenge), media_type="text/plain")
    logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
    return Response(content="forbidden", status_code=403)


# POST webhook - main message processing
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    logger.debug(f"Incoming webhook: {data}")

    try:
        if "messages" in data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}):
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            from_number = message["from"]
            message_id = message["id"]

            if message["type"] == "image":
                image_url = await get_image_url(message)
                if not image_url:
                    logger.error("Failed to get image URL from Meta")
                    send_message(
                        from_number,
                        TEXTS["errors"]["image_processing"],
                        reply_to=message_id,
                    )
                    return {"status": "received"}

                result = check_barcode(image_url)
                send_message(from_number, result, reply_to=message_id)

            elif message["type"] == "text":
                text = message["text"]["body"].lower().strip()
                logger.debug(f"Received text message: {text}")
                if text in HELP_KEYWORDS:
                    logger.info(f"Help message requested from {from_number}")
                    send_message(from_number, TEXTS["welcome"])
                    return {"status": "help_sent"}


                digits = ''.join(filter(str.isdigit, text))
                if digits:
                    result = check_barcode(digits, text=True)
                    send_message(from_number, result, reply_to=message_id)
                else:
                    reply = TEXTS["errors"]["invalid_message"]
                    send_message(from_number, reply, reply_to=message_id)
            else:
                logger.info(f"Unsupported message type: {message['type']}")
                send_message(
                    from_number,
                    TEXTS["errors"]["unsupported_type"],
                    reply_to=message_id,
                )
    except Exception as e:
        logger.exception(f"Error processing webhook")

    return {"status": "received"}


async def get_image_url(message):
    media_id = message["image"]["id"]
    image_info_url = f"https://graph.facebook.com/v22.0/{media_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    image_info = requests.get(image_info_url, headers=headers).json()
    logger.debug(f"Image info: {image_info}")
    image_url = image_info.get("url")
    return image_url


def send_message(to: str, text: str, reply_to: str = None):
    url = f"https://graph.facebook.com/v22.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }

    if reply_to:
        payload["context"] = {"message_id": reply_to}

    logger.debug(f"Sending payload: {payload}")

    response = requests.post(url, headers=headers, json=payload)
    logger.info(f"Send status: {response.status_code} | {response.text}")
