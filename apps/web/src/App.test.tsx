import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'
import { capeTown, weatherFixture } from './test/fixtures'

function mockApi(weather = weatherFixture) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const url = String(input)
    if (url.includes('/api/v1/weather')) {
      return new Response(JSON.stringify(weather), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    if (url.includes('/api/v1/locations/search')) {
      const query = new URL(url).searchParams.get('q') ?? ''
      const locations = query.toLowerCase().includes('cape') ? [capeTown] : []
      return new Response(JSON.stringify({ query, locations }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }
    throw new Error(`Unexpected request: ${url}`)
  })
}

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  )
}

afterEach(() => vi.restoreAllMocks())

describe('App', () => {
  it('renders a meaningful loading state while weather is pending', () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => new Promise(() => undefined))

    renderApp()

    expect(screen.getByLabelText(/loading weather forecast/i)).toHaveAttribute('aria-busy', 'true')
    expect(screen.getByRole('status')).toHaveTextContent('Loading...')
  })

  it('loads the default location and renders the complete forecast', async () => {
    mockApi()
    renderApp()

    expect(await screen.findByRole('heading', { name: 'Berlin, Germany' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /daily forecast/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /hourly forecast/i })).toBeInTheDocument()
    expect(screen.getAllByText('20°').length).toBeGreaterThan(0)
  })

  it('switches all measurements to imperial units', async () => {
    const user = userEvent.setup()
    mockApi()
    renderApp()
    await screen.findByRole('heading', { name: 'Berlin, Germany' })

    await user.click(screen.getByRole('button', { name: /units/i }))
    await user.click(screen.getByRole('menuitem', { name: /switch to imperial/i }))

    expect(screen.getAllByText('68°').length).toBeGreaterThan(0)
    expect(screen.getByText('9 mph')).toBeInTheDocument()
    expect(screen.getByText('0 in')).toBeInTheDocument()
  })

  it('supports keyboard selection from location suggestions', async () => {
    const user = userEvent.setup()
    mockApi()
    renderApp()
    await screen.findByRole('heading', { name: 'Berlin, Germany' })
    const input = screen.getByRole('combobox', { name: /search for a place/i })

    await user.type(input, 'Cape')
    await screen.findByRole('option', { name: /cape town, south africa/i })
    await user.keyboard('{ArrowDown}{Enter}')

    expect(await screen.findByRole('heading', { name: 'Cape Town, South Africa' })).toBeInTheDocument()
  })

  it('changes the day shown in the hourly forecast', async () => {
    const user = userEvent.setup()
    mockApi()
    renderApp()
    await screen.findByRole('heading', { name: 'Berlin, Germany' })
    const daySelector = screen.getByRole('combobox', { name: /forecast day/i })

    await user.selectOptions(daySelector, '2025-08-06')

    expect(daySelector).toHaveValue('2025-08-06')
    expect(screen.getByRole('option', { name: 'Wednesday' })).toHaveProperty('selected', true)
  })

  it('shows the empty state when a submitted search has no matches', async () => {
    const user = userEvent.setup()
    mockApi()
    renderApp()
    await screen.findByRole('heading', { name: 'Berlin, Germany' })

    await user.type(screen.getByRole('combobox', { name: /search for a place/i }), 'Atlantis')
    await user.click(screen.getByRole('button', { name: /^search$/i }))

    await waitFor(() => expect(screen.getByText(/no search result found/i)).toBeInTheDocument())
  })

  it('shows stale-data context when the API serves a saved forecast', async () => {
    const staleWeather = {
      ...weatherFixture,
      metadata: { ...weatherFixture.metadata, cache_status: 'stale' as const, is_stale: true },
    }
    mockApi(staleWeather)

    renderApp()

    expect(await screen.findByText(/showing the latest saved forecast/i)).toBeInTheDocument()
  })

  it('recovers from an API failure when retry succeeds', async () => {
    const user = userEvent.setup()
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ error: { code: 'UPSTREAM_ERROR', message: 'Service unavailable' } }),
        { status: 503, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    renderApp()
    expect(await screen.findByRole('alert', {}, { timeout: 4_000 })).toHaveTextContent(
      /something went wrong/i,
    )

    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(weatherFixture), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    await user.click(screen.getByRole('button', { name: /retry/i }))

    expect(await screen.findByRole('heading', { name: 'Berlin, Germany' })).toBeInTheDocument()
  })
})
