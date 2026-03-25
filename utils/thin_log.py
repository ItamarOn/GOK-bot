import copy
from config import logger

def thin_log(whatsapp_request):
    log_view = copy.deepcopy(whatsapp_request)
    try:
        log_view['messageData']['fileMessageData']['jpegThumbnail'] = "..."
    except (KeyError, TypeError):
        pass
    try:
        log_view['messageData']['extendedTextMessageData']['jpegThumbnail'] = "..."
    except (KeyError, TypeError):
        pass

    logger.info(f"Request: {log_view}")
