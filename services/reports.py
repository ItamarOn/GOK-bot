from config import REPORTS_CHAT_ID, tz_info, RENDER_GIT_COMMIT, SERVER_PROVIDER, APP_GIT_SHA
from core.message import green_send_message
from datetime import datetime

async def report_new_user_startup(whatsapp_request):
    time_now = datetime.now(tz_info).strftime("%H:%M %d/%m")
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    text = (m.get('textMessageData', {}).get('textMessage', '') or
            m.get('fileMessageData', {}).get('mimeType', '') or
            m.get('extendedTextMessageData', {}).get('text', '') or
            'unextractable')
    await green_send_message(
        REPORTS_CHAT_ID,
        f"🆕({time_now}) new chat started.\n"
        f"User whatsapp's name: '{s['senderName']}'\n"
        f"Number: {s['sender'].split('@')[0]}\n"
        f"Message: `{text}`"
    )
    return text

async def report_quoted_response(whatsapp_request):
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    await green_send_message(
        REPORTS_CHAT_ID,
        f"💬User: '{s['senderName']}' ({s['sender'].split('@')[0]}) quote bot group message and wrote:\n"
        f"`{m.get('extendedTextMessageData', {}).get('text', '')}`"
    )

async def report_bug_request(whatsapp_request):
    s = whatsapp_request['senderData']
    m = whatsapp_request['messageData']
    await green_send_message(
        REPORTS_CHAT_ID,
        f"🐞Bug reported by '{s['senderName']}' ({s['sender'].split('@')[0]}), the message is:\n"
        f"`{m.get('textMessageData', {}).get('textMessage', '')}`"
    )

async def report_version_update(db):
    cur_version = RENDER_GIT_COMMIT if SERVER_PROVIDER == "render" else APP_GIT_SHA

    is_change, version = await db.sync_app_version(cur_version[:7])
    if is_change:
        await green_send_message(
            REPORTS_CHAT_ID,
            f"🚀 New bot version: {version}"
        )

async def update_weekly_status(result: dict):
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
        f"📊 Weekly report from {result['week_start']}:\n\n"
        "🤖Bot private conversations: \n"
        f"   - 📥 Received: {result['received']['private']}\n"
        f"   - 📤 Sent:{result['sent']['private']} (Failed/Delayed: {result['sent']['failed_private']})\n\n"
        f"👥Messages in Groups:\n"
        f"   - 📥 Received: {result['received']['group']}\n"
        f"   - 📤 Sent by Bot: {result['sent']['group']} (Failed: {result['sent']['failed_group']})\n"
        f"   - 📤 Sent by Admins: {result['received']['admin']}\n"
    )
    await green_send_message(REPORTS_CHAT_ID, msg)