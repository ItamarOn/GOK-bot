import requests
from PIL import Image
from pyzbar.pyzbar import decode
import io
from config import (
    logger,
    ACCOUNT_SID,
    AUTH_TOKEN,
    GOK_API_TOKEN,
    WHITE_IP,
)

def check_barcode(media_url: str, text=False) -> str:
    """
    get link to the pic (MediaUrl0 of Twilio)
    return the barcode data if found, else an error message
    """
    if text:
        logger.info(f"Barcode (text) detected: {media_url}")
        return f"barcode: {media_url}\n" + ask_gok(media_url)

    try:
        # get the picture from the URL
        response = requests.get(media_url, auth=(ACCOUNT_SID, AUTH_TOKEN))
        response.raise_for_status()

        image_bytes = io.BytesIO(response.content)
        image = Image.open(image_bytes)

        # decode the barcode
        barcodes = decode(image)
        if not barcodes:
            return "😲 לא נמצא ברקוד בתמונה"

        # first barcode
        barcode = barcodes[0]
        barcode_data = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        logger.info(f"Barcode ({barcode_type}) detected: {barcode_data}")
        if barcode_type != "EAN13":
            return "בתמונה מופיע ברקוד שאיננו נתמך, נא לשלוח תמונה בה יש ברקוד סטנדרטי בלבד"
        return f"barcode: {barcode_data}\n" + ask_gok(barcode_data)

    except Exception as e:
        logger.exception("error while reading BarCode")
        return "error while reading BarCode"

def ask_gok(barcode_data: str):
    url = "https://www.zekasher.com/api/v1/products"
    payload = {
        "queries": [
            {
                "barcode": f"{barcode_data}",
                # "status": 'מוצר מאושר ע"י הרב לשימוש במערכת'
            }
        ],
        "user-ip": WHITE_IP,
        # "button_id": ""
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
        if not product_info:
            logger.debug("Doesn't exist in GOK system")
            return "Doesn't exist in GOK system 😢"

        logger.debug(f"product_info[0]:\n{product_info[0]}\n")
        kashrut_type = product_info[0]['kashrutTypes'][0]
        if kashrut_type == "לא כשר":
            return "❌ לא כשר"
        logger.debug("Kosher")
        return f"✅ {kashrut_type} ✅" + product_info[0]['kashrutCerts'][0]
    except Exception as e:
        logger.exception("error while asking GOK, Try again later")
