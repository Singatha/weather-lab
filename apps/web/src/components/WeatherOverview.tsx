import type { Location, WeatherResponse } from '../types/weather'
import { precipitation, temperature, type UnitSettings, windSpeed } from '../utils/units'
import { formatFullDate, weatherIcon } from '../utils/weather'

interface WeatherOverviewProps {
  location: Location
  units: UnitSettings
  weather: WeatherResponse
}

export function WeatherOverview({ location, units, weather }: WeatherOverviewProps) {
  const { current } = weather
  const metrics = [
    ['Feels Like', temperature(current.apparent_temperature, units.temperature)],
    ['Humidity', `${current.relative_humidity}%`],
    ['Wind', windSpeed(current.wind_speed, units.wind)],
    ['Precipitation', precipitation(current.precipitation, units.precipitation)],
  ]

  return (
    <>
      {weather.metadata.is_stale && (
        <p className="stale-notice" role="status">
          Showing the latest saved forecast while the weather service reconnects.
        </p>
      )}
      <section className="weather-overview" aria-labelledby="current-weather-heading">
        <div className="place-details">
          <h2 id="current-weather-heading">{location.name}, {location.country}</h2>
          <p>{formatFullDate(current.time, weather.location.timezone)}</p>
        </div>
        <div className="current-condition">
          <img
            alt={current.condition.description}
            className="current-icon"
            src={weatherIcon(current.condition.category)}
          />
          <strong>{temperature(current.temperature, units.temperature)}</strong>
        </div>
      </section>

      <section aria-label="Current weather details" className="weather-metrics">
        {metrics.map(([label, value]) => (
          <article className="metric-card" key={label}>
            <h3>{label}</h3>
            <p>{value}</p>
          </article>
        ))}
      </section>
    </>
  )
}
