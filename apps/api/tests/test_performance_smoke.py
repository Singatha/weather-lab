import pytest

from performance.smoke import PerformanceResult, percentile


def test_percentile_uses_nearest_rank() -> None:
    values = [5.0, 1.0, 4.0, 2.0, 3.0]

    assert percentile(values, 0.50) == 3.0
    assert percentile(values, 0.95) == 5.0


def test_performance_result_calculates_rates() -> None:
    result = PerformanceResult(
        requests=100,
        errors=2,
        elapsed_seconds=0.5,
        p50_ms=2,
        p95_ms=5,
        p99_ms=8,
    )

    assert result.requests_per_second == 200
    assert result.error_rate == pytest.approx(0.02)
