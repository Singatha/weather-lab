import { expect, test, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { capeTown, weatherFixture } from '../src/test/fixtures'

async function mockApi(page: Page) {
  await page.route('**/api/v1/weather?*', async (route) => {
    await route.fulfill({ json: weatherFixture })
  })
  await page.route('**/api/v1/locations/search?*', async (route) => {
    const query = new URL(route.request().url()).searchParams.get('q') ?? ''
    await route.fulfill({
      json: {
        query,
        locations: query.toLowerCase().includes('cape') ? [capeTown] : [],
      },
    })
  })
}

test.beforeEach(async ({ page }) => {
  await mockApi(page)
  await page.goto('/')
})

test('loads the forecast and changes measurement systems', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Berlin, Germany' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Daily forecast' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Hourly forecast' })).toBeVisible()

  await page.getByRole('button', { name: /units/i }).click()
  await page.getByRole('menuitem', { name: /switch to imperial/i }).click()
  await expect(page.locator('.current-condition').getByText('68°')).toBeVisible()
  await expect(page.getByText('9 mph')).toBeVisible()
})

test('searches for a location with the keyboard', async ({ page }) => {
  const search = page.getByRole('combobox', { name: /search for a place/i })
  await search.fill('Cape')
  await expect(page.getByRole('option', { name: /cape town, south africa/i })).toBeVisible()
  await search.press('ArrowDown')
  await search.press('Enter')
  await expect(page.getByRole('heading', { name: 'Cape Town, South Africa' })).toBeVisible()
})

test('shows a clear empty state', async ({ page }) => {
  await page.getByRole('combobox', { name: /search for a place/i }).fill('Atlantis')
  await page.getByRole('button', { name: /^search$/i }).click()
  await expect(page.getByText('No search result found!')).toBeVisible()
})

test('changes the hourly forecast day', async ({ page }) => {
  const selector = page.getByRole('combobox', { name: /forecast day/i })

  await selector.selectOption('2025-08-06')

  await expect(selector).toHaveValue('2025-08-06')
  await expect(selector.getByRole('option', { name: 'Wednesday' })).toHaveJSProperty(
    'selected',
    true,
  )
})

test('recovers after an API error', async ({ page }) => {
  await page.unroute('**/api/v1/weather?*')
  await page.route('**/api/v1/weather?*', async (route) => {
    await route.fulfill({
      status: 503,
      json: { error: { code: 'UPSTREAM_ERROR', message: 'Service unavailable' } },
    })
  })
  await page.reload()
  await expect(page.getByRole('alert')).toContainText('Something went wrong', { timeout: 5_000 })

  await page.unroute('**/api/v1/weather?*')
  await page.route('**/api/v1/weather?*', async (route) => {
    await route.fulfill({ json: weatherFixture })
  })
  await page.getByRole('button', { name: /retry/i }).click()

  await expect(page.getByRole('heading', { name: 'Berlin, Germany' })).toBeVisible()
})

test('has no detectable WCAG A or AA violations', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Berlin, Germany' })).toBeVisible()
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()

  expect(results.violations).toEqual([])
})
