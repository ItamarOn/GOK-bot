import os
from dotenv import load_dotenv
import logging

env_location = 'local .env'
if os.path.exists(".env"):
    load_dotenv()
else:
    env_location = 'server environment variables'

logging.basicConfig(
    level=os.getenv("LOG_LEVEL"),  # or INFO
    format="%(asctime)s [%(levelname)s]: %(message)s",
)

logger = logging.getLogger("gok-bot")

logger.info(f"Loaded env vars from: {env_location}")

GOK_API_TOKEN = os.getenv("GOK_API_TOKEN")
WHITE_IP = os.getenv("WHITE_IP")

# # for Meta webhook verification
# VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
# ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
# PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# for green-api verification
GREEN_ID = os.getenv("GREEN_ID")
GREEN_TOKEN = os.getenv("GREEN_TOKEN")

# for Redis connection (duplicate checker)
REDIS_URL = os.getenv("REDIS_URL")

if not GREEN_ID or not GREEN_TOKEN or not GOK_API_TOKEN or not WHITE_IP:
    raise RuntimeError("Missing credentials — check .env or Render Environment settings.")
