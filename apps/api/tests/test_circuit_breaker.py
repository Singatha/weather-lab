import pytest

from app.core.exceptions import ProviderCircuitOpenError
from app.resilience.circuit_breaker import CircuitBreaker, CircuitState


class MonotonicClock:
    def __init__(self) -> None:
        self.current = 0.0

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


def assert_state(breaker: CircuitBreaker, expected: CircuitState) -> None:
    assert breaker.state == expected


async def test_circuit_opens_probes_after_timeout_and_closes_on_success() -> None:
    clock = MonotonicClock()
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout_seconds=10,
        clock=clock,
    )

    await breaker.before_call()
    await breaker.record_failure()
    assert_state(breaker, CircuitState.CLOSED)
    assert breaker.consecutive_failures == 1

    await breaker.before_call()
    await breaker.record_failure()
    assert_state(breaker, CircuitState.OPEN)

    with pytest.raises(ProviderCircuitOpenError):
        await breaker.before_call()

    clock.advance(10)
    await breaker.before_call()
    assert_state(breaker, CircuitState.HALF_OPEN)
    await breaker.record_success()

    assert_state(breaker, CircuitState.CLOSED)
    assert breaker.consecutive_failures == 0


async def test_half_open_allows_one_probe_and_reopens_on_failure() -> None:
    clock = MonotonicClock()
    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout_seconds=5,
        clock=clock,
    )
    await breaker.before_call()
    await breaker.record_failure()
    clock.advance(5)

    await breaker.before_call()
    with pytest.raises(ProviderCircuitOpenError):
        await breaker.before_call()
    await breaker.record_failure()

    assert_state(breaker, CircuitState.OPEN)
