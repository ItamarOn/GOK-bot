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

    # TEXT:
    # {'typeWebhook': 'incomingMessageReceived',
    #  'instanceData': {'idInstance': 7105398750,
    #                   'wid': '972556815085@c.us',
    #                   'typeInstance': 'whatsapp'
    #                   },
    #  'timestamp': 1764531848,
    #  'idMessage': 'AC9335C6B9C6B5CCAFEC5DB341B6F71E',
    #  'senderData': {'chatId': '972547271571@c.us',
    #                 'chatName': '😎',
    #                 'sender': '972547271571@c.us',
    #                 'senderName': '😎',
    #                 'senderContactName': ''
    #                 },
    #  'messageData': {'typeMessage': 'textMessage',
    #                  'textMessageData': {'textMessage': 'הלו?'}
    #                  }
    #     }
    #
    # IMAGE:
    # {'typeWebhook': 'incomingMessageReceived',
    # 'instanceData': {'idInstance': 7105398750,
    #                  'wid': '972556815085@c.us',
    #                  'typeInstance': 'whatsapp'
    #                  },
    # 'timestamp': 1764533249,
    # 'idMessage': 'ACA03B1F1029CA2081E3EB455844CF50',
    # 'senderData': {'chatId': '972547271571@c.us',
    #                'chatName': '😎',
    #                'sender': '972547271571@c.us',
    #                'senderName': '😎',
    #                'senderContactName': ''
    #                },
    # 'messageData': {'typeMessage': 'imageMessage',
    #                 'fileMessageData': {'downloadUrl': 'https://do-media-7105.fra1.digitaloceanspaces.com/7105398750/9182bc37-9d40-4274-b7c7-2ed782051329.jpg',
    #                                     'caption': '',
    #                                     'fileName': '9182bc37-9d40-4274-b7c7-2ed782051329.jpg',
    #                                     'jpegThumbnail': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDABsSFBcUERsXFhceHBsgKEIrKCUlKFE6PTBCYFVlZF9VXVtqeJmBanGQc1tdhbWGkJ6jq62rZ4C8ybqmx5moq6T/2wBDARweHigjKE4rK06kbl1upKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKSkpKT/wgARCABIAEgDASIAAhEBAxEB/8QAGgAAAwEBAQEAAAAAAAAAAAAAAAMEAgEFBv/EABgBAAMBAQAAAAAAAAAAAAAAAAECAwAE/9oADAMBAAIQAxAAAABLPOVLqo9LxXqfd+dqlM56Mei6tFFYQlLIdEWr9NpVVZZEtJWeg4BX2qvRNrwiyb5gJ1NdMuiLg7Ncm4tpNCbIsYMK8a3NtGQaJYRojYUHeht3obbAI//EACERAAICAQMFAQAAAAAAAAAAAAABAhESITFRAxATICJB/9oACAECAQE/AKQ4qqILHQb4Eu2L2F0p8HikNSW5DcVn0ZSX6ZyIiehaG9SxMv0//8QAIREAAgECBgMAAAAAAAAAAAAAAAERAhIDEBMgMVEhMkH/2gAIAQMBAT8AWF9Q6XMlbbfk9UNdl9XZqPsuUyPEVXIrSrjKScnsjd//xAAoEAACAgEDAwQCAwEAAAAAAAABAgADEQQSITFBURMiMmEFcRAUQjP/2gAIAQEAAT8Ao1+KcO2Wz0MF1D5ZkAIHWa7Uf2GStBgSvQvXpURcEdTiUkaWgu/AAmv1Tam8senYSqwq3E09D6qzj4jqfESj0wACBWveavH9h8DjMBwYcFs4xKtTdWfbY0s1N+qAV24E1Fe4gAdO809HqWBc7R3Jm8VYqqIVDwWgswfRrYEdyYVLEk9TCh8TYTFrOYqkDgQlkBUjr3lKqWHjvLnQ+wKB4iabJza2B4EVBFr+syvRvY+0Jj7mo0racjcM58TeuPiRGNZ6xrK1rIRefMIZnBJAxH1G98HiJUSczSacMNxiYXOO8cMa8Hkz0DsOQM9pVSpGLq1j6HTPnAI/Us/Fofg5H7ln4qz/AC4MA2iVDZSPuW2mvpBqmYMdvQx9SVZQF6w6gg42iVEWdRjiGxt7DJ4g3t0P8U2blA8TV5DiJ/zeOuWWbSbT9TTjoPqNTttJyMHzKqUZQQY3Amnb3y9d5DAcQIwVh5hrYjMFbAk+ZQfd+pZYrMR4i3bRtmMx1KZKnEFtp/2YHt49xzPWfHyMW58fIz1rBzuMNhJ68xbiMZ6z//4AAwD/2Q==',
    #                                     'isAnimated': False,
    #                                     'mimeType': 'image/jpeg',
    #                                     'forwardingScore': 1,
    #                                     'isForwarded': True
    #                                     }
    #                 }
    # }
    if data.get("typeWebhook") != "incomingMessageReceived":
        return {"status": "ignored"}

    sender = data["senderData"]["sender"]
    msg_data = data["messageData"]
    msg_type = msg_data["typeMessage"]
    msg_id = data["idMessage"]

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
