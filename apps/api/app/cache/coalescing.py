import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass


@dataclass
class _LockEntry:
    lock: asyncio.Lock
    users: int = 0


class RequestCoalescer:
    """Coalesce same-key misses within one API process."""

    def __init__(self) -> None:
        self._registry_lock = asyncio.Lock()
        self._locks: dict[str, _LockEntry] = {}

    @asynccontextmanager
    async def hold(self, key: str) -> AsyncIterator[None]:
        async with self._registry_lock:
            entry = self._locks.get(key)
            if entry is None:
                entry = _LockEntry(lock=asyncio.Lock())
                self._locks[key] = entry
            entry.users += 1

        acquired = False
        try:
            await entry.lock.acquire()
            acquired = True
            yield
        finally:
            if acquired:
                entry.lock.release()
            async with self._registry_lock:
                entry.users -= 1
                if entry.users == 0:
                    self._locks.pop(key, None)
