import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../api/client.ts'
import type { RecommendationRequest } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import { RequirementForm, type RequirementFormProps } from './RequirementForm.tsx'

describe('RequirementForm', () => {
  afterEach(() => {
    cleanup()
  })

  it('exposes every feature checkbox by its label', () => {
    renderForm()

    for (const label of Object.values(featureLabels)) {
      expect(screen.getByLabelText(label)).toBeTruthy()
    }
  })

  it('shows file storage only while file uploads is selected', () => {
    renderForm()

    expect(screen.queryByLabelText('파일 저장 용량')).toBeNull()
    fireEvent.click(screen.getByLabelText('파일 업로드'))
    expect(screen.getByLabelText('파일 저장 용량')).toBeTruthy()
    fireEvent.click(screen.getByLabelText('파일 업로드'))
    expect(screen.queryByLabelText('파일 저장 용량')).toBeNull()
  })

  it('shows the database size field when database is selected', () => {
    renderForm()

    fireEvent.click(screen.getByLabelText('데이터베이스'))
    expect(screen.getByLabelText('데이터베이스 크기')).toBeTruthy()
  })

  it('shows a feature error and does not submit an empty form', () => {
    const { onSubmit } = renderForm()

    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    expect(screen.getByText(/필요한 기능을 하나 이상 선택해 주세요/)).toBeTruthy()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits 500 MB as 500000000 bytes', () => {
    const { onSubmit } = renderForm()

    fireEvent.click(screen.getByLabelText('데이터베이스'))
    fireEvent.change(screen.getByLabelText('데이터베이스 크기'), { target: { value: '500' } })
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    expect(onSubmit).toHaveBeenCalledWith({
      features: ['database'],
      file_storage_bytes: null,
      database_size_bytes: 500_000_000,
      monthly_bandwidth_bytes: null,
      monthly_budget_usd_cents: null,
    } satisfies RecommendationRequest)
  })

  it('submits a zero budget as 0 cents', () => {
    const { onSubmit } = renderForm()

    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.change(screen.getByLabelText('월 예산 (USD)'), { target: { value: '0' } })
    fireEvent.click(screen.getByRole('button', { name: '무료 스택 추천받기' }))

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ monthly_budget_usd_cents: 0 }))
  })

  it('marks the submit button busy without disabling it', () => {
    renderForm({ submitting: true })

    const button = screen.getByRole('button', { name: '추천 받는 중…' })
    expect(button.getAttribute('aria-disabled')).toBe('true')
    expect(button.getAttribute('aria-busy')).toBe('true')
    expect(button.hasAttribute('disabled')).toBe(false)
  })

  it('ignores another submit while a request is in progress', () => {
    const { onSubmit } = renderForm({ submitting: true })

    fireEvent.click(screen.getByLabelText('정적 프론트엔드'))
    fireEvent.click(screen.getByRole('button', { name: '추천 받는 중…' }))

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('shows the success status without the response body', () => {
    renderForm({ succeeded: true })

    const status = screen.getByRole('status')
    expect(status.textContent).toContain('추천 결과를 받았습니다.')
  })

  it('shows the mapped invalid-requirement message and hides the server message', () => {
    renderForm({
      error: new ApiError('http', 422, 'INVALID_REQUIREMENT', 'secret server message'),
    })

    expect(
      screen.getByText('선택한 기능과 입력값의 조합을 처리할 수 없습니다. 입력 내용을 확인해 주세요.'),
    ).toBeTruthy()
    expect(screen.queryByText('secret server message')).toBeNull()
  })

  it('announces a network failure', () => {
    renderForm({ error: new ApiError('network', null, null, 'offline') })

    const alert = screen.getByRole('alert')
    expect(alert.textContent).toContain(
      '서버에 연결할 수 없습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.',
    )
  })
})

function renderForm(overrides: Partial<RequirementFormProps> = {}) {
  const onSubmit = overrides.onSubmit ?? vi.fn()
  render(
    <RequirementForm
      submitting={overrides.submitting ?? false}
      succeeded={overrides.succeeded ?? false}
      error={'error' in overrides ? overrides.error : null}
      onSubmit={onSubmit}
    />,
  )
  return { onSubmit }
}
