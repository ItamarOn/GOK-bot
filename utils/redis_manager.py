from typing import Tuple, Optional

from datetime import datetime, timedelta
import redis.asyncio as redis
import redis as redis_sync
from config import logger, REDIS_URL


class RedisManager:
    def __init__(self):
        self.redis_url = REDIS_URL
        self.client = None
        self.sync_client = None

    async def connect(self):
        """Establish connection to Redis once (called on startup)"""
        try:
            if not self.client:
                self.client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                self.sync_client = redis_sync.from_url(self.redis_url, decode_responses=True)
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
            logger.info(f"Duplicate detected for {key}")
            return True
        return False

    async def is_n_duplicate(self, identifier: str, ttl_seconds: int = 86400, n: int = 3) -> bool:
        """Checks if an identifier has been seen more than n times within TTL."""
        await self._ensure_connection()
        key = f"dup-n:{identifier}"
        new_value = await self.client.incr(key)
        if new_value == 1:
            await self.client.expire(key, ttl_seconds)
        if new_value > n:
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

    async def count_keys(self, match: str = '*') -> int:
        """ Returns the number of keys in the current Redis DB """
        await self._ensure_connection()
        if match == '*':
            count = await self.client.dbsize()
        else:
            count = 0
            async for _ in self.client.scan_iter(match=match):
                count += 1
        logger.debug(f"Number of {match} keys in Redis: {count}")
        return count

    async def sync_app_version(self, cur_version: str) -> Tuple[bool, Optional[str]]:
        """
        Stores current_version in Redis only if different.
        """
        await self._ensure_connection()
        key = 'app:version'
        previous = await self.client.get(key)

        if previous == cur_version:
            return False, cur_version

        await self.client.set(key, cur_version)
        logger.info(f"App version updated in Redis: {cur_version} (was: {previous})")
        return True, cur_version

    @staticmethod
    def _get_current_week_key() -> str:
        """Get the current week key based on Sunday as start of week"""
        today = datetime.now()
        days_since_sunday = (today.weekday() + 1) % 7
        start_of_week = today - timedelta(days=days_since_sunday)
        return start_of_week.strftime("%d/%m")

    def track_received_message(self, is_group: bool, is_admin: bool) -> None:
        """Track incoming message statistics"""
        try:
            week_key = self._get_current_week_key()
            message_type = "group" if is_group else "private"
            message_type += ":admin" if is_admin else ""
            redis_key = f"stats:{week_key}:received:{message_type}"

            incrementer = self.sync_client.incr(redis_key)
            if incrementer == 1:
                self.sync_client.expire(redis_key, 1209600) # 14 days in seconds

        except Exception as e:
            logger.info(f"Failed to track received message: {e}")

    def track_sent_message(self, is_group: bool) -> None:
        """Track outgoing message statistics"""
        try:
            week_key = self._get_current_week_key()
            message_type = "group" if is_group else "private"
            redis_key = f"stats:{week_key}:sent:{message_type}"

            incrementer = self.sync_client.incr(redis_key)
            if incrementer == 1:
                self.sync_client.expire(redis_key, 1209600)

        except Exception as e:
            logger.info(f"Failed to track sent message: {e}")

    def get_weekly_stats(self, week_offset: int = 0) -> dict:
        """
        Get statistics for a specific week (Sunday to Saturday)

        Args:
            week_offset: 0 for current week, 1 for last week (max 1 for free tier)

        Returns:
            Dictionary with received and sent message counts
        """
        try:
            today = datetime.now()

            # Calculate target date based on offset
            target_date = today - timedelta(weeks=week_offset)

            # Find the Sunday of that week
            days_since_sunday = (target_date.weekday() + 1) % 7
            start_of_week = target_date - timedelta(days=days_since_sunday)

            week_key = start_of_week.strftime("%d/%m")

            return {
                "week_start": week_key,
                "received": {
                    "group": int(self.sync_client.get(f"stats:{week_key}:received:group") or 0),
                    "private": int(self.sync_client.get(f"stats:{week_key}:received:private") or 0),
                    "admin": int(self.sync_client.get(f"stats:{week_key}:received:group:admin") or 0)
                },
                "sent": {
                    "group": int(self.sync_client.get(f"stats:{week_key}:sent:group") or 0),
                    "private": int(self.sync_client.get(f"stats:{week_key}:sent:private") or 0)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get weekly stats: {e}")
            return {
                "week_start": "error",
                "week_start_full": "error",
                "received": {"group": 0, "private": 0},
                "sent": {"group": 0, "private": 0}
            }


db = RedisManager()  # Singleton instance
