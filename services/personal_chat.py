from config import logger
from core.engine import check_barcode
from core.message import green_send_message
from services.reports import report_new_user_startup
from utils.texts import HELP_KEYWORDS, TEXTS, THANKS_KEYWORDS
from utils.redis_manager import db

async def personal_chat_handler(whatsapp_request: dict):
    sender_data = whatsapp_request["senderData"]
    sender = sender_data["sender"]
    msg_data = whatsapp_request["messageData"]
    msg_type = msg_data["typeMessage"]
    msg_id = whatsapp_request["idMessage"]

    # ignore duplicates
    if await db.is_duplicate('msg-p', msg_id, ttl_seconds=86400):
        logger.info(f"Duplicate message ignored: {msg_id} from {sender}")
        return {"status": "duplicate_ignored"}

    sender_digits = "".join(c for c in sender if c.isdigit())
    number_of_requests = db.increment_counter(sender_digits)
    if number_of_requests == 1:
        report_new_user_startup(whatsapp_request)
        green_send_message(sender, TEXTS["welcome"])

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

        digits = "".join(c for c in text if c.isdigit())
        if digits:
            result = check_barcode(digits, text=True)
            green_send_message(sender, result, reply_to=msg_id)
        elif any(keyword in text for keyword in THANKS_KEYWORDS):
            green_send_message(sender, TEXTS["thanks"], reply_to=msg_id)
        else:
            green_send_message(sender, TEXTS["errors"]["invalid_message"], reply_to=msg_id)

        return {"status": "text_processed"}

    # all the rest
    green_send_message(
        sender,
        TEXTS["errors"]["unsupported_type"],
        reply_to=msg_id
    )
    return {"status": "unsupported"}
