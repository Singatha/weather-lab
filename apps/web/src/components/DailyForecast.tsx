import type { DailyForecast as DailyForecastType } from '../types/weather'
import { temperature, type UnitSettings } from '../utils/units'
import { weatherIcon, weekday } from '../utils/weather'

interface DailyForecastProps {
  days: DailyForecastType[]
  onSelectDay: (date: string) => void
  selectedDate: string
  units: UnitSettings
}

export function DailyForecast({ days, onSelectDay, selectedDate, units }: DailyForecastProps) {
  return (
    <section aria-labelledby="daily-heading" className="daily-section">
      <h2 id="daily-heading">Daily forecast</h2>
      <div className="daily-grid">
        {days.slice(0, 7).map((day) => (
          <button
            aria-pressed={selectedDate === day.date}
            className="daily-card"
            key={day.date}
            onClick={() => onSelectDay(day.date)}
            type="button"
          >
            <span>{weekday(day.date)}</span>
            <span className="sr-only">{day.condition.description}. </span>
            <img alt="" aria-hidden="true" src={weatherIcon(day.condition.category)} />
            <span className="daily-temperatures">
              <span><span className="sr-only">High </span>{temperature(day.temperature_max, units.temperature)}</span>
              <span><span className="sr-only">Low </span>{temperature(day.temperature_min, units.temperature)}</span>
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}
