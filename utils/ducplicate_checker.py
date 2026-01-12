import redis.asyncio as redis
from config import logger, REDIS_URL
import inspect


class DuplicateChecker:
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

    async def _maybe_await(self, value):
        """Await value if it's awaitable, otherwise return it directly.

        This allows using both sync fakeredis (used in tests) and async redis clients.
        """
        if inspect.isawaitable(value):
            return await value
        return value

    async def is_duplicate(self, topic, identifier: str, ttl_seconds: int = 86400) -> bool:
        """
        Generic duplicate check for any topic and identifier.
        Returns True if identifier already processed (within TTL).
        Uses an atomic SET NX with expiration
        """
        if not self.client:
            logger.debug("restarting Redis connection for duplicate check")
            await self.connect()

        key = f"{topic}:{identifier}"
        # SET NX - set only if not exist - returns True if set, False otherwise
        was_set = self.client.set(key, "1", ex=ttl_seconds, nx=True)
        was_set = await self._maybe_await(was_set)
        if not was_set:
            logger.debug(f"Duplicate detected for {topic}: {identifier}")
            return True

        return False


    async def ping(self) -> bool:
        """Simple health check"""
        try:
            pong = self.client.ping()
            pong = await self._maybe_await(pong)
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
        msgs_on_last_24h = self.client.dbsize()
        msgs_on_last_24h = await self._maybe_await(msgs_on_last_24h)
        logger.info(f"Number of keys in Redis: {msgs_on_last_24h}")
        return msgs_on_last_24h
