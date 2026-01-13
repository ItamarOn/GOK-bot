from config import logger
from core.engine import check_barcode

from core.message import green_send_message
from utils.time_check import is_night_hours
from utils.texts import TEXTS


async def group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, duplicate_checker):
    actual_sender = sender_data.get("sender", "Unknown")
    group_name = sender_data.get("chatName", "Unknown Group")
    logger.info(f"Group {msg_type} from {group_name} sender: {actual_sender}")

    if is_night_hours(timestamp):
        if not await duplicate_checker.is_duplicate('sender', f'{group_name}:{actual_sender}', ttl_seconds=300):
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
        if detected_barcode and await duplicate_checker.is_duplicate('barcode', detected_barcode, ttl_seconds=300):
            logger.info(f"Duplicate barcode {detected_barcode} from {actual_sender} in {group_name}")
            return {"status": "group_duplicate_barcode_ignored"}

        if TEXTS["errors"]["gok_not_found"] in result:
            logger.info(f"Group image barcode not found in GOK: {msg_id} from {actual_sender} in {group_name}")
            green_send_message(sender_data["chatId"], TEXTS['group']['unlisted'], reply_to=msg_id)
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