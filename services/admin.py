import socket
from config import ADMIN_CHAT_ID, ENVIRONMENT, RENDER_GIT_COMMIT, SERVER_PROVIDER, APP_GIT_SHA, logger, tz_info
from core.message import green_send_message, is_green_available
from datetime import datetime
import random

GIT_SHA = RENDER_GIT_COMMIT if SERVER_PROVIDER == "render" else APP_GIT_SHA


async def update_admin_startup():
    if is_green_available():
        logger.info('Green API is available - sending startup message to admin.')
    else:
        logger.error('Green API is not available')
    time_now = datetime.now(tz_info).strftime("%H:%M %d/%m")
    try:
        await green_send_message(
            ADMIN_CHAT_ID,
            f"🟢Active {ENVIRONMENT} {GIT_SHA[:7]} {SERVER_PROVIDER} ({time_now})"
        )
    except:
        logger.exception("Failed to send startup message to admin.")


async def update_admin_shutdown(db):
    try:
        # group_msg_last_24h_count = await db.count_keys('dup:msg-g:*')
        # personal_msg_last_24h_count = await db.count_keys('dup:msg-p:*')
        message = (
            f"🔴Sleep ({ENVIRONMENT}-{SERVER_PROVIDER})"
            # f"Last 24h processed messages:\n"
            # f"  - Group: {group_msg_last_24h_count}\n"
            # f"  - Personal: {personal_msg_last_24h_count}\n"
        )
        await green_send_message(ADMIN_CHAT_ID, message)
    except:
        logger.exception("Failed to send shutdown message to admin.")
