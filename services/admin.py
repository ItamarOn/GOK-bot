import socket
from config import ADMIN_CHAT_ID, ENVIRONMENT, RENDER_GIT_COMMIT, logger, tz_info
from core.message import green_send_message, is_green_available
from datetime import datetime

def update_admin_startup():
    if is_green_available():
        logger.info('Green API is available - sending startup message to admin.')
    else:
        logger.error('Green API is not available')
    time_now = datetime.now(tz_info).strftime("%H:%M %d/%m")
    try:
        green_send_message(
            ADMIN_CHAT_ID,
            f"🟢Bot has been started ({time_now}).\n\n"
            f"Environment: {ENVIRONMENT}\n"
            f"Version: {RENDER_GIT_COMMIT[:7]}\n"
            f"hostname: {socket.gethostname()}\n"
        )
    except:
        logger.exception("Failed to send startup message to admin.")


async def update_admin_shutdown(db):
    try:
        group_msg_last_24h_count = await db.count_keys('dup:msg-g:*')
        personal_msg_last_24h_count = await db.count_keys('dup:msg-p:*')
        # number_of_personal_chats = await db.count_keys('co:')
        green_send_message(
            ADMIN_CHAT_ID,
            "🔴Bot is shutting down.\n\n"
            f"Environment: {ENVIRONMENT}\n"
            f"hostname: {socket.gethostname()}\n"
            f"In the last 24h:\n"
            f" - Group messages processed: {group_msg_last_24h_count}\n"
            f" - Personal messages processed: {personal_msg_last_24h_count}\n"
        )
    except:
        logger.exception("Failed to send shutdown message to admin.")
