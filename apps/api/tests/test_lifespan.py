from pathlib import Path
from typing import cast

import httpx
import pytest
from fastapi import FastAPI
from redis.asyncio import Redis

import app.main as main_module
from app.core.config import Settings


class FakeHttpClient:
    def __init__(self, *, fail_close: bool = False) -> None:
        self.closed = False
        self.fail_close = fail_close

    async def aclose(self) -> None:
        self.closed = True
        if self.fail_close:
            raise RuntimeError("HTTP close failed")


class FakeRedisClient:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


async def test_lifespan_closes_all_resources_and_clears_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_http = FakeHttpClient(fail_close=True)
    fake_redis = FakeRedisClient()
    monkeypatch.setattr(
        main_module,
        "_build_http_client",
        lambda: cast(httpx.AsyncClient, fake_http),
    )
    monkeypatch.setattr(
        main_module,
        "_build_redis_client",
        lambda: cast(Redis, fake_redis),
    )
    application = FastAPI()

    async with main_module.lifespan(application):
        assert application.state.weather_service is not None
        assert application.state.rate_limiter is not None
        assert application.state.cache_service is not None

    assert fake_http.closed is True
    assert fake_redis.closed is True
    assert not hasattr(application.state, "weather_service")
    assert not hasattr(application.state, "rate_limiter")
    assert not hasattr(application.state, "cache_service")


async def test_http_client_uses_separate_bounded_timeouts() -> None:
    client = main_module._build_http_client()
    try:
        assert client.timeout.connect == 3
        assert client.timeout.read == 10
        assert client.timeout.write == 5
        assert client.timeout.pool == 3
    finally:
        await client.aclose()


def test_redis_password_is_loaded_from_secret_file(tmp_path: Path) -> None:
    secret_file = tmp_path / "redis_password"
    secret_file.write_text("production-secret\n", encoding="utf-8")

    password = main_module._redis_password(Settings(redis_password_file=secret_file))

    assert password == "production-secret"


def test_empty_redis_password_file_is_rejected(tmp_path: Path) -> None:
    secret_file = tmp_path / "redis_password"
    secret_file.write_text("\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="must not be empty"):
        main_module._redis_password(Settings(redis_password_file=secret_file))
