import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, getHealth } from './api/client'
import { postRecommendation } from './api/recommendations'
import type { RecommendationResponse } from './api/types'
import App from './App'

vi.mock('./api/client', async () => {
  const actual = await vi.importActual<typeof import('./api/client')>('./api/client')
  return { ...actual, getHealth: vi.fn() }
})

vi.mock('./api/recommendations', () => ({
  postRecommendation: vi.fn(),
}))

describe('App', () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.mocked(getHealth).mockReset()
    vi.mocked(postRecommendation).mockReset()
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

  it('owns a successful recommendation without rendering the response', async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: 'ok' })
    vi.mocked(postRecommendation).mockResolvedValue(composedResponse())

    render(<App />)
    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    const status = await screen.findByText('추천 결과를 받았습니다.')
    expect(status.getAttribute('role')).toBe('status')
    expect(postRecommendation).toHaveBeenCalledWith(
      expect.objectContaining({
        features: ['static-frontend'],
        monthly_budget_usd_cents: null,
      }),
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
    expect(screen.queryByText(/"composition"/)).toBeNull()
  })

  it('keeps the submitting state on the submit button', async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: 'ok' })
    vi.mocked(postRecommendation).mockImplementation(() => new Promise(() => {}))

    render(<App />)
    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    const button = await screen.findByRole('button', { name: '추천 받는 중…' })
    expect(button.getAttribute('aria-disabled')).toBe('true')
    expect(button.hasAttribute('disabled')).toBe(false)
  })

  it('shows a mapped error from the app-owned submission', async () => {
    vi.mocked(getHealth).mockResolvedValue({ status: 'ok' })
    vi.mocked(postRecommendation).mockRejectedValue(
      new ApiError('http', 422, 'INVALID_REQUIREMENT', 'secret server message'),
    )

    render(<App />)
    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    expect(
      await screen.findByText('선택한 기능과 입력값의 조합을 처리할 수 없습니다. 입력 내용을 확인해 주세요.'),
    ).toBeTruthy()
    expect(screen.queryByText('secret server message')).toBeNull()
  })
})

function composedResponse(): RecommendationResponse {
  return {
    requirement: {
      features: ['static-frontend'],
      file_storage_bytes: null,
      database_size_bytes: null,
      monthly_bandwidth_bytes: null,
      monthly_budget_usd_cents: null,
    },
    roles: [],
    composition: {
      status: 'composed',
      compatible: [],
      unknown: [],
      incompatible: [],
      blocked_roles: [],
      combination_count: 0,
      unevaluated_features: [],
    },
    unevaluated_features: [],
    plans: {},
    sources: {},
  }
}
