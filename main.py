from time import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.security import APIKeyHeader

from config import logger, ADMIN_SECRET_TOKEN
from services.admin import update_admin_startup, update_admin_shutdown
from services.group import group_handler
from services.personal_chat import personal_chat_handler
from utils.redis_manager import db


api_key_header = APIKeyHeader(name="X-Admin-Token")

async def verify_admin(api_key: str = Depends(api_key_header)):
    if api_key != ADMIN_SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden: Invalid Admin Token"
        )
    return api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown lifecycle for FastAPI"""
    await db.connect()
    logger.info("Redis connected successfully")
    update_admin_startup()
    yield
    if db.client:
        await db.client.close()
        logger.info("Redis connection closed")
        update_admin_shutdown()

app = FastAPI(lifespan=lifespan)

# Health Checks
@app.get("/health/redis", tags=["system"])
async def redis_health():
    healthy = await db.ping()
    return {"redis": "ok" if healthy else "unreachable"}

@app.get("/health", tags=["system"])
async def health_check(request: Request):
    client_ip = request.client.host or "unknown"
    logger.debug(f"health_check from {client_ip}")
    return {
        "status": "ok",
        "ip": f"{client_ip}",
        "time": f"{time()}",
    }

@app.get("/health/redis/count", tags=["system"])
async def redis_keys_count(admin: str = Depends(verify_admin)):
    count = await db.count_keys()
    return {"total_keys": count}

@app.get("/health/redis/all", tags=["system"])
async def redis_all_data(limit: int = 100, admin: str = Depends(verify_admin)):
    if not db.client:
        return {"error": "Redis client not connected"}

    personal_counters_data = {}
    async for key in db.client.scan_iter(match="co*", count=100):
        if len(personal_counters_data) >= limit:
            break
        value = await db.client.get(key)
        personal_counters_data[key] = value

    duplicate_prevention = await db.count_keys(match="dup*")

    return {
        "total_redis_keys": duplicate_prevention + len(personal_counters_data),
        "count_duplicate_prevention": duplicate_prevention,
        "count_personal_counters": len(personal_counters_data),
        "limit_personal_counters": limit,
        "data": dict(sorted(personal_counters_data.items()))
    }

@app.post("/webhook-green", tags=["whatsapp"])
async def green_webhook(request: Request):
    data = await request.json()
    logger.debug(f"Green incoming: {data}")

    if data.get("typeWebhook") != "incomingMessageReceived":
        return {"status": "ignored"}

    if db.is_duplicate('msg_id', data["idMessage"], ttl_seconds=300):
        logger.info(f"Green sent this message again, probably the previous got timeout. sender:"
                    f"{data['senderData'].get('sender', 'unknown')}")
        return {"status": "duplicate_ignored"}

    sender_data = data["senderData"]
    sender = sender_data["sender"]
    msg_data = data["messageData"]
    msg_type = msg_data["typeMessage"]
    msg_id = data["idMessage"]
    timestamp = data["timestamp"]

    # Group Chat logic:
    if "@g.us" in sender_data.get("chatId", ""):
        return await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)

    # Personal Chat logic:
    return await personal_chat_handler(msg_data, msg_id, msg_type, sender)
