import socket
from config import ADMIN_CHAT_ID, ENVIRONMENT, logger
from services.message import green_send_message, is_green_available
from datetime import datetime

def update_admin_startup():
    if is_green_available():
        logger.info('Green API is available - sending startup message to admin.')
    else:
        logger.error('Green API is not available')
    time_now = datetime.now().strftime("%H:%M %d/%m")
    try:
        green_send_message(
            ADMIN_CHAT_ID,
            f"Bot has been started ({time_now}).\n\n"
            f"Environment: {ENVIRONMENT}\n"
            f"hostname: {socket.gethostname()}\n"
            # add bot version
        )
    except:
        logger.exception("Failed to send startup message to admin.")


def update_admin_shutdown():
    try:
        # add redis personal count
        # add redis group count
        green_send_message(
            ADMIN_CHAT_ID,
            "Bot is shutting down.\n\n"
            f"Environment: {ENVIRONMENT}\n"
            f"hostname: {socket.gethostname()}\n"
        )
    except:
        logger.exception("Failed to send shutdown message to admin.")