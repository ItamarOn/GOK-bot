import copy
from config import logger

def _redact_sensitive_data(data, target_key="jpegThumbnail", replacement="..."):
    """
    Recursively traverse a dictionary or list to replace target_key values.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                data[key] = replacement
            else:
                _redact_sensitive_data(value, target_key, replacement)
    elif isinstance(data, list):
        for item in data:
            _redact_sensitive_data(item, target_key, replacement)
    return data


def thin_log(whatsapp_request):
    log_view = copy.deepcopy(whatsapp_request)
    _redact_sensitive_data(log_view)

    sender_name = whatsapp_request.get('senderData', {}).get('senderName')
    download_url = whatsapp_request.get('messageData', {}).get('fileMessageData', {}).get('downloadUrl')

    full_log = f"Request: {log_view}"
    if sender_name and download_url:
        full_log += f"\n🔽 {download_url} ▶️ {sender_name}"

    logger.info(full_log)