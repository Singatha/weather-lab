from datetime import datetime, timedelta


class MutableClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def __call__(self) -> datetime:
        return self.current

    def advance(self, *, seconds: int) -> None:
        self.current += timedelta(seconds=seconds)


class InMemoryCacheBackend:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.fail_get = False
        self.fail_set = False
        self.fail_ping = False
        self.closed = False

    async def get(self, key: str) -> str | None:
        if self.fail_get:
            raise ConnectionError("cache unavailable")
        return self.values.get(key)

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        if self.fail_set:
            raise ConnectionError("cache unavailable")
        self.values[key] = value
        self.ttls[key] = ttl_seconds

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)
        self.ttls.pop(key, None)

    async def ping(self) -> bool:
        if self.fail_ping:
            raise ConnectionError("cache unavailable")
        return True

    async def aclose(self) -> None:
        self.closed = True
