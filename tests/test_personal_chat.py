# same as in test_group.py but for personal chat, check if incremrent counter works

# image with no barcode
from unittest.mock import patch
import pytest
import fakeredis

from services.personal_chat import personal_chat_handler
from utils.redis_manager import RedisManager

from examples import personal_pic_example


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
    result = await personal_chat_handler(personal_pic_example)
    assert result["status"] == "image_processed"
