import os
import sys
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import logging

env_location = 'local .env'
if os.path.exists(".env"):
    load_dotenv()
else:
    env_location = 'server environment variables'

log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# 3. Use force=True to override AWS Lambda's default configuration
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    stream=sys.stdout,
    force=True  # <--- THIS IS THE KEY FOR LAMBDA
)

logger = logging.getLogger("gok-bot")

# Optional: Ensure the child logger level is also explicitly set
logger.setLevel(log_level)


tz_info = ZoneInfo("Asia/Jerusalem")

logger.info(f"Loaded env vars from: {env_location}. Timezone set to {tz_info}. log: {log_level}")

# Get Upstash Redis connection from environment variable
UPSTASH_REDIS_REST_URL = os.getenv('UPSTASH_REDIS_REST_URL')
UPSTASH_REDIS_REST_TOKEN = os.getenv('UPSTASH_REDIS_REST_TOKEN')

if not UPSTASH_REDIS_REST_TOKEN:
    raise ValueError("UPSTASH_REDIS_REST_TOKEN environment variable not set! AWS Lambda requires this for Redis connection.")


GOK_API_TOKEN = os.getenv("GOK_API_TOKEN")
WHITE_IP = os.getenv("WHITE_IP")

# # for Meta webhook verification
# VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
# ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
# PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# for green-api verification
GREEN_ID = os.getenv("GREEN_ID")
GREEN_TOKEN = os.getenv("GREEN_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
REPORTS_CHAT_ID = os.getenv("REPORTS_CHAT_ID")
ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")
# for Redis connection
REDIS_URL = os.getenv("REDIS_URL")
ADMIN_SECRET_TOKEN = os.getenv("ADMIN_SECRET_TOKEN")

#  Working hours, no env-vars, using defaults
WORKING_HOURS = os.getenv("WORKING_HOURS", "7,22")  # 7 AM to 10 PM
MATES = set(phone.strip() for phone in os.getenv('MATES', '').split(','))

RENDER_GIT_COMMIT = os.getenv("RENDER_GIT_COMMIT", "unknown/dev")
APP_GIT_SHA = os.getenv("APP_GIT_SHA", "unknown/dev")

SERVER_PROVIDER = "local"
if os.getenv("FLY_APP_NAME") or os.getenv("FLY_MACHINE_ID"):
    SERVER_PROVIDER = "fly"
if os.getenv("RENDER_GIT_COMMIT") or os.getenv("RENDER"):
    SERVER_PROVIDER = "render"


if not GREEN_ID or not GREEN_TOKEN or not GOK_API_TOKEN or not WHITE_IP:
    raise RuntimeError("Missing credentials — check .env or Render Environment settings.")
