# test leading_zero_retry with barcode_data='0003'

import pytest
from unittest.mock import patch
from utils.texts import TEXTS
from core.engine import leading_zero_retry, ask_gok, check_barcode

@pytest.mark.parametrize("barcode_data, expected", [
    ('007', 2),
    ('0074880020021', 2),
    ('000080042563', 3),
    ('0123456789012', 1),
])
@patch('time.sleep', return_value=None)
@patch('core.engine.ask_gok', return_value=TEXTS['errors']['gok_not_found'])
def test_leading_zero_retry(mock_ask_gok, sleep_mock, barcode_data, expected):
    result = leading_zero_retry(barcode_data)
    assert mock_ask_gok.call_count == expected
    assert result.count('\n') == expected


@pytest.mark.parametrize("barcode_data, expected", [
    ('0003', 4),
    ('00000006756', 4),
    ('0123456789012', 2),
    ('123456789012', 1),
])
@patch('time.sleep', return_value=None)
@patch('core.engine.requests.post', return_value=type('obj', (object,), {'ok': True, 'json': lambda: [], 'raise_for_status': lambda: None}))
def test_ask_gok_with_leading_zero_retry(mock_post, sleep_mock, barcode_data, expected):
    result = ask_gok(barcode_data)
    assert mock_post.call_count == expected
    assert result.count('\n') == expected - 1