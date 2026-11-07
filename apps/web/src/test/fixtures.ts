import type { Location, WeatherResponse } from '../types/weather'

export const capeTown: Location = {
  id: 3369157,
  name: 'Cape Town',
  country: 'South Africa',
  country_code: 'ZA',
  region: 'Western Cape',
  latitude: -33.92584,
  longitude: 18.42322,
  timezone: 'Africa/Johannesburg',
  elevation_m: 25,
  population: 433688,
}

const conditions = [
  ['rain', 'Rain', 61],
  ['drizzle', 'Drizzle', 51],
  ['clear', 'Clear sky', 0],
  ['partly_cloudy', 'Partly cloudy', 2],
  ['storm', 'Thunderstorm', 95],
  ['snow', 'Snow showers', 85],
  ['fog', 'Fog', 45],
] as const

export const weatherFixture: WeatherResponse = {
  location: {
    latitude: 52.52437,
    longitude: 13.41053,
    elevation_m: 74,
    timezone: 'Europe/Berlin',
    timezone_abbreviation: 'CEST',
    utc_offset_seconds: 7200,
  },
  current: {
    time: '2025-08-05T15:00:00+02:00',
    temperature: 20,
    apparent_temperature: 18,
    relative_humidity: 46,
    precipitation: 0,
    wind_speed: 14,
    is_day: true,
    condition: { code: 0, description: 'Clear sky', category: 'clear' },
  },
  hourly: Array.from({ length: 7 * 24 }, (_, index) => {
    const date = new Date('2025-08-04T22:00:00Z')
    date.setUTCHours(date.getUTCHours() + index)
    const condition = conditions[index % conditions.length]
    return {
      time: date.toISOString(),
      temperature: 17 + (index % 8),
      relative_humidity: 50,
      precipitation: index % 4 === 0 ? 0.4 : 0,
      precipitation_probability: 20,
      wind_speed: 12,
      is_day: index % 24 >= 6 && index % 24 <= 20,
      condition: { code: condition[2], description: condition[1], category: condition[0] },
    }
  }),
  daily: conditions.map((condition, index) => {
    const day = new Date('2025-08-05T12:00:00Z')
    day.setUTCDate(day.getUTCDate() + index)
    const date = day.toISOString().slice(0, 10)
    return {
      date,
      temperature_max: 20 + index,
      temperature_min: 14 + index,
      precipitation_sum: index,
      precipitation_probability_max: 30,
      sunrise: `${date}T06:00:00+02:00`,
      sunset: `${date}T20:00:00+02:00`,
      condition: { code: condition[2], description: condition[1], category: condition[0] },
    }
  }),
  units: {
    temperature: 'celsius',
    wind_speed: 'km/h',
    precipitation: 'mm',
    relative_humidity: 'percent',
  },
  metadata: {
    provider: 'open-meteo',
    fetched_at: '2025-08-05T13:00:00Z',
    provider_generation_time_ms: 0.4,
    cache_status: 'hit',
    is_stale: false,
    cached_at: '2025-08-05T13:00:00Z',
  },
}
