from config import logger
from engine import check_barcode
from services.message import green_send_message
from texts import TEXTS


def group_handler(sender_data, msg_data, msg_type, msg_id, timestamp):
    actual_sender = sender_data.get("sender", "Unknown")
    group_name = sender_data.get("chatName", "Unknown Group")
    logger.info(f"Group {msg_type} from {group_name} sender: {actual_sender}")

    if is_night_hours(timestamp):  # Big TODO - should be in separate file. not in main
        logger.info(f"Outside working hours - group message ignored: {msg_id} from {actual_sender} in {group_name}")
        green_send_message(sender_data["chatId"], TEXTS["errors"]["out_of_working_hours"], reply_to=msg_id)
        return {"status": "group_outside_hours"}

    # reply only for pic with barcode:
    if msg_type == "imageMessage":
        image_url = msg_data["fileMessageData"]["downloadUrl"]

        # analyze image
        result = check_barcode(image_url)
        if result == TEXTS["errors"]["barcode_not_found"] or \
           result == TEXTS["errors"]["unsupported_barcode"]:
            logger.info(f"Group image ignored (no barcode): {msg_id} from {actual_sender} in {group_name}")
            return {"status": "group_image_ignored"}

        green_send_message(sender_data["chatId"], result, reply_to=msg_id)
        return {"status": "group_image_processed"}

    return {"status": "group_ignored"}


def is_night_hours(hour: int) -> bool:
    """calculte the hour in israel from the timestamp (unix), and check if it is working hours 8-22"""
    return False
