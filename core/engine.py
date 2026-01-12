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
from utils.texts import TEXTS, GOK_STATUS

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
            TEXTS["barcode"]["prefix"]
            + f"{media_url}\n"
            + ask_gok(media_url)
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
        barcode_data = align_to_gok_format(barcode_data, barcode_type)
        logger.info(f"Barcode ({barcode_type}) detected: {barcode_data}")

        return (
            TEXTS["barcode"]["prefix"]
            + f"{barcode_data}\n"
            + ask_gok(barcode_data)
        )

    except Exception as e:
        logger.exception("error while reading BarCode")
        return TEXTS["errors"]["exception"]


def ask_gok(barcode_data: str, retry_seconds=0):
    url = "https://www.zekasher.com/api/v1/products"
    payload = {
        "queries": [
            {
                "barcode": f"{barcode_data}",
            }
        ],
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
        product_info = response.json()
    except Exception as e:
        if retry_seconds == 0:
            sleep_time = random.randint(9, 25)
            logger.debug(f"retrying after {sleep_time} seconds. due to exception: {e}")
            time.sleep(sleep_time)
            return ask_gok(barcode_data, retry_seconds=sleep_time)
        else:
            logger.debug(f"request: {url} payload: {payload}")
            logger.exception("Cannot get basic response from GOK")
            return TEXTS["errors"]["gok_server_error"]

    if not product_info:
        logger.debug("Doesn't exist in GOK system")
        return TEXTS["errors"]["gok_not_found"]

    try:
        logger.debug(f'retry after {retry_seconds} seconds') if retry_seconds else None
        logger.debug(f"product_info[0]:\n{product_info[0]}\n")

        product_name = html.unescape(product_info[0].get('name', '')) + '\n'
        status = product_info[0]['status']

        if status != GOK_STATUS['confirmed']:
            logger.debug(f"Product status: {status}")
            return product_name + TEXTS["product_status"]["in_review"]

        kashrut_type = product_info[0]['kashrutTypes'][0]
        if kashrut_type == GOK_STATUS['not_kosher']:
            return product_name + TEXTS["product_status"]["not_kosher"]

        logger.debug("Kosher")
        cert = product_info[0]['kashrutCerts'][0] if product_info[0]['kashrutCerts'] else ''
        return product_name + TEXTS["product_status"]["kosher_template"].format(
            kashrut_type=kashrut_type,
            cert=cert,
        )

    except Exception as e:
        logger.debug(f"request: {url} payload: {payload}")
        logger.debug(f"response: {response.json()}")
        logger.exception("200 OK for asking GOK, But error for parsing")
        return TEXTS["errors"]["internal_logic_error"]


def align_to_gok_format(barcode_data: str, barcode_type: str) -> str:
    """
    GTIN-13 format include EAN-13 and UPC-A. by add leading '0' to UPC-A.
    to align with GOK system we must remove this leading '0' for EAN-13.
    """
    if barcode_type == "EAN13" and len(barcode_data) == 13 and barcode_data.startswith('0') :
        return barcode_data[1:]  # Remove leading '0'
    return barcode_data