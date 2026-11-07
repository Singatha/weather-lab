import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { App } from './App'

describe('App', () => {
  it('renders the Phase 1 application shell', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: /weather lab foundation is ready/i }),
    ).toBeInTheDocument()
  })
})

