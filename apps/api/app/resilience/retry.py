import asyncio
import random
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Bounded exponential-backoff policy for transient operations."""

    max_attempts: int = 3
    base_delay_seconds: float = 0.2
    max_delay_seconds: float = 2.0
    jitter_ratio: float = 0.25

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        if self.base_delay_seconds < 0:
            raise ValueError("base_delay_seconds must not be negative")
        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError("max_delay_seconds must be at least base_delay_seconds")
        if not 0 <= self.jitter_ratio <= 1:
            raise ValueError("jitter_ratio must be between zero and one")

    def delay(self, failed_attempt: int, *, random_value: float) -> float:
        """Return capped exponential delay plus bounded positive jitter."""
        exponential = min(
            self.max_delay_seconds,
            self.base_delay_seconds * (2.0 ** (failed_attempt - 1)),
        )
        return exponential + (exponential * self.jitter_ratio * random_value)


async def retry_async[T](
    operation: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    is_retryable: Callable[[Exception], bool],
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    randomizer: Callable[[], float] = random.random,
) -> T:
    """Run an async operation with a finite number of eligible retries."""
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            if attempt >= policy.max_attempts or not is_retryable(exc):
                raise
            await sleep(policy.delay(attempt, random_value=randomizer()))

    raise RuntimeError("retry loop exhausted without returning or raising")
