import pytest
from unittest.mock import patch, Mock, MagicMock
from PIL import Image
import io

from core.engine import check_barcode
from utils.texts import TEXTS


@pytest.fixture
def mock_barcode_image():
    """Create a mock image with barcode data"""
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()


@pytest.fixture
def mock_barcode_object():
    """Create a mock barcode object from pyzbar"""
    barcode = Mock()
    barcode.data = b'7290000000000'
    barcode.type = 'EAN13'
    return barcode


class TestCheckBarcodeText:
    """Test check_barcode with text input"""

    @patch('core.engine.ask_gok')
    def test_check_barcode_text_input(self, mock_ask_gok):
        """Test barcode from text input"""
        mock_ask_gok.return_value = "Product\n✅ כשר"

        result = check_barcode('7290000000000', text=True)

        mock_ask_gok.assert_called_once_with('7290000000000')
        assert TEXTS["barcode"]["prefix"] in result
        assert '7290000000000' in result
        assert "✅ כשר" in result


class TestCheckBarcodeImage:
    """Test check_barcode with image URL"""

    @patch('core.engine.ask_gok')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_image_success(
            self,
            mock_requests,
            mock_decode,
            mock_ask_gok,
            mock_barcode_image,
            mock_barcode_object
    ):
        """Test successful barcode extraction from image"""
        # Mock requests.get
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Mock barcode decode
        mock_decode.return_value = [mock_barcode_object]

        # Mock GOK response
        mock_ask_gok.return_value = "Product Name\n✅ כשר פרווה"

        result = check_barcode('https://example.com/barcode.jpg')

        mock_requests.assert_called_once_with('https://example.com/barcode.jpg')
        assert mock_decode.call_count >= 1  # Called at least once (maybe twice with contrast)
        mock_ask_gok.assert_called_once_with('7290000000000')
        assert TEXTS["barcode"]["prefix"] in result
        assert '7290000000000' in result
        assert "✅ כשר" in result

    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_no_barcode_found(
            self,
            mock_requests,
            mock_decode,
            mock_barcode_image
    ):
        """Test when no barcode is detected in image"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # No barcodes found
        mock_decode.return_value = []

        result = check_barcode('https://example.com/image.jpg')

        assert result == TEXTS["errors"]["barcode_not_found"]
        assert mock_decode.call_count == 2  # Once normal, once with contrast

    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_unsupported_type(
            self,
            mock_requests,
            mock_decode,
            mock_barcode_image
    ):
        """Test when barcode type is not EAN13/EAN8"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # QR code instead of EAN
        barcode = Mock()
        barcode.data = b'https://example.com'
        barcode.type = 'QRCODE'
        mock_decode.return_value = [barcode]

        result = check_barcode('https://example.com/qr.jpg')

        assert result == TEXTS["errors"]["unsupported_barcode"]

    @patch('core.engine.ask_gok')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_multiple_barcodes(
            self,
            mock_requests,
            mock_decode,
            mock_ask_gok,
            mock_barcode_image
    ):
        """Test when multiple barcodes are detected"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # Two EAN barcodes
        barcode1 = Mock()
        barcode1.data = b'7290000000000'
        barcode1.type = 'EAN13'

        barcode2 = Mock()
        barcode2.data = b'7290111111111'
        barcode2.type = 'EAN13'

        mock_decode.return_value = [barcode1, barcode2]

        result = check_barcode('https://example.com/double.jpg')

        assert result == TEXTS["errors"]["image_processing"]
        mock_ask_gok.assert_not_called()

    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_network_error(
            self,
            mock_requests,
            mock_decode
    ):
        """Test network error when fetching image"""
        mock_requests.side_effect = Exception("Network error")

        result = check_barcode('https://example.com/barcode.jpg')

        assert result == TEXTS["errors"]["exception"]
        mock_decode.assert_not_called()

    @patch('core.engine.ask_gok')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_ean8(
            self,
            mock_requests,
            mock_decode,
            mock_ask_gok,
            mock_barcode_image
    ):
        """Test EAN8 barcode (should be supported)"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        barcode = Mock()
        barcode.data = b'12345678'
        barcode.type = 'EAN8'
        mock_decode.return_value = [barcode]

        mock_ask_gok.return_value = "Product\n✅ כשר"

        result = check_barcode('https://example.com/ean8.jpg')

        mock_ask_gok.assert_called_once_with('12345678')
        assert TEXTS["barcode"]["prefix"] in result

    @patch('core.engine.ask_gok')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_with_non_ean_and_ean(
            self,
            mock_requests,
            mock_decode,
            mock_ask_gok,
            mock_barcode_image
    ):
        """Test mixed barcodes - should ignore non-EAN and use EAN"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        qr = Mock()
        qr.type = 'QRCODE'
        qr.data = b'https://example.com'

        ean = Mock()
        ean.type = 'EAN13'
        ean.data = b'7290000000000'

        mock_decode.return_value = [qr, ean]
        mock_ask_gok.return_value = "Product\n✅ כשר"

        result = check_barcode('https://example.com/mixed.jpg')

        mock_ask_gok.assert_called_once_with('7290000000000')
        assert "✅" in result


class TestCheckBarcodeWithContrastEnhancement:
    """Test contrast enhancement fallback"""

    @patch('core.engine.ask_gok')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_barcode_found_after_contrast_enhancement(
            self,
            mock_requests,
            mock_decode,
            mock_ask_gok,
            mock_barcode_image,
            mock_barcode_object
    ):
        """Test barcode found only after contrast enhancement"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        # First call returns empty, second call returns barcode
        mock_decode.side_effect = [[], [mock_barcode_object]]
        mock_ask_gok.return_value = "Product\n✅ כשר"

        result = check_barcode('https://example.com/low_contrast.jpg')

        assert mock_decode.call_count == 2
        mock_ask_gok.assert_called_once_with('7290000000000')
        assert "✅" in result


class TestCheckBarcodeWithLeadingZeros:
    """Test check_barcode with barcodes that have leading zeros"""

    @patch('time.sleep', return_value=None)
    @patch('core.engine.requests.post')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_leading_zeros_not_found_then_retry(
            self,
            mock_get,
            mock_decode,
            mock_post,
            mock_sleep,
            mock_barcode_image
    ):
        """Test barcode with leading zeros triggers retry mechanism"""
        # Mock image download
        mock_response_get = Mock()
        mock_response_get.content = mock_barcode_image
        mock_response_get.raise_for_status = Mock()
        mock_get.return_value = mock_response_get

        # Mock barcode detection - barcode starts with zeros
        barcode = Mock()
        barcode.data = b'0007290000000'
        barcode.type = 'EAN13'
        mock_decode.return_value = [barcode]

        # Mock GOK API responses - need to create new Mock for each call
        def create_post_response(json_data):
            resp = Mock()
            resp.raise_for_status = Mock()
            resp.json = Mock(return_value=json_data)
            resp.ok = True
            return resp

        # 1st call (0007290000000) - empty (not found)
        # 2nd call (007290000000) - empty (not found)
        # 3rd call (07290000000) - found!
        mock_post.side_effect = [
            create_post_response([]),
            create_post_response([]),
            create_post_response([{
                'name': 'Test Product',
                'status': 'מוצר מאושר ע"י הרב לשימוש במערכת',
                'kashrutTypes': ['כשר חלבי'],
                'kashrutCerts': ['GOK']
            }])
        ]

        result = check_barcode('https://example.com/barcode.jpg')

        # Verify ask_gok was called 3 times (original + 2 retries)
        assert mock_post.call_count == 3

        # Verify sleep was called 2 times (between retries)
        assert mock_sleep.call_count == 2

        # Verify successful result
        assert 'Test Product' in result
        assert '✅' in result
        assert 'כשר חלבי' in result

    @patch('time.sleep', return_value=None)
    @patch('core.engine.requests.post')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_leading_zeros_all_not_found(
            self,
            mock_get,
            mock_decode,
            mock_post,
            mock_sleep,
            mock_barcode_image
    ):
        """Test barcode with leading zeros - all retries fail"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        barcode = Mock()
        barcode.data = b'000123456'
        barcode.type = 'EAN13'
        mock_decode.return_value = [barcode]

        # All GOK API calls return empty
        def create_empty_response():
            resp = Mock()
            resp.raise_for_status = Mock()
            resp.json = Mock(return_value=[])
            resp.ok = True
            return resp

        mock_post.side_effect = [create_empty_response() for _ in range(4)]

        result = check_barcode('https://example.com/barcode.jpg')

        # Should try: 000123456, 00123456, 0123456 = 3 calls
        assert mock_post.call_count == 3
        assert TEXTS["errors"]["gok_not_found"] in result
        # Should list all attempted barcodes
        assert '00123456' in result
        assert '0123456' in result
        assert '123456' in result

    @patch('time.sleep', return_value=None)
    @patch('core.engine.requests.post')
    @patch('core.engine.decode')
    @patch('core.engine.requests.get')
    def test_check_barcode_leading_zero_found_on_second_try(
            self,
            mock_get,
            mock_decode,
            mock_post,
            mock_sleep,
            mock_barcode_image
    ):
        """Test barcode found after removing one leading zero"""
        mock_response = Mock()
        mock_response.content = mock_barcode_image
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        barcode = Mock()
        barcode.data = b'00729000'
        barcode.type = 'EAN8'
        mock_decode.return_value = [barcode]

        def create_post_response(json_data):
            resp = Mock()
            resp.raise_for_status = Mock()
            resp.json = Mock(return_value=json_data)
            resp.ok = True
            return resp

        mock_post.side_effect = [
            create_post_response([]),  # 00729000 - not found
            create_post_response([{  # 0729000 - found!
                'name': 'Mega Gluflex Choclate 100g',
                'status': 'מוצר מאושר ע"י הרב לשימוש במערכת',
                'kashrutTypes': ['חלבי'],
                'kashrutCerts': ['OU']
            }])
        ]

        result = check_barcode('https://example.com/barcode.jpg')

        # Only 2 calls - original failed, first retry succeeded
        assert mock_post.call_count == 2
        assert 'Mega Gluflex Choclate 100g' in result
        assert 'חלבי' in result

    @patch('core.engine.ask_gok')
    def test_check_barcode_text_with_leading_zeros(self, mock_ask_gok):
        """Test text input with leading zeros"""
        mock_ask_gok.return_value = "Product\n✅ כשר"

        result = check_barcode('0001234567890', text=True)

        # ask_gok should be called with the original barcode
        mock_ask_gok.assert_called_once_with('0001234567890')
        assert '0001234567890' in result
