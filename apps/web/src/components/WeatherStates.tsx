export function LoadingState() {
  return (
    <div className="forecast-layout" aria-busy="true" aria-label="Loading weather forecast">
      <div className="primary-column">
        <section className="overview-skeleton skeleton-card">
          <div className="loading-label" role="status">
            <img alt="" aria-hidden="true" className="spin" src="/assets/images/icon-loading.svg" />
            <span>Loading...</span>
          </div>
        </section>
        <section aria-hidden="true" className="weather-metrics">
          {['Feels Like', 'Humidity', 'Wind', 'Precipitation'].map((label) => (
            <article className="metric-card" key={label}>
              <h3>{label}</h3><p>–</p>
            </article>
          ))}
        </section>
        <section aria-hidden="true" className="daily-section">
          <h2>Daily forecast</h2>
          <div className="daily-grid">
            {Array.from({ length: 7 }, (_, index) => <div className="daily-card skeleton-card" key={index} />)}
          </div>
        </section>
      </div>
      <section aria-hidden="true" className="hourly-section">
        <div className="hourly-header"><h2>Hourly forecast</h2><span className="fake-select">–</span></div>
        <div className="hourly-list">
          {Array.from({ length: 8 }, (_, index) => <div className="hour-skeleton skeleton-card" key={index} />)}
        </div>
      </section>
    </div>
  )
}

export function NoResultsState() {
  return <p className="no-results" role="status">No search result found!</p>
}

interface ErrorStateProps {
  onRetry: () => void
}

export function ErrorState({ onRetry }: ErrorStateProps) {
  return (
    <section className="error-state" role="alert">
      <img alt="" aria-hidden="true" src="/assets/images/icon-error.svg" />
      <h1>Something went wrong</h1>
      <p>We couldn’t connect to the server (API error). Please try again in a few moments.</p>
      <button onClick={onRetry} type="button">
        <img alt="" aria-hidden="true" src="/assets/images/icon-retry.svg" /> Retry
      </button>
    </section>
  )
}
