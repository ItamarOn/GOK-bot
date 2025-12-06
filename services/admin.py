import socket
import platform
from config import ADMIN_CHAT_ID, ENVIRONMENT, logger
from services.message import green_send_message


def update_admin_startup():
    try:
        green_send_message(
            ADMIN_CHAT_ID,
            "Bot has been started.\n\n"
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