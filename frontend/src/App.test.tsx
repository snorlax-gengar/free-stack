import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHealth } from './api/client'
import App from './App'

vi.mock('./api/client', () => ({
  getHealth: vi.fn(),
}))

describe('App', () => {
  beforeEach(() => {
    vi.mocked(getHealth).mockReset()
  })

  it('shows OK when the health API succeeds', async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: 'ok' })

    render(<App />)

    expect(screen.getByText('Backend Status: Checking...')).toBeTruthy()
    expect(await screen.findByText('Backend Status: OK')).toBeTruthy()
  })

  it('shows connection failed when the health API fails', async () => {
    vi.mocked(getHealth).mockRejectedValue(new Error('network down'))

    render(<App />)

    expect(await screen.findByText('Backend Status: Connection Failed')).toBeTruthy()
  })
})
