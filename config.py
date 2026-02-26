import os
import redis
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import logging
from urllib.parse import urlparse

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
tz_info = ZoneInfo("Asia/Jerusalem")

logger.info(f"Loaded env vars from: {env_location}. Timezone set to {tz_info}")




# Get Upstash Redis connection from environment variable
UPSTASH_REDIS_URL = os.getenv('UPSTASH_REDIS_URL')

if not UPSTASH_REDIS_URL:
    raise ValueError("UPSTASH_REDIS_URL environment variable not set!")

# Parse the connection string
redis_url = urlparse(UPSTASH_REDIS_URL)

# Create Redis client
redis_client = redis.Redis(
    host=redis_url.hostname,
    port=redis_url.port,
    password=redis_url.password,
    ssl=True,  # Upstash requires SSL
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
    health_check_interval=30
)

# Test connection
try:
    redis_client.ping()
    print("✅ Redis connected successfully!")
except Exception as e:
    print(f"❌ Redis connection error: {e}")
    # Don't raise - let it fail gracefully on first request







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
