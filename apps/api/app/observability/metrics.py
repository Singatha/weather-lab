from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST

_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)


class ObservabilityMetrics:
    """Own a low-cardinality Prometheus registry for one application instance."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry(auto_describe=True)
        self._http_requests = Counter(
            "weather_http_requests_total",
            "HTTP requests completed by the API.",
            ("method", "route", "status_code"),
            registry=self.registry,
        )
        self._http_errors = Counter(
            "weather_http_errors_total",
            "HTTP responses with a status code of 400 or greater.",
            ("method", "route", "status_code"),
            registry=self.registry,
        )
        self._http_duration = Histogram(
            "weather_http_request_duration_seconds",
            "End-to-end HTTP request latency.",
            ("method", "route"),
            buckets=_LATENCY_BUCKETS,
            registry=self.registry,
        )
        self._cache_operations = Counter(
            "weather_cache_operations_total",
            "Cache operations by operation and bounded result.",
            ("operation", "result"),
            registry=self.registry,
        )
        self._provider_requests = Counter(
            "weather_provider_requests_total",
            "Logical provider requests by operation and outcome.",
            ("operation", "outcome"),
            registry=self.registry,
        )
        self._provider_duration = Histogram(
            "weather_provider_request_duration_seconds",
            "Logical provider request latency, including retries.",
            ("operation", "outcome"),
            buckets=_LATENCY_BUCKETS,
            registry=self.registry,
        )

    def observe_http(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        labels = (method, route, str(status_code))
        self._http_requests.labels(*labels).inc()
        self._http_duration.labels(method, route).observe(duration_seconds)
        if status_code >= 400:
            self._http_errors.labels(*labels).inc()

    def observe_cache(self, *, operation: str, result: str) -> None:
        self._cache_operations.labels(operation, result).inc()

    def observe_provider(
        self,
        *,
        operation: str,
        outcome: str,
        duration_seconds: float,
    ) -> None:
        self._provider_requests.labels(operation, outcome).inc()
        self._provider_duration.labels(operation, outcome).observe(duration_seconds)

    def render(self) -> tuple[bytes, str]:
        return generate_latest(self.registry), CONTENT_TYPE_LATEST
