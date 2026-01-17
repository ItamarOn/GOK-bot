from config import logger, MATES, ADMIN_CHAT_ID
from core.engine import check_barcode

from core.message import green_send_message
from utils.time_check import is_night_hours, is_too_old
from utils.texts import TEXTS
from utils.redis_manager import db

async def group_handler(whatsapp_request: dict):
    sender_data = whatsapp_request["senderData"]
    msg_data = whatsapp_request["messageData"]
    msg_type = msg_data["typeMessage"]
    msg_id = whatsapp_request["idMessage"]
    timestamp = whatsapp_request["timestamp"]
    actual_sender = sender_data.get("sender", "Unknown")
    group_name = sender_data.get("chatName", "Unknown Group")
    logger.info(f"Group {msg_type} from {group_name} sender: {actual_sender}")

    if is_too_old(timestamp, max_age_hours=12):
        logger.info(f"Old group message ignored: {msg_id} from {actual_sender} in {group_name}")
        return {"status": "group_message_too_old"}

    if await db.is_duplicate('msg-g', msg_id, ttl_seconds=86400):
        logger.info(f"Duplicate message ignored: {msg_id} from {actual_sender} in {group_name}")
        return {"status": "duplicate_ignored"}

    if actual_sender.split('@')[0] in MATES:
        return {"status": "group_mate_ignored"}

    # if is_night_hours(timestamp):
    if is_night_hours(timestamp) and actual_sender != ADMIN_CHAT_ID:
        if not await db.is_duplicate('sender', f'{group_name}:{actual_sender}', ttl_seconds=300):
            return night_response(sender_data, msg_id, actual_sender, group_name)
        return {"status": "group_outside_hours_many_messages"}

    # reply only for pic with barcode:
    if msg_type == "imageMessage":
        image_url = msg_data["fileMessageData"]["downloadUrl"]

        # analyze image
        result = check_barcode(image_url)

        if TEXTS["errors"]["barcode_not_found"] in result or \
           TEXTS["errors"]["unsupported_barcode"] in result:
            logger.info(f"Group image ignored (no barcode): {msg_id} from {actual_sender} in {group_name}")
            return {"status": "group_image_ignored"}

        detected_barcode = "".join(c for c in result if c.isdigit())
        if detected_barcode and await db.is_duplicate('barcode', detected_barcode, ttl_seconds=300):
            logger.info(f"Duplicate barcode {detected_barcode} from {actual_sender} in {group_name}")
            return {"status": "group_duplicate_barcode_ignored"}

        if TEXTS["errors"]["gok_not_found"] in result:
            logger.info(f"Group image barcode not found in GOK: {msg_id} from {actual_sender} in {group_name}")
            barcode_or_barcodes_list = "".join(c for c in result if c.isdigit() or c == '\n')
            unlisted_msg = barcode_or_barcodes_list + TEXTS['group']['unlisted']
            green_send_message(sender_data["chatId"], unlisted_msg, reply_to=msg_id)
            return {"status": "group_unlisted"}

        if TEXTS["product_status"]["not_kosher"] in result or "✅" in result:
            logger.info(f"Group image with status: {msg_id} from {actual_sender} in {group_name}")
            green_send_message(sender_data["chatId"], TEXTS['group']['listed'], reply_to=msg_id)
            return {"status": "group_listed"}

    return {"status": "group_ignored"}


def night_response(sender_data, msg_id, actual_sender, group_name):
    logger.info(f"Outside working hours - ignoring group message {msg_id} from {actual_sender} in {group_name}")
    green_send_message(sender_data["chatId"], TEXTS["errors"]["out_of_working_hours"], reply_to=msg_id)
    return {"status": "group_outside_hours"}