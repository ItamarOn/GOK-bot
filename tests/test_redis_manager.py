import pytest
from utils.redis_manager import RedisManager
import fakeredis
import asyncio


@pytest.fixture
def redis_client():
    return fakeredis.aioredis.FakeRedis()


@pytest.mark.asyncio
async def test_duplicate_checker(redis_client):
    db = RedisManager()
    db.client = redis_client
    topic = "some_fake"
    identifier = "12345"
    # First check should return False (not duplicate)
    is_dup = await db.is_duplicate(topic, identifier, ttl_seconds=1)
    assert is_dup is False
    # Second check should return True (is duplicate)
    is_dup = await db.is_duplicate(topic, identifier)
    assert is_dup is True
    # Wait for expiration
    await asyncio.sleep(1.01)
    # After expiration, should return False again
    is_dup = await db.is_duplicate(topic, identifier)
    assert is_dup is False
    is_dup = await db.is_duplicate('another', '12345')
    assert is_dup is False
    all_keys = await redis_client.execute_command('KEYS', '*')
    assert len(all_keys) == 2

@pytest.mark.asyncio
async def test_increment_counter(redis_client):
    db = RedisManager()
    db.client = redis_client
    topic = "counter_test"
    count = await db.increment_counter(topic)
    assert count == 1
    count = await db.increment_counter(topic)
    assert count == 2
    count = await db.increment_counter(topic)
    assert count == 3
    all_keys = await redis_client.execute_command('KEYS', '*')
    assert len(all_keys) == 1