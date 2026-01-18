from config import REPORTS_CHAT_ID, ENVIRONMENT, RENDER_GIT_COMMIT, logger, tz_info
from core.message import green_send_message, is_green_available
from datetime import datetime

def report_new_user_startup(whatsapp_request):
    time_now = datetime.now(tz_info).strftime("%H:%M %d/%m")
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    green_send_message(
        REPORTS_CHAT_ID,
        f"({time_now}) {s['senderName']} ({s['sender']}) started a with:\n"
        f"`{m.get('textMessage', {}).get('textMessageData', '')}"
        f" {m.get('fileMessageData', {}).get('mimeType', '')}`"
    )
