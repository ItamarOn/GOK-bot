from time import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from config import logger
from services.admin import update_admin_startup, update_admin_shutdown
from services.group import group_handler
from services.personal_chat import personal_chat_handler
from ducplicate_checker import DuplicateChecker

duplicate_checker = DuplicateChecker()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown lifecycle for FastAPI"""
    await duplicate_checker.connect()
    logger.info("Redis connected successfully")
    update_admin_startup()
    yield
    if duplicate_checker.client:
        await duplicate_checker.client.close()
        logger.info("Redis connection closed")
        update_admin_shutdown()


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
    timestamp = data["timestamp"]

    # Group Chat logic:
    if "@g.us" in sender_data.get("chatId", ""):
        return group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)

    # Personal Chat logic:
    return await personal_chat_handler(msg_data, msg_id, msg_type, sender, duplicate_checker)
