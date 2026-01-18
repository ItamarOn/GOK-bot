from config import REPORTS_CHAT_ID, tz_info, RENDER_GIT_COMMIT
from core.message import green_send_message, is_green_available
from datetime import datetime

def report_new_user_startup(whatsapp_request):
    time_now = datetime.now(tz_info).strftime("%H:%M %d/%m")
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    green_send_message(
        REPORTS_CHAT_ID,
        f"({time_now}) new chat started.\n"
        f"user whatsapp`s name: {s['senderName']} from number {s['sender'].split('@')[0]})\n"
        f"the message is : `{m.get('textMessage', {}).get('textMessageData', '')}"
        f" {m.get('fileMessageData', {}).get('mimeType', '')}`"
    )

def report_service_version():
    green_send_message(
        REPORTS_CHAT_ID,
        f"app version: {RENDER_GIT_COMMIT[:7]}"
    )