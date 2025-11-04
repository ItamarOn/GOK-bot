# fast api application with a single POST endpoint get json, make some request and return json
from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from engine import check_barcode
from config import logger
import requests
import os

app = FastAPI()

# basic health check endpoint for any browser
@app.get("/health_check")
async def health_check(request: Request):
    client_ip = request.client.host or "unknown"
    logger.debug(f"health_check from {client_ip}")
    return {"status": "ok",
            "ip": f"{client_ip}"}


# full cycle processing endpoint for Twilio webhook
@app.post("/process")
async def process(request: Request):
    logger.debug('start process')
    form = await request.form()
    data = dict(form)
    logger.debug(f'massage from: {data.get("From", "")}')
    resp = MessagingResponse()
    if data.get('MessageType', '') == 'image':
        img_link = data['MediaUrl0']
        bc = check_barcode(img_link)
        resp.message(bc)
    else:
        logger.debug('not a pic, checking if text include barcode digits')
        # get 13 digits number from the text
        text = data.get('Body', '')
        digits = ''.join(filter(str.isdigit, text))
        if digits:
            bc = check_barcode(digits, text=True)
            resp.message(bc)
        else:
            resp.message("Not a pic and no digits found in the text 😢")
    logger.debug('end process')
    return Response(content=str(resp), media_type="application/xml")

# Cycle for Meta develop:

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


@app.get("/webhook")
async def verify_webhook(request: Request):
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


@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    logger.debug(f"Incoming webhook: {data}")

    try:
        if "messages" in data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}):
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            from_number = message["from"]
            text = message["text"]["body"]

            reply = f"הודעה התקבלה: {text}"
            send_message(from_number, reply)
    except Exception as e:
        logger.exception(f"Error processing webhook")

    return {"status": "received"}


def send_message(to: str, text: str):
    url = f"https://graph.facebook.com/v22.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    response = requests.post(url, headers=headers, json=payload)
    logger.info(f"Send status: {response.status_code} | {response.text}")