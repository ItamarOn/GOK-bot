# test leading_zero_retry with barcode_data='0003'

import pytest
from unittest.mock import patch
from utils.texts import TEXTS
from core.engine import ask_gok


@pytest.mark.parametrize("barcode_data, expected", [
    ('0003', 3),
    ('00000006756', 7),
    ('0123456789012', 1),
    ('123456789012', 0),
])
@patch('time.sleep', return_value=None)
@patch('core.engine.requests.post', return_value=type('obj', (object,), {'ok': True, 'json': lambda: [], 'raise_for_status': lambda: None}))
def test_ask_gok_with_leading_zero_retry(mock_post, sleep_mock, barcode_data, expected):
    result = ask_gok(barcode_data)
    assert mock_post.call_count == 1
    assert result.count('\n') == expected
