from time import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends, status
from fastapi.security import APIKeyHeader

from config import logger, ADMIN_SECRET_TOKEN, MATES
from services.admin import (
    update_admin_startup,
    update_admin_shutdown,
)
from services.reports import report_version_update, update_weekly_status
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
    await report_version_update(db)
    yield
    if db.client:
        await update_admin_shutdown(db)
        await db.client.close()
        logger.info("Redis connection closed")

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

@app.delete("/redis/remove", tags=["system"])
async def redis_del_key(key:str = 'nothing', admin: str = Depends(verify_admin)):
    if not db.client:
        return {"error": "Redis client not connected"}
    if not key or key=='*':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid key provided"
        )
    deleted = await db.client.delete(key)
    return {"deleted_keys": deleted}

@app.get("/health/redis/all", tags=["system"])
async def redis_all_data(limit: int = 100, prefix: str = 'co', admin: str = Depends(verify_admin)):
    if not db.client:
        return {"error": "Redis client not connected"}

    if not prefix or '*' in prefix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid prefix provided"
        )

    prefix_match = f"{prefix}*"
    match_keys = {}
    async for key in db.client.scan_iter(match=prefix_match, count=100):
        if len(match_keys) >= limit:
            break
        value = await db.client.get(key)
        match_keys[key] = value

    return {
        "prefix": prefix,
        "limit": limit,
        "count": len(match_keys),
        "data": dict(sorted(match_keys.items()))
    }


@app.get("/stats", tags=["system"])
async def get_stats(offset: int = 0, send_whatsapp: bool=False, admin: str = Depends(verify_admin)):
    """Get statistics for current week and last week only (free tier limitation)"""
    if offset > 1:
        return {"error": "Offset too large"}
    result = await db.get_weekly_stats(offset)
    if send_whatsapp:
        update_weekly_status(result)
    return result


@app.post("/webhook-green", tags=["whatsapp"])
async def green_webhook(request: Request, background_tasks: BackgroundTasks):
    whatsapp_request = await request.json()
    logger.info(f"Request: {whatsapp_request}")

    if whatsapp_request.get("typeWebhook") != "incomingMessageReceived":
        return {"status": "ignored"}

    is_group = whatsapp_request.get("senderData", {}).get("chatId", "").endswith("@g.us")
    db.track_received_message(is_group=is_group)

    # Group Chat logic:
    if "@g.us" in whatsapp_request["senderData"].get("chatId", ""):
        # reduce unprocessed tasks:
        if whatsapp_request["senderData"].get('sender').split('@')[0] in MATES:
            return {"status": "group_mate_ignored"}
        if whatsapp_request["messageData"].get("typeMessage") != "imageMessage":
            return {"status": "group_non_image_ignored"}
        # group message processing in background:
        background_tasks.add_task(group_handler, whatsapp_request)
        return {'status': 'group_acknowledged'}

    # Personal Chat logic:
    background_tasks.add_task(personal_chat_handler, whatsapp_request)
    return {"status": "personal_acknowledged"}
