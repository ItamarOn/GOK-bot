# tests for the logic of GOK-bot/services/group.py

import pytest
import fakeredis
from unittest.mock import patch

from services.group import group_handler
from utils.texts import TEXTS
from utils.redis_manager import RedisManager

# make fixture for all tests in this file
@pytest.fixture(autouse=True)
def mock_redis_manager():
    fake_client = fakeredis.aioredis.FakeRedis()
    rm = RedisManager()
    rm.client = fake_client
    with patch('services.group.db', rm):
        yield fake_client

# duplicate call at nighttime
@patch('services.group.is_night_hours', return_value=True)
@pytest.mark.asyncio
async def test_group_handler_night_duplicate(
        mock_is_night_hours,
        mock_redis_manager
):
    sender_data = {
        "chatId": "123123123",
        "chatName": "Group Of Test 2 👳🏻‍♂️",
        "sender": "972547777777@c.us"
    }
    msg_data = {
        "fileMessageData": {
            "downloadUrl": "http://example.com/image_with_no_barcode.jpg"
        }
    }
    msg_type = "imageMessage"
    msg_id = "ACF1C883BE25C3AEE97E812C1234567B"
    timestamp = 1234567890

    # result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_redis_manager)
    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)
    assert result['status'] == 'group_outside_hours'
    result2 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp + 1)
    assert result2['status'] == 'group_outside_hours_many_messages'
    result3 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp + 1)
    assert result3['status'] == 'group_outside_hours_many_messages'

    assert mock_is_night_hours.call_count == 3

    redis_values = await mock_redis_manager.execute_command('KEYS', '*')
    assert redis_values == [b'dup:sender:Group Of Test 2 '
                            b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f:972547777777@c.us']


# image with no barcode
@patch('services.group.check_barcode', return_value=TEXTS["errors"]["barcode_not_found"])
@patch('services.group.green_send_message')
@patch('services.group.is_night_hours', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_no_barcode(
        mock_check_barcode,
        mock_green_send_message,
        mock_is_night_hours,
        mock_redis_manager
):
    sender_data = {
        "chatId": "group123",
        "chatName": "Test Group",
        "sender": "user123"
    }
    msg_data = {
        "fileMessageData": {
            "downloadUrl": "http://example.com/image_with_no_barcode.jpg"
        }
    }
    msg_type = "imageMessage"
    msg_id = "msg001"
    timestamp = 1234567890

    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)
    assert result["status"] == "group_image_ignored"


# image with barcode that not found
@patch('services.group.check_barcode',
       return_value='{0}, {1}'.format('123456789\n ברקוד', TEXTS["errors"]["gok_not_found"]))
@patch('services.group.green_send_message')
@patch('services.group.is_night_hours', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_barcode_not_found(
        mock_check_barcode,
        mock_green_send_message,
        mock_is_night_hours,
        mock_redis_manager
):
    sender_data = {
        "chatId": "123123123",
        "chatName": "Group Of Test 2",
        "sender": "972547777777@c.us"
    }
    msg_data = {
        "fileMessageData": {
            "downloadUrl": "http://example.com/image_with_barcode_not_found.jpg"
        }
    }
    msg_type = "imageMessage"
    msg_id = "ACF1C883BE25C3AEE97E812C1234567B"
    timestamp = 1234567890

    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)
    assert result['status'] == 'group_unlisted'
    result2 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)
    assert result2['status'] == 'group_duplicate_barcode_ignored'

    redis_values = await mock_redis_manager.execute_command('KEYS', '*')
    assert redis_values == [b'dup:barcode:123456789']


# image with kosher barcode
@patch('services.group.check_barcode',
       return_value='123456789\n ברקוד {}'.format(
           TEXTS["product_status"]["kosher_template"].format(
               kashrut_type='kashrut_type',
               cert='cert')
       ))
@patch('services.group.green_send_message')
@patch('services.group.is_night_hours', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_kosher_barcode(
        mock_check_barcode,
        mock_green_send_message,
        mock_is_night_hours,
        mock_redis_manager,
):
    sender_data = {
        "chatId": "123123123",
        "chatName": "Group Of Test 2",
        "sender": "972547777777@c.us"
    }
    msg_data = {
        "fileMessageData": {
            "downloadUrl": "http://example.com/image_with_kosher_barcode.jpg"
        }
    }
    msg_type = "imageMessage"
    msg_id = "ACF1C883BE25C3AEE97E812C1234567B"
    timestamp = 1234567890
    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)
    assert result['status'] == 'group_listed'
    result2 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp)
    assert result2['status'] == 'group_duplicate_barcode_ignored'
