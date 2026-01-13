import redis.asyncio as redis
from config import logger, REDIS_URL


class RedisManager:
    def __init__(self):
        self.redis_url = REDIS_URL
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

    async def _ensure_connection(self):
        if not self.client:
            logger.debug("restarting Redis connection")
            await self.connect()

    async def is_duplicate(self, topic, identifier: str, ttl_seconds: int = 86400) -> bool:
        """
        Generic duplicate check for any topic and identifier.
        Returns True if identifier already processed (within TTL).
        Uses an atomic SET NX with expiration
        """
        await self._ensure_connection()

        key = f"dup:{topic}:{identifier}"
        # SET NX - set only if not exist - returns True if set, False otherwise
        was_set = await self.client.set(key, "1", ex=ttl_seconds, nx=True)
        if not was_set:
            logger.debug(f"Duplicate detected for {key}")
            return True
        return False

    async def increment_counter(self, name: str, amount: int = 1) -> int:
        """ Increments a named counter by the specified amount """
        await self._ensure_connection()
        key = f"co:{name}"
        new_value = await self.client.incrby(key, amount)
        return new_value

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
        await self._ensure_connection()
        msgs_on_last_24h = await self.client.dbsize()
        logger.info(f"Number of keys in Redis: {msgs_on_last_24h}")
        return msgs_on_last_24h


db = RedisManager()  # Singleton instance
