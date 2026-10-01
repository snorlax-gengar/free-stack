import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import {
  fixtureA,
  fixtureB,
  fixtureC,
  fixtureD,
  fixtureE,
  fixtureF,
  fixtureG,
} from './fixtures/recommendationResponses.ts'
import { RecommendationResult } from './RecommendationResult.tsx'

describe('RecommendationResult', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders a composed result from fixture A and focuses the heading', () => {
    render(<RecommendationResult response={fixtureA} />)

    const heading = screen.getByRole('heading', { level: 2, name: '추천 결과' })
    expect(heading.tabIndex).toBe(-1)
    expect(document.activeElement).toBe(heading)

    const features = screen.getByRole('list', { name: '선택한 기능' })
    expect(within(features).getAllByRole('listitem').map((item) => item.textContent)).toEqual([
      '데이터베이스',
      '인증',
      '실시간',
    ])
    expect(screen.getByText('예산 조건 없음')).toBeTruthy()
    expect(screen.getByRole('heading', { name: '충족 (1)' })).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Supabase Platform' })).toBeTruthy()

    const plans = screen.getByRole('list', { name: '플랜' })
    const rows = within(plans).getAllByRole('listitem')
    expect(rows).toHaveLength(1)
    expect(rows[0]?.textContent).toContain('Supabase')
    expect(rows[0]?.textContent).toContain('Platform')
    expect(rows[0]?.textContent).toContain('Free')
    expect(rows[0]?.textContent).toContain('인증 · 데이터베이스 · 실시간')
    expect(screen.queryByText(/^예산 \$/)).toBeNull()
    expect(screen.queryByText(/확인된 합계/)).toBeNull()
    expect(resultText()).not.toMatch(/1위|최적|Best|추천 1/)
    expect(resultText().replace('표시 순서는 순위가 아닙니다.', '')).not.toContain('순위')
  })

  it('shows an unknown budget without a confirmed total for fixture F', () => {
    render(<RecommendationResult response={fixtureF} />)

    expect(screen.getByText('월 $0 상한')).toBeTruthy()
    expect(screen.getByRole('heading', { name: '확인 필요 (1)' })).toBeTruthy()
    expect(screen.getByText('가격 확인 필요')).toBeTruthy()
    expect(screen.queryByText(/확인된 합계/)).toBeNull()
  })

  it('renders two plan rows for fixture G', () => {
    render(<RecommendationResult response={fixtureG} />)

    expect(screen.getByRole('heading', { name: 'Cloudflare Pages + Cloudflare R2' })).toBeTruthy()
    expect(within(screen.getByRole('list', { name: '플랜' })).getAllByRole('listitem')).toHaveLength(2)
  })

  it('shows unevaluated features beside a composed result for fixture D', () => {
    render(<RecommendationResult response={fixtureD} />)

    expect(screen.getByText('평가되지 않은 기능: AI API')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Cloudflare Pages' })).toBeTruthy()
    expect(screen.getByText(/조합 1개를 구성했습니다/)).toBeTruthy()
  })

  it.each([
    ['blocked', fixtureB, '조합 불가'],
    ['no-roles', fixtureC, '평가할 역할 없음'],
    ['too-many-combinations', fixtureE, '조합이 너무 많음'],
  ] as const)('shows only the %s status label', (_status, response, label) => {
    render(<RecommendationResult response={response} />)

    expect(screen.getByText(label)).toBeTruthy()
    expect(screen.queryByText(/조합 \d+개를 구성했습니다/)).toBeNull()
    expect(screen.queryByRole('list', { name: '플랜' })).toBeNull()
  })

  it('shows the plan id when plan details are missing', () => {
    render(<RecommendationResult response={{ ...fixtureA, plans: {} }} />)

    expect(screen.getByRole('heading', { name: 'supabase-platform-free' })).toBeTruthy()
    expect(within(screen.getByRole('list', { name: '플랜' })).getByText('supabase-platform-free')).toBeTruthy()
  })
})

function resultText(): string {
  return screen.getByRole('region', { name: '추천 결과' }).textContent ?? ''
}
