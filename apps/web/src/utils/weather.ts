import type { WeatherCategory } from '../types/weather'

const imageByCategory: Record<WeatherCategory, string> = {
  clear: 'icon-sunny.webp',
  partly_cloudy: 'icon-partly-cloudy.webp',
  overcast: 'icon-overcast.webp',
  fog: 'icon-fog.webp',
  drizzle: 'icon-drizzle.webp',
  rain: 'icon-rain.webp',
  snow: 'icon-snow.webp',
  storm: 'icon-storm.webp',
  unknown: 'icon-overcast.webp',
}

export function weatherIcon(category: WeatherCategory): string {
  return `/assets/images/${imageByCategory[category]}`
}

export function localDateKey(value: string, timeZone: string): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date(value))
  const lookup = Object.fromEntries(parts.map((part) => [part.type, part.value]))
  return `${lookup.year}-${lookup.month}-${lookup.day}`
}

export function formatFullDate(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat('en-US', {
    timeZone,
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

export function formatHour(value: string, timeZone: string): string {
  return new Intl.DateTimeFormat('en-US', {
    timeZone,
    hour: 'numeric',
    hour12: true,
  }).format(new Date(value))
}

export function weekday(value: string, style: 'short' | 'long' = 'short'): string {
  return new Intl.DateTimeFormat('en-US', { weekday: style }).format(
    new Date(`${value}T12:00:00`),
  )
}
