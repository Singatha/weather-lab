import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_retry_delay_configuration_must_be_ordered() -> None:
    with pytest.raises(ValidationError):
        Settings(
            weather_provider_retry_base_delay_seconds=2,
            weather_provider_retry_max_delay_seconds=1,
        )


def test_keepalive_pool_must_not_exceed_total_connections() -> None:
    with pytest.raises(ValidationError):
        Settings(
            weather_provider_max_connections=5,
            weather_provider_max_keepalive_connections=6,
        )
