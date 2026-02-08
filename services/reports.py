from config import REPORTS_CHAT_ID, tz_info, RENDER_GIT_COMMIT
from core.message import green_send_message
from datetime import datetime

def report_new_user_startup(whatsapp_request):
    time_now = datetime.now(tz_info).strftime("%H:%M %d/%m")
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    text = (m.get('textMessageData', {}).get('textMessage', '') or
            m.get('fileMessageData', {}).get('mimeType', '') or
            m.get('extendedTextMessageData', {}).get('text', '') or
            'unextractable')
    green_send_message(
        REPORTS_CHAT_ID,
        f"({time_now}) new chat started.\n"
        f"user whatsapp's name: `{s['senderName']}` from number {s['sender'].split('@')[0]}\n"
        f"the message is : `{text}`"
    )
    return text

def report_quoted_response(whatsapp_request):
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    green_send_message(
        REPORTS_CHAT_ID,
        f"User: `{s['senderName']}` ({s['sender'].split('@')[0]}) quote bot group message and wrote: "
        f"`{m.get('extendedTextMessageData', {}).get('text', '')}"
    )

def report_bug_request(whatsapp_request):
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    green_send_message(
        REPORTS_CHAT_ID,
        f"Bug reported by `{s['senderName']}` ({s['sender'].split('@')[0]}), the message is:\n"
        f"`{m.get('textMessageData', {}).get('textMessage', '')}`"
    )

async def report_version_update(db):
    cur_version = RENDER_GIT_COMMIT[:7]
    is_change, version = await db.sync_app_version(cur_version)
    if is_change:
        green_send_message(
            REPORTS_CHAT_ID,
            f"New bot version: {version}"
        )

def update_weekly_status(result: dict):
    """
    {
        "week_start": week_key,
        "received": {
            "group": int(self.client.get(f"stats:{week_key}:received:group") or 0),
            "private": int(self.client.get(f"stats:{week_key}:received:private") or 0)\
            "admin": int(self.sync_client.get(f"stats:{week_key}:received:group:admin") or 0)

        },
        "sent": {
            "group": int(self.client.get(f"stats:{week_key}:sent:group") or 0),
            "private": int(self.client.get(f"stats:{week_key}:sent:private") or 0)
        }
    }
    """
    msg = (
        f"📊 Weekly report for {result['week_start']}:\n"
        "🤖Bot private conversations: \n"
        f"   - 📥 Received: {result['received']['private']}\n"
        f"   - 📤 Sent:{result['sent']['private']}\n"
        f"👥Messages in Groups:\n"
        f"   - 📥 Received: {result['received']['group']}\n"
        f"   - 📤 Sent by Bot: {result['sent']['group']}\n"
        f"   - 📤 Sent by Admins: {result['received']['admin']}\n"
    )
    green_send_message(REPORTS_CHAT_ID, msg)