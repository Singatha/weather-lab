export type TemperatureUnit = 'celsius' | 'fahrenheit'
export type WindUnit = 'km/h' | 'mph'
export type PrecipitationUnit = 'mm' | 'in'

export interface UnitSettings {
  temperature: TemperatureUnit
  wind: WindUnit
  precipitation: PrecipitationUnit
}

export const METRIC_UNITS: UnitSettings = {
  temperature: 'celsius',
  wind: 'km/h',
  precipitation: 'mm',
}

export const IMPERIAL_UNITS: UnitSettings = {
  temperature: 'fahrenheit',
  wind: 'mph',
  precipitation: 'in',
}

export function temperature(value: number, unit: TemperatureUnit): string {
  const converted = unit === 'fahrenheit' ? (value * 9) / 5 + 32 : value
  return `${Math.round(converted)}°`
}

export function windSpeed(value: number, unit: WindUnit): string {
  const converted = unit === 'mph' ? value / 1.609344 : value
  return `${Math.round(converted)} ${unit}`
}

export function precipitation(value: number, unit: PrecipitationUnit): string {
  const converted = unit === 'in' ? value / 25.4 : value
  const rounded = converted < 10 ? Math.round(converted * 10) / 10 : Math.round(converted)
  return `${rounded} ${unit}`
}
