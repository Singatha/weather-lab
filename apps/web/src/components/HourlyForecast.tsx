import { useMemo } from 'react'
import type { DailyForecast, HourlyForecast as HourlyForecastType } from '../types/weather'
import { temperature, type UnitSettings } from '../utils/units'
import { formatHour, localDateKey, weatherIcon, weekday } from '../utils/weather'

interface HourlyForecastProps {
  currentTime: string
  days: DailyForecast[]
  hours: HourlyForecastType[]
  onSelectDay: (date: string) => void
  selectedDate: string
  timeZone: string
  units: UnitSettings
}

export function HourlyForecast({
  currentTime,
  days,
  hours,
  onSelectDay,
  selectedDate,
  timeZone,
  units,
}: HourlyForecastProps) {
  const visibleHours = useMemo(() => {
    const dayHours = hours.filter((hour) => localDateKey(hour.time, timeZone) === selectedDate)
    const futureHours = dayHours.filter((hour) => new Date(hour.time) >= new Date(currentTime))
    return (futureHours.length >= 4 ? futureHours : dayHours).slice(0, 8)
  }, [currentTime, hours, selectedDate, timeZone])

  return (
    <section aria-labelledby="hourly-heading" className="hourly-section">
      <div className="hourly-header">
        <h2 id="hourly-heading">Hourly forecast</h2>
        <label className="day-select-label">
          <span className="sr-only">Forecast day</span>
          <select
            aria-label="Forecast day"
            onChange={(event) => onSelectDay(event.target.value)}
            value={selectedDate}
          >
            {days.slice(0, 7).map((day) => (
              <option key={day.date} value={day.date}>{weekday(day.date, 'long')}</option>
            ))}
          </select>
        </label>
      </div>

      <ol className="hourly-list">
        {visibleHours.map((hour) => (
          <li key={hour.time}>
            <img alt="" aria-hidden="true" src={weatherIcon(hour.condition.category)} />
            <time dateTime={hour.time}>{formatHour(hour.time, timeZone)}</time>
            <span>{temperature(hour.temperature, units.temperature)}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}
