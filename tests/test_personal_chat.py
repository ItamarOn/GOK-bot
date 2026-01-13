# same as in test_group.py but for personal chat, check if incremrent counter works

# image with no barcode
from unittest.mock import patch
import pytest
from services.personal_chat import personal_chat_handler
from utils.redis_manager import RedisManager
import fakeredis

@pytest.fixture(autouse=True)
def mock_redis_manager():
    fake_client = fakeredis.aioredis.FakeRedis()
    rm = RedisManager()
    rm.client = fake_client
    with patch('services.personal_chat.db', rm):
        yield fake_client

@patch('services.personal_chat.check_barcode', return_value="")
@patch('services.personal_chat.green_send_message')
@pytest.mark.asyncio
async def test_personal_chat_handler_no_barcode(
        mock_green_send_message,
        mock_redis_manager
):
    msg_data = {
        "fileMessageData": {
            "downloadUrl": "http://some_url.jpg"
        }
    }

    result = await personal_chat_handler(msg_data, "ABC123", "imageMessage", "054222222@c.us")
    assert result["status"] == "image_processed"
