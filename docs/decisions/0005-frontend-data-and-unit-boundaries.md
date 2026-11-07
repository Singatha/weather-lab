# ADR 0005: Frontend data and unit boundaries

- Status: accepted
- Date: 2026-11-07

## Context

The dashboard needs responsive weather views, searchable locations, day
selection, and flexible measurement settings without coupling the browser to
Open-Meteo or duplicating server data.

## Decision

FastAPI remains the frontend's only weather data source. TanStack Query owns
remote request state, caching, cancellation, and retries. The selected location,
forecast day, and unit preferences remain small component-level React state.

The backend contract stays canonical in Celsius, km/h, and millimeters. Pure
formatters convert these values for display, so changing units never refetches
weather data. Location labels remain paired with their coordinates in the
browser because the coordinate-based weather response intentionally does not
repeat geocoding presentation fields.

The UI uses the supplied assets and self-hosted fonts. Native form semantics,
ARIA combobox/listbox relationships, visible focus styling, and reduced-motion
support provide accessible interaction without a component framework.

## Consequences

- provider response changes remain isolated behind the API
- unit switching is instant and does not increase provider or cache traffic
- frontend tests can mock one stable application contract
- optional preference persistence remains explicitly outside the MVP
