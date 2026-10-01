import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { getHealth } from './api/client'
import App from './App'

vi.mock('./api/client', () => ({
  getHealth: vi.fn(),
}))

vi.mock('./api/recommendations', () => ({
  postRecommendation: vi.fn(),
}))

describe('App', () => {
  afterEach(() => {
    cleanup()
  })

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

  it('renders the requirement form', () => {
    vi.mocked(getHealth).mockResolvedValue({ status: 'ok' })

    render(<App />)

    expect(screen.getByRole('heading', { name: 'FreeStack' })).toBeTruthy()
    expect(screen.getByText('내 프로젝트에 필요한 기능을 선택하세요.')).toBeTruthy()
    expect(screen.getByText('조건을 입력하면 적합한 인프라 조합을 찾아드립니다.')).toBeTruthy()
    expect(screen.getByRole('button', { name: '무료 스택 추천받기' })).toBeTruthy()
  })
})
