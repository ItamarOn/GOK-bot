import os
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=os.getenv("LOG_LEVEL"),  # or INFO
    format="%(asctime)s [%(levelname)s]: %(message)s",
)

logger = logging.getLogger("gok-bot")

if os.path.exists(".env"):
    load_dotenv()
    logger.info("Loaded local .env")
else:
    logger.info("Using server environment variables")


ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
GOK_API_TOKEN = os.getenv("GOK_API_TOKEN")
WHITE_IP = os.getenv("WHITE_IP")


if not ACCOUNT_SID or not AUTH_TOKEN or not GOK_API_TOKEN or not WHITE_IP:
    raise RuntimeError("Missing Twilio credentials — check .env or Render Environment settings.")
