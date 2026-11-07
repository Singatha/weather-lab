import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { DailyForecast } from './components/DailyForecast'
import { Header } from './components/Header'
import { HourlyForecast } from './components/HourlyForecast'
import { LocationSearch } from './components/LocationSearch'
import { WeatherOverview } from './components/WeatherOverview'
import { ErrorState, LoadingState, NoResultsState } from './components/WeatherStates'
import { getWeather } from './services/api'
import type { Location } from './types/weather'
import { METRIC_UNITS, type UnitSettings } from './utils/units'

const DEFAULT_LOCATION: Location = {
  id: 2950159,
  name: 'Berlin',
  country: 'Germany',
  country_code: 'DE',
  region: 'Berlin',
  latitude: 52.52437,
  longitude: 13.41053,
  timezone: 'Europe/Berlin',
  elevation_m: 74,
  population: 3426354,
}

export function App() {
  const [location, setLocation] = useState(DEFAULT_LOCATION)
  const [units, setUnits] = useState<UnitSettings>(METRIC_UNITS)
  const [selectedDate, setSelectedDate] = useState('')
  const [hasNoResults, setHasNoResults] = useState(false)
  const weatherQuery = useQuery({
    queryKey: ['weather', location.latitude, location.longitude],
    queryFn: ({ signal }) => getWeather(location.latitude, location.longitude, signal),
    staleTime: 10 * 60 * 1000,
    retry: 1,
  })

  const weather = weatherQuery.data
  const activeDate =
    weather?.daily.some((day) => day.date === selectedDate) && selectedDate
      ? selectedDate
      : (weather?.daily[0]?.date ?? '')

  const selectLocation = (nextLocation: Location) => {
    setLocation(nextLocation)
    setSelectedDate('')
    setHasNoResults(false)
  }

  return (
    <div className="app-shell">
      <Header onUnitsChange={setUnits} units={units} />

      {weatherQuery.isError && !weather ? (
        <ErrorState onRetry={() => void weatherQuery.refetch()} />
      ) : (
        <main>
          <h1 className="hero-title">How’s the sky looking today?</h1>
          <LocationSearch onNoResults={() => setHasNoResults(true)} onSelect={selectLocation} />

          {hasNoResults ? (
            <NoResultsState />
          ) : weatherQuery.isPending || !weather ? (
            <LoadingState />
          ) : (
            <div className="forecast-layout">
              <div className="primary-column">
                <WeatherOverview location={location} units={units} weather={weather} />
                <DailyForecast
                  days={weather.daily}
                  onSelectDay={setSelectedDate}
                  selectedDate={activeDate}
                  units={units}
                />
              </div>
              <HourlyForecast
                currentTime={weather.current.time}
                days={weather.daily}
                hours={weather.hourly}
                onSelectDay={setSelectedDate}
                selectedDate={activeDate}
                timeZone={weather.location.timezone}
                units={units}
              />
            </div>
          )}
        </main>
      )}

      <footer>
        Weather data by{' '}
        <a href="https://open-meteo.com/" rel="noreferrer" target="_blank">Open-Meteo</a>
      </footer>
    </div>
  )
}
