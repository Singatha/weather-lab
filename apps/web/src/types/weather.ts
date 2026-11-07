export type WeatherCategory =
  | 'clear'
  | 'partly_cloudy'
  | 'overcast'
  | 'fog'
  | 'drizzle'
  | 'rain'
  | 'snow'
  | 'storm'
  | 'unknown'

export interface WeatherCondition {
  code: number
  description: string
  category: WeatherCategory
}

export interface Location {
  id: number
  name: string
  country: string
  country_code: string
  region: string | null
  latitude: number
  longitude: number
  timezone: string
  elevation_m: number | null
  population: number | null
}

export interface LocationSearchResponse {
  query: string
  locations: Location[]
}

export interface CurrentWeather {
  time: string
  temperature: number
  apparent_temperature: number
  relative_humidity: number
  precipitation: number
  wind_speed: number
  is_day: boolean
  condition: WeatherCondition
}

export interface HourlyForecast {
  time: string
  temperature: number
  relative_humidity: number
  precipitation: number
  precipitation_probability: number
  wind_speed: number
  is_day: boolean
  condition: WeatherCondition
}

export interface DailyForecast {
  date: string
  temperature_max: number
  temperature_min: number
  precipitation_sum: number
  precipitation_probability_max: number
  sunrise: string
  sunset: string
  condition: WeatherCondition
}

export interface WeatherResponse {
  location: {
    latitude: number
    longitude: number
    elevation_m: number | null
    timezone: string
    timezone_abbreviation: string
    utc_offset_seconds: number
  }
  current: CurrentWeather
  hourly: HourlyForecast[]
  daily: DailyForecast[]
  units: {
    temperature: 'celsius'
    wind_speed: 'km/h'
    precipitation: 'mm'
    relative_humidity: 'percent'
  }
  metadata: {
    provider: 'open-meteo'
    fetched_at: string
    provider_generation_time_ms: number
    cache_status: 'not_cached' | 'miss' | 'hit' | 'stale' | 'bypass'
    is_stale: boolean
    cached_at: string | null
  }
}

export interface ApiErrorEnvelope {
  error?: {
    code?: string
    message?: string
  }
}
