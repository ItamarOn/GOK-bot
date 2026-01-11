import redis.asyncio as redis
from config import logger, REDIS_URL


class DuplicateChecker:
    def __init__(self, ttl_seconds: int = 86400):
        """
        Handles duplicate message prevention using Redis.
        Uses `REDIS_URL` from `config.py` as the Redis connection string.
        :param ttl_seconds: Expiration time for message IDs (default: 24 hours)
        """
        self.redis_url = REDIS_URL
        self.ttl = ttl_seconds
        self.client = None

    async def connect(self):
        """Establish connection to Redis once (called on startup)"""
        try:
            if not self.client:
                self.client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {self.redis_url}")
            raise

    async def is_duplicate(self, message_id: str) -> bool:
        """
        Returns True if message_id already processed (within TTL)
        """
        if not self.client:
            logger.debug("restarting Redis connection for duplicate check")
            await self.connect()

        exists = await self.client.exists(message_id)
        if exists:
            logger.debug(f"Duplicate detected: {message_id}")
            return True

        # Mark as seen
        await self.client.set(message_id, "1", ex=self.ttl)
        return False

    async def is_duplicate_sender(self, sender_id: str, ttl_seconds: int = 30) -> bool:
        """
        Returns True if `sender_id` has recently sent a message (within ttl_seconds).
        Uses a separate Redis key namespace `sender:{sender_id}` to avoid colliding with message IDs.
        This method uses an atomic SET NX to avoid race conditions.
        """
        if not self.client:
            logger.debug("restarting Redis connection for sender duplicate check")
            await self.connect()

        key = f"sender:{sender_id}"
        try:
            # SET NX will only set the key if it does not exist; returns True if set, False otherwise
            was_set = await self.client.set(key, "1", ex=ttl_seconds, nx=True)
            if not was_set:
                logger.debug(f"Duplicate sender detected: {sender_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking sender duplicate for {sender_id}: {e}")
            # On Redis error, conservative approach: don't treat as duplicate to avoid dropping messages
            return False

    async def ping(self) -> bool:
        """Simple health check"""
        try:
            pong = await self.client.ping()
            return pong
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def count_keys(self) -> int:
        """
        Returns the number of keys in the current Redis DB.
        Note: expired keys are removed lazily; count is approximate in edge cases.
        """
        if not self.client:
            logger.debug("restarting Redis connection for key count")
            await self.connect()
        msgs_on_last_24h = await self.client.dbsize()
        logger.info(f"Number of keys in Redis: {msgs_on_last_24h}")
        return msgs_on_last_24h