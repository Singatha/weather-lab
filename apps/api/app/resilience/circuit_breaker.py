import asyncio
import time
from collections.abc import Callable
from enum import StrEnum

from app.core.exceptions import ProviderCircuitOpenError


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Async-safe consecutive-failure circuit breaker with one half-open probe."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least one")
        if recovery_timeout_seconds <= 0:
            raise ValueError("recovery_timeout_seconds must be positive")
        self._failure_threshold = failure_threshold
        self._recovery_timeout_seconds = recovery_timeout_seconds
        self._clock = clock
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._probe_in_flight = False
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    async def before_call(self) -> None:
        """Allow a call, promote to half-open, or fail fast while open."""
        async with self._lock:
            if self._state is CircuitState.OPEN:
                assert self._opened_at is not None
                elapsed = self._clock() - self._opened_at
                if elapsed < self._recovery_timeout_seconds:
                    raise ProviderCircuitOpenError()
                self._state = CircuitState.HALF_OPEN

            if self._state is CircuitState.HALF_OPEN:
                if self._probe_in_flight:
                    raise ProviderCircuitOpenError()
                self._probe_in_flight = True

    async def record_success(self) -> None:
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = None
            self._probe_in_flight = False

    async def record_failure(self) -> None:
        async with self._lock:
            self._consecutive_failures += 1
            if (
                self._state is CircuitState.HALF_OPEN
                or self._consecutive_failures >= self._failure_threshold
            ):
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()
            self._probe_in_flight = False
