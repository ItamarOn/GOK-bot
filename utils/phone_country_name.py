import phonenumbers
from phonenumbers import geocoder
from config import logger


def _get_flag_emoji(country_code):
    if not country_code: return ""
    # Converts 'IL' to 🇮🇱 using Unicode regional indicator symbols
    return "".join(chr(127397 + ord(c)) for c in country_code.upper())


def process_phone_number(raw_number):
    try:
        clean_number = raw_number if raw_number.startswith('+') else '+' + raw_number
        parsed_number = phonenumbers.parse(clean_number, None)
        country_name = geocoder.country_name_for_number(parsed_number, 'en')
        iso_code = phonenumbers.region_code_for_number(parsed_number)
        flag = _get_flag_emoji(iso_code)

        if country_name:
            if country_name.startswith("Israel"):
                return f"{raw_number} {flag}"
            return f"{raw_number} from {country_name} {flag}"
        else:
            logger.info(f"{raw_number} - country unknown")
            return f"{raw_number}"

    except Exception as e:
        logger.error(f"Error processing phone number {raw_number}: {e}")
        return f"{raw_number}"
