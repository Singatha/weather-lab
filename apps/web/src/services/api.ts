import type {
  ApiErrorEnvelope,
  LocationSearchResponse,
  WeatherResponse,
} from '../types/weather'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: 'application/json' },
    signal,
  })

  if (!response.ok) {
    let payload: ApiErrorEnvelope | undefined
    try {
      payload = (await response.json()) as ApiErrorEnvelope
    } catch {
      payload = undefined
    }

    throw new ApiError(
      payload?.error?.message ?? 'The weather service is unavailable right now.',
      response.status,
      payload?.error?.code,
    )
  }

  return (await response.json()) as T
}

export function searchLocations(query: string, signal?: AbortSignal) {
  return getJson<LocationSearchResponse>(
    `/api/v1/locations/search?q=${encodeURIComponent(query)}`,
    signal,
  )
}

export function getWeather(
  latitude: number,
  longitude: number,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
  })
  return getJson<WeatherResponse>(`/api/v1/weather?${params}`, signal)
}
