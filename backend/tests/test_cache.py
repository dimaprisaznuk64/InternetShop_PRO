import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_delete_pattern,
    init_redis,
    close_redis,
    redis_client,
)


@pytest.mark.asyncio
async def test_cache_set_and_get():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"key": "value"}'
    mock_redis.ping.return_value = True

    with patch("app.cache.redis_client", mock_redis):
        await cache_set("test:key", {"key": "value"}, ttl=60)
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "test:key"

        result = await cache_get("test:key")
        assert result == {"key": "value"}
        mock_redis.get.assert_called_with("test:key")


@pytest.mark.asyncio
async def test_cache_get_miss():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("app.cache.redis_client", mock_redis):
        result = await cache_get("test:miss")
        assert result is None


@pytest.mark.asyncio
async def test_cache_delete():
    mock_redis = AsyncMock()

    with patch("app.cache.redis_client", mock_redis):
        await cache_delete("test:key")
        mock_redis.delete.assert_called_once_with("test:key")


@pytest.mark.asyncio
async def test_cache_delete_pattern():
    mock_redis = AsyncMock()

    async def fake_scan_iter(match=None):
        for k in ["products:list:1", "products:list:2"]:
            yield k

    mock_redis.scan_iter = fake_scan_iter

    with patch("app.cache.redis_client", mock_redis):
        await cache_delete_pattern("products:list:*")
        mock_redis.delete.assert_called_once_with("products:list:1", "products:list:2")


@pytest.mark.asyncio
async def test_cache_returns_none_when_redis_unavailable():
    with patch("app.cache.redis_client", None):
        result = await cache_get("any:key")
        assert result is None

        await cache_set("any:key", {"data": 1})
        await cache_delete("any:key")
        await cache_delete_pattern("any:*")


@pytest.mark.asyncio
async def test_cache_handles_redis_errors():
    mock_redis = AsyncMock()
    mock_redis.set.side_effect = Exception("Connection lost")

    with patch("app.cache.redis_client", mock_redis):
        await cache_set("test:key", {"data": 1})


@pytest.mark.asyncio
async def test_init_redis_success():
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True

    with patch("app.cache.aioredis.from_url", return_value=mock_redis):
        import app.cache as cache_module
        cache_module.redis_client = None
        await init_redis()
        assert cache_module.redis_client is mock_redis
        cache_module.redis_client = None


@pytest.mark.asyncio
async def test_init_redis_failure():
    with patch("app.cache.aioredis.from_url", side_effect=Exception("Connection refused")):
        import app.cache as cache_module
        cache_module.redis_client = None
        await init_redis()
        assert cache_module.redis_client is None


@pytest.mark.asyncio
async def test_close_redis():
    import app.cache as cache_module
    mock_redis = AsyncMock()
    cache_module.redis_client = mock_redis
    await close_redis()
    mock_redis.close.assert_called_once()
    assert cache_module.redis_client is None


@pytest.mark.asyncio
async def test_cache_delete_pattern_empty():
    mock_redis = AsyncMock()

    async def fake_scan_iter(match=None):
        return
        yield  # make it an async generator

    mock_redis.scan_iter = fake_scan_iter

    with patch("app.cache.redis_client", mock_redis):
        await cache_delete_pattern("no:keys:*")
        mock_redis.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cache_json_serialization():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"total": 5, "items": ["a", "b"]}'

    with patch("app.cache.redis_client", mock_redis):
        result = await cache_get("test:json")
        assert result["total"] == 5
        assert result["items"] == ["a", "b"]
