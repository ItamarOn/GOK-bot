# tests for the logic of GOK-bot/services/group.py

import pytest
import fakeredis
from unittest.mock import patch

from services.group import group_handler
from utils.texts import TEXTS
from utils.redis_manager import RedisManager

from examples import group_pic_example, group_text_example

# make fixture for all tests in this file
@pytest.fixture(autouse=True)
def mock_redis_manager():
    fake_client = fakeredis.aioredis.FakeRedis()
    rm = RedisManager()
    rm.client = fake_client
    with patch('services.group.db', rm):
        yield fake_client

# duplicate call at nighttime
@patch('services.group.is_too_old', return_value=False)
@patch('services.group.is_night_hours', return_value=True)
@patch('services.group.green_send_message')
@pytest.mark.asyncio
async def test_group_handler_night_duplicate(
        mock_green_send_message,
        mock_is_night_hours,
        mock_is_too_old,
        mock_redis_manager
):
    whatsapp_request = group_pic_example.copy()
    whatsapp_request_later = group_pic_example.copy()
    whatsapp_request_later_later = group_pic_example.copy()
    whatsapp_request['timestamp'] = 1000000000
    whatsapp_request_later['timestamp'] = 1000000001
    whatsapp_request_later['idMessage'] = 'some_ID_ACG65TR4345342'
    whatsapp_request_later_later['timestamp'] = 1000000002
    whatsapp_request_later_later['idMessage'] = 'some_ID2_F545454545411'

    # result = await group_handler(sender_data, msg_data, msg_type, msg_id, timestamp, mock_redis_manager)
    result = await group_handler(whatsapp_request)
    assert result['status'] == 'group_outside_hours'
    result2 = await group_handler(whatsapp_request_later)
    assert result2['status'] == 'group_outside_hours_many_messages'
    result3 = await group_handler(whatsapp_request_later_later)
    assert result3['status'] == 'group_outside_hours_many_messages'

    assert mock_is_night_hours.call_count == 3

    redis_values = await mock_redis_manager.execute_command('KEYS', '*')
    assert redis_values == [
        b'dup:msg-g:AC584E061E32C650FDE0817A965D54D6',
        f"dup:night:{whatsapp_request['senderData']['chatId']}".encode("utf-8"),
        b'dup:msg-g:some_ID_ACG65TR4345342',
        b'dup:msg-g:some_ID2_F545454545411'
    ]


# image with no barcode
@patch('services.group.check_barcode', return_value=TEXTS["errors"]["barcode_not_found"])
@patch('services.group.green_send_message')
@patch('services.group.is_night_hours', return_value=False)
@patch('services.group.is_too_old', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_no_barcode(
        mock_check_barcode,
        mock_green_send_message,
        mock_is_night_hours,
        mock_is_too_old,
        mock_redis_manager
):
    result = await group_handler(group_pic_example)
    assert result["status"] == "group_image_ignored"


# image with barcode that not found
@patch('services.group.check_barcode',
       return_value='{0}, {1}'.format('123456789\n ברקוד', TEXTS["errors"]["gok_not_found"]))
@patch('services.group.green_send_message')
@patch('services.group.is_night_hours', return_value=False)
@patch('services.group.is_too_old', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_barcode_not_found(
        mock_check_barcode,
        mock_green_send_message,
        mock_is_night_hours,
        mock_is_too_old,
        mock_redis_manager
):
    group_pic_example2 = group_pic_example.copy()
    group_pic_example2['idMessage'] = 'some_other_id_12345'

    result = await group_handler(group_pic_example)
    assert result['status'] == 'group_unlisted'
    result2 = await group_handler(group_pic_example2)
    assert result2['status'] == 'group_duplicate_barcode_ignored'

    redis_values = await mock_redis_manager.execute_command('KEYS', '*')
    assert redis_values == [
        b'dup:msg-g:AC584E061E32C650FDE0817A965D54D6',
        b'dup:barcode:123456789',
        b'dup:msg-g:some_other_id_12345'
    ]


# image with kosher barcode - 3 statuses should mark as listed: not_kosher, unknown, kosher_template
@pytest.mark.parametrize("gok_result", [
    TEXTS["product_status"]["not_kosher"],
    TEXTS["product_status"]["unknown"],
    TEXTS["product_status"]["kosher_template"].format(kashrut_type='kashrut_type', cert='cert'),
])
@patch('services.group.check_barcode')
@patch('services.group.green_send_message')
@patch('services.group.is_night_hours', return_value=False)
@patch('services.group.is_too_old', return_value=False)
@pytest.mark.asyncio
async def test_group_handler_kosher_barcode(
        #mock_redis_manager,
        mock_is_too_old,
        mock_is_night_hours,
        mock_green_send_message,
        mock_check_barcode,
        gok_result,
):
    mock_check_barcode.return_value = '123456789\n ברקוד {}'.format(gok_result)
    group_pic_example2 = group_pic_example.copy()
    group_pic_example2['idMessage'] = 'some_other_id_67890'
    result = await group_handler(group_pic_example)
    assert result['status'] == 'group_listed'
    result2 = await group_handler(group_pic_example2)
    assert result2['status'] == 'group_duplicate_barcode_ignored'
