import io
import html
import time
import random
import requests
from PIL import Image, ImageEnhance
from pyzbar.pyzbar import decode

from config import (
    logger,
    GOK_API_TOKEN,
    WHITE_IP,
)
from utils.texts import TEXTS, GOK_STATUS, LISTED_SIGNS

FOOD_BARCODES = {"EAN13", "EAN8"}  # UPC-A is normalized to GTIN-13 by adding a leading '0' (GS1 standard).

def extract_barcode_from_image(image: Image) -> list:
    barcodes = decode(image)
    if barcodes:
        return barcodes

    enhancer = ImageEnhance.Contrast(image)
    contrast_image = enhancer.enhance(10)
    return decode(contrast_image)


def check_barcode(media_url: str, text=False) -> str:
    """
    Check barcode from image URL or text input.
    return response string.
    """
    if text:
        logger.info(f"Barcode (text) detected: {media_url}")
        return (
            TEXTS["barcode"]["prefix"] + f"{media_url}\n"
            + ask_gok([media_url])
        )

    try:
        response = requests.get(media_url)
        response.raise_for_status()

        image_bytes = io.BytesIO(response.content)
        image = Image.open(image_bytes)

        barcodes = extract_barcode_from_image(image)

        if not barcodes:
            return TEXTS["errors"]["barcode_not_found"]

        # only EAN** is supported
        food_barcodes = [b for b in barcodes if b.type in FOOD_BARCODES]
        if not food_barcodes:
            logger.debug(f"Not EAN barcodes found: {barcodes}")
            return TEXTS["errors"]["unsupported_barcode"]

        if len(food_barcodes) > 1:
            logger.info(f"{len(food_barcodes)} detected barcodes: {food_barcodes}")
            return TEXTS["errors"]["image_processing"]

        barcode = food_barcodes[0]
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        logger.info(f"Barcode ({barcode_type}) detected: {barcode_data}")

        return (
            TEXTS["barcode"]["prefix"] + f"{barcode_data}\n"
            + ask_gok([barcode_data])
        )

    except Exception as e:
        logger.exception("error while reading BarCode")
        return TEXTS["errors"]["exception"]


def ask_gok(barcode_data: list[str], retry_seconds=0):
    url = "https://www.zekasher.com/api/v1/products"
    queries = barcodes_to_queries(barcode_data)
    payload = {
        "queries": queries,
        "user-ip": WHITE_IP,
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": GOK_API_TOKEN,
        "Origin": "https://kosher.global",
        "Referer": "https://kosher.global/"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        products_info = response.json()
    except Exception as e:
        if retry_seconds == 0:
            return smart_retry(barcode_data, e)
        else:
            logger.debug(f"request: {url} payload: {payload}")
            logger.exception("Cannot get basic response from GOK")
            return TEXTS["errors"]["gok_server_error"]

    logger.debug(f"request: {url} payload: {payload}")
    return process_gok_response(barcode_data, products_info, retry_seconds == 0)


def barcodes_to_queries(barcode_data):
    if not barcode_data:
        return []

    if not barcode_data[0].startswith('0') or len(barcode_data) > 1:
        return [{"barcode": str(b)} for b in barcode_data]

    barcode = barcode_data[0]
    barcodes_to_check = [barcode, ]
    for i in range(1, len(barcode)):
        if len(barcode) < i or barcode[i - 1] != '0':
            break
        barcodes_to_check.append(barcode[i:])
    return [{"barcode": str(b)} for b in barcodes_to_check]



def process_gok_response(barcode_data: list[str], products_info: list[dict], is_first_run) -> str:
    logger.debug(f'products_info={products_info} is_first_run={is_first_run}')

    if not products_info:
        logger.debug(f"{barcode_data} Doesn't exist in GOK system")
        if len(barcode_data) > 1:
            printed_results = "\n".join(barcode_data)
            return f'{printed_results}\n' + TEXTS["errors"]["gok_not_found"]
        return TEXTS["errors"]["gok_not_found"]

    try:
        info = products_info[0]

        if len(products_info) > 1:
            for confirm_product in products_info:
                if confirm_product.get('status') == GOK_STATUS['confirmed']:
                    info = confirm_product
                    break

        product_name = html.unescape(info.get('name', '')) + '\n'
        status = info['status']

        if status != GOK_STATUS['confirmed'] or not info.get('kashrutTypes'):
            logger.debug(f"Product status: {status}")
            return product_name + TEXTS["product_status"]["in_review"]

        kashrut_type = info['kashrutTypes'][0]
        if kashrut_type == GOK_STATUS['not_kosher']:
            return product_name + TEXTS["product_status"]["not_kosher"]

        if kashrut_type == GOK_STATUS['unknown']:
            return product_name + TEXTS["product_status"]["unknown"]

        logger.debug("Kosher")
        cert = info['kashrutCerts'][0] if info['kashrutCerts'] else ''
        return product_name + TEXTS["product_status"]["kosher_template"].format(
            kashrut_type=kashrut_type,
            cert=cert,
        )

    except Exception as e:
        logger.debug(f"response: {products_info}")
        logger.exception("200 OK for asking GOK, But error for parsing")
        return TEXTS["errors"]["internal_logic_error"]


def smart_retry(barcodes: list[str], e):
    sleep_time = random.randint(6, 12)
    logger.debug(f"retrying after {sleep_time} seconds. due to exception: {e}")
    time.sleep(sleep_time)
    return ask_gok(barcodes, retry_seconds=sleep_time)


def leading_zero_retry(barcode_data: str) -> str:
    """
    Retry GOK query by removing leading zeros (up to 3)
    GTIN-13 format include EAN-13 and UPC-A. by add leading '0' to UPC-A.
    to align with GOK system we must remove this leading '0' for EAN-13.
    """
    barcodes_to_check = []
    results = {}
    for i in range(1, 4):
        if len(barcode_data) < i or barcode_data[i-1] != '0':
            break
        barcodes_to_check.append(barcode_data[i:])

    time.sleep(6)
    result = ask_gok(barcodes_to_check, 1)
    if any(sign in result for sign in LISTED_SIGNS):
        return TEXTS['barcode']['edited'] + modified_barcode + '\n' + result
    results[modified_barcode] = result
    logger.info(f'No results after leading zero retries: {results}')
    printed_results = "\n".join(results.keys())
    return f'{printed_results}\n' + TEXTS["errors"]["gok_not_found"]