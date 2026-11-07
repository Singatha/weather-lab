import argparse
import asyncio
import math
from dataclasses import dataclass
from time import perf_counter

import httpx


@dataclass(frozen=True)
class PerformanceResult:
    requests: int
    errors: int
    elapsed_seconds: float
    p50_ms: float
    p95_ms: float
    p99_ms: float

    @property
    def requests_per_second(self) -> float:
        return self.requests / self.elapsed_seconds

    @property
    def error_rate(self) -> float:
        return self.errors / self.requests


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("At least one value is required")
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return ordered[index]


async def run_smoke(
    *,
    base_url: str,
    requests: int,
    concurrency: int,
) -> PerformanceResult:
    semaphore = asyncio.Semaphore(concurrency)
    durations: list[float] = []
    errors = 0

    async with httpx.AsyncClient(base_url=base_url, timeout=5) as client:

        async def request_once() -> None:
            nonlocal errors
            async with semaphore:
                started = perf_counter()
                try:
                    response = await client.get("/health/live")
                    if response.status_code != 200:
                        errors += 1
                except httpx.HTTPError:
                    errors += 1
                durations.append((perf_counter() - started) * 1000)

        started = perf_counter()
        await asyncio.gather(*(request_once() for _ in range(requests)))
        elapsed = perf_counter() - started

    return PerformanceResult(
        requests=requests,
        errors=errors,
        elapsed_seconds=elapsed,
        p50_ms=percentile(durations, 0.50),
        p95_ms=percentile(durations, 0.95),
        p99_ms=percentile(durations, 0.99),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Weather API performance smoke check")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--max-p95-ms", type=float, default=250)
    parser.add_argument("--max-error-rate", type=float, default=0)
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1:
        parser.error("requests and concurrency must be positive")
    return args


def main() -> int:
    args = parse_args()
    result = asyncio.run(
        run_smoke(
            base_url=args.base_url.rstrip("/"),
            requests=args.requests,
            concurrency=min(args.concurrency, args.requests),
        )
    )
    print(
        f"requests={result.requests} errors={result.errors} "
        f"rps={result.requests_per_second:.1f} p50_ms={result.p50_ms:.2f} "
        f"p95_ms={result.p95_ms:.2f} p99_ms={result.p99_ms:.2f}"
    )
    if result.error_rate > args.max_error_rate or result.p95_ms > args.max_p95_ms:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
