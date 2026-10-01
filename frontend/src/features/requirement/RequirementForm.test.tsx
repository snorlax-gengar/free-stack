import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../api/client.ts'
import { postRecommendation } from '../../api/recommendations.ts'
import type { RecommendationResponse } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import { RequirementForm } from './RequirementForm.tsx'

vi.mock('../../api/recommendations.ts', () => ({
  postRecommendation: vi.fn(),
}))

describe('RequirementForm', () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.mocked(postRecommendation).mockReset()
  })

  it('exposes every feature checkbox by its label', () => {
    render(<RequirementForm />)

    for (const label of Object.values(featureLabels)) {
      expect(screen.getByLabelText(label)).toBeTruthy()
    }
  })

  it('shows file storage only while file uploads is selected', () => {
    render(<RequirementForm />)

    expect(screen.queryByLabelText('파일 저장 용량')).toBeNull()
    fireEvent.click(screen.getByLabelText('파일 업로드'))
    expect(screen.getByLabelText('파일 저장 용량')).toBeTruthy()
    fireEvent.click(screen.getByLabelText('파일 업로드'))
    expect(screen.queryByLabelText('파일 저장 용량')).toBeNull()
  })

  it('shows the database size field when database is selected', () => {
    render(<RequirementForm />)

    fireEvent.click(screen.getByLabelText('데이터베이스'))
    expect(screen.getByLabelText('데이터베이스 크기')).toBeTruthy()
  })

  it('shows a feature error and does not call the API for an empty form', () => {
    render(<RequirementForm />)

    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    expect(screen.getByText(/필요한 기능을 하나 이상 선택해 주세요/)).toBeTruthy()
    expect(postRecommendation).not.toHaveBeenCalled()
  })

  it('submits 500 MB as 500000000 bytes', async () => {
    vi.mocked(postRecommendation).mockResolvedValue(composedResponse())
    render(<RequirementForm />)

    fireEvent.click(screen.getByLabelText('데이터베이스'))
    fireEvent.change(screen.getByLabelText('데이터베이스 크기'), { target: { value: '500' } })
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    const status = await screen.findByText('추천 결과를 받았습니다.')
    expect(status.getAttribute('role')).toBe('status')
    expect(postRecommendation).toHaveBeenCalledWith(
      {
        features: ['database'],
        file_storage_bytes: null,
        database_size_bytes: 500_000_000,
        monthly_bandwidth_bytes: null,
        monthly_budget_usd_cents: null,
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
  })

  it('submits a zero budget as 0 cents', async () => {
    vi.mocked(postRecommendation).mockResolvedValue(composedResponse())
    render(<RequirementForm />)

    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.change(screen.getByLabelText('월 예산 (USD)'), { target: { value: '0' } })
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    await screen.findByText('추천 결과를 받았습니다.')
    expect(vi.mocked(postRecommendation).mock.calls[0]?.[0]).toMatchObject({
      monthly_budget_usd_cents: 0,
    })
  })

  it('marks the submit button busy without disabling it', async () => {
    vi.mocked(postRecommendation).mockImplementation(() => new Promise(() => {}))
    render(<RequirementForm />)

    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    const button = await screen.findByRole('button', { name: '추천 받는 중…' })
    expect(button.getAttribute('aria-disabled')).toBe('true')
    expect(button.hasAttribute('disabled')).toBe(false)
  })

  it('shows the mapped invalid-requirement message and hides the server message', async () => {
    vi.mocked(postRecommendation).mockRejectedValue(
      new ApiError('http', 422, 'INVALID_REQUIREMENT', 'secret server message'),
    )
    render(<RequirementForm />)

    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    expect(
      await screen.findByText('선택한 기능과 입력값의 조합을 처리할 수 없습니다. 입력 내용을 확인해 주세요.'),
    ).toBeTruthy()
    expect(screen.queryByText('secret server message')).toBeNull()
  })

  it('announces a network failure', async () => {
    vi.mocked(postRecommendation).mockRejectedValue(new ApiError('network', null, null, 'offline'))
    render(<RequirementForm />)

    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    const alert = await screen.findByRole('alert')
    expect(alert.textContent).toContain(
      '서버에 연결할 수 없습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.',
    )
  })
})

function composedResponse(): RecommendationResponse {
  return {
    requirement: {
      features: ['database'],
      file_storage_bytes: null,
      database_size_bytes: 500_000_000,
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
