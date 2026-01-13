# tests for the logic of GOK-bot/services/group.py
# mock the core.engine.check_barcode and decide inside test func what is returned
# mock also the call to green_send_message to avoid actual sending, and assert what was sent
# mock is_night_hours to control time-based behavior
# mock duplicate_checker to control duplicate behavior
import pytest
from unittest.mock import patch, AsyncMock
from services.group import group_handler
from utils.texts import TEXTS
import fakeredis
from utils.ducplicate_checker import DuplicateChecker

# make fixture for all tests in this file
@pytest.fixture
def redis_client():
    return fakeredis.aioredis.FakeRedis()

@pytest.fixture()
def mock_duplicate_checker(redis_client):
    duplicate_checker = DuplicateChecker()
    duplicate_checker.client = redis_client
    yield duplicate_checker


# duplicate call at nighttime
@patch('services.group.is_night_hours', return_value=True)
@pytest.mark.asyncio
async def test_group_handler_night_duplicate(mock_is_night_hours, mock_duplicate_checker, redis_client):
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

    # result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_duplicate_checker)
    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_duplicate_checker)
    assert result['status'] == 'group_outside_hours'
    result2 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp + 1, mock_duplicate_checker)
    assert result2['status'] == 'group_outside_hours_many_messages'
    result3 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp + 1, mock_duplicate_checker)
    assert result3['status'] == 'group_outside_hours_many_messages'

    assert mock_is_night_hours.call_count == 3

    redis_values = await redis_client.execute_command('KEYS', '*')
    assert redis_values == [b'sender:Group Of Test 2 '
                            b'\xf0\x9f\x91\xb3\xf0\x9f\x8f\xbb\xe2\x80\x8d\xe2\x99\x82\xef\xb8\x8f:972547777777@c.us']


# image with no barcode
@patch('services.group.check_barcode', return_value=TEXTS["errors"]["barcode_not_found"])
@patch('services.group.green_send_message', new_callable=AsyncMock)
@patch('services.group.is_night_hours', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_no_barcode(mock_check_barcode, mock_green_send_message, mock_is_night_hours, redis_client):
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

    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, AsyncMock())
    assert result["status"] == "group_image_ignored"


# image with barcode that not found
@patch('services.group.check_barcode',
       return_value='{0}, {1}'.format('123456789\n ברקוד', TEXTS["errors"]["gok_not_found"]))
@patch('services.group.green_send_message', new_callable=AsyncMock)
@patch('services.group.is_night_hours', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_barcode_not_found(
        mock_check_barcode, mock_green_send_message, mock_is_night_hours, mock_duplicate_checker, redis_client):
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

    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_duplicate_checker)
    assert result['status'] == 'group_unlisted'
    result2 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_duplicate_checker)
    assert result2['status'] == 'group_duplicate_barcode_ignored'

    redis_values = await redis_client.execute_command('KEYS', '*')
    assert redis_values == [b'barcode:123456789']


# image with kosher barcode
@patch('services.group.check_barcode',
       return_value='{0}, {1}'.format('123456789\n ברקוד',
                                      TEXTS["product_status"]["kosher_template"].format(kashrut_type='kashrut_type',
                                                                                        cert='cert')
                                      )
       )
@patch('services.group.green_send_message', new_callable=AsyncMock)
@patch('services.group.is_night_hours', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_kosher_barcode(
        mock_check_barcode, mock_green_send_message, mock_is_night_hours, mock_duplicate_checker, redis_client):
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
    result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_duplicate_checker)
    assert result['status'] == 'group_listed'
    result2 = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_duplicate_checker)
    assert result2['status'] == 'group_duplicate_barcode_ignored'