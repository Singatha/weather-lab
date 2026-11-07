# ADR 0003: Provider boundary and timezone-aware normalization

- Status: Accepted
- Date: 2026-11-07

## Context

Open-Meteo exposes useful but vendor-specific geocoding and forecast payloads.
The frontend needs stable contracts, and forecast days and hours must follow the
searched location rather than the API server's timezone.

## Decision

Define an application-facing `WeatherProvider` protocol and implement an
`OpenMeteoProvider` adapter. The adapter requests canonical metric units and
`timezone=auto`, validates the external payload, maps WMO codes, and attaches
the returned IANA timezone to local ISO timestamps before returning application
schemas.

Routes depend on `WeatherService`, which receives the provider through
dependency injection. Automated provider tests use HTTPX mock transports.

## Alternatives

- Returning Open-Meteo JSON directly would reduce code initially but couple
  the frontend and cache format to a vendor contract.
- Requesting Unix timestamps would remove ISO parsing, but Open-Meteo requires
  additional offset handling for local daily boundaries. Local ISO values plus
  the returned IANA zone make the response intent clearer.
- Converting units in the backend was considered. Canonical metric storage and
  frontend conversion better support the Phase 3 cache design.

## Consequences

Provider replacement and deterministic testing are straightforward, and API
consumers receive timezone-aware values. The adapter must continue validating
array alignment and updating its external models when provider contracts
change.

