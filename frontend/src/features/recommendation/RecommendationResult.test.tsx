import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import {
  fixtureA,
  fixtureB,
  fixtureC,
  fixtureD,
  fixtureE,
  fixtureF,
  fixtureG,
  fixtureJ,
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
    expect(within(screen.getByRole('region', { name: '구성' })).getByRole('heading', { name: '충족 (1)' })).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Supabase Platform' })).toBeTruthy()

    const plans = screen.getByRole('list', { name: '플랜' })
    const rows = planRowsIn(plans)
    expect(rows).toHaveLength(1)
    expect(rows[0]?.textContent).toContain('Supabase · Platform · Free')
    const assigned = within(rows[0]!).getAllByRole('listitem')
    expect(assigned.map((item) => item.textContent?.replaceAll(/\s+/g, ''))).toEqual([
      '인증충족',
      '데이터베이스충족',
      '실시간충족',
    ])
    expect(screen.queryByText(/^예산 \$/)).toBeNull()
    expect(screen.queryByText(/확인된 합계/)).toBeNull()
    expect(screen.queryByText('무료')).toBeNull()
    expect(resultText()).not.toMatch(/1위|최적|Best|추천 순위|최고/)
    expect(withoutRankDisclaimers(resultText())).not.toContain('순위')
  })

  it('shows an unknown budget without a confirmed total for fixture F', () => {
    render(<RecommendationResult response={fixtureF} />)

    expect(screen.getByText('월 $0 상한')).toBeTruthy()
    expect(within(screen.getByRole('region', { name: '구성' })).getByRole('heading', { name: '확인 필요 (1)' })).toBeTruthy()
    expect(screen.getByText('가격 확인 필요')).toBeTruthy()
    expect(screen.queryByText(/확인된 합계/)).toBeNull()
  })

  it('renders two plan rows for fixture G', () => {
    render(<RecommendationResult response={fixtureG} />)

    expect(screen.getByRole('heading', { name: 'Cloudflare Pages + Cloudflare R2' })).toBeTruthy()
    const rows = planRowsIn(screen.getByRole('list', { name: '플랜' }))
    expect(rows.map((row) => row.textContent)).toEqual([
      expect.stringContaining('Cloudflare · Pages · Free'),
      expect.stringContaining('Cloudflare · R2 · Free'),
    ])
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

  it('shows role candidates and their checks', () => {
    render(<RecommendationResult response={fixtureG} />)

    expect(screen.getByRole('heading', { name: '역할별 후보 평가' })).toBeTruthy()
    const uploads = screen.getByText('파일 업로드 — 충족 1 · 미충족 1')
    expect(uploads.closest('details')?.open).toBe(false)
    fireEvent.click(uploads)

    const details = uploads.closest('details')
    expect(details).not.toBeNull()
    if (details === null) {
      return
    }
    expect(within(details).getByRole('heading', { name: '충족 (1)' })).toBeTruthy()
    expect(within(details).getByRole('heading', { name: '미충족 (1)' })).toBeTruthy()
    expect(within(details).getByText('Cloudflare · R2 · Free')).toBeTruthy()
    expect(within(details).getByText('Supabase · Platform · Free')).toBeTruthy()
    expect(within(details).getByText('공통 사용량: 미충족 — 대역폭 월 5 GB · 한도 초과')).toBeTruthy()
    expect(within(details).queryByText('무료')).toBeNull()
  })

  it('says when a role has no evaluated candidates', () => {
    render(<RecommendationResult response={fixtureB} />)

    expect(screen.getByText('예약 작업 — 평가된 후보가 없습니다')).toBeTruthy()
  })

  it('does not render role evaluations when roles are empty', () => {
    render(<RecommendationResult response={fixtureC} />)

    expect(screen.queryByRole('heading', { name: '역할별 후보 평가' })).toBeNull()
  })

  it('keeps fixture J stack order and shared plan assignments', () => {
    render(<RecommendationResult response={fixtureJ} />)

    const articles = screen.getAllByRole('article')
    expect(articles.map((article) => within(article).getByRole('heading', { level: 4 }).textContent)).toEqual([
      'Cloudflare Pages + Cloudflare R2',
      'Cloudflare Pages + Supabase Platform',
    ])
    const lists = screen.getAllByRole('list', { name: '플랜' })
    expect(planRowsIn(lists[0]!).map((row) => row.textContent?.includes('파일 업로드'))).toEqual([false, true])
    expect(planRowsIn(lists[1]!).map((row) => row.textContent?.includes('파일 업로드'))).toEqual([false, true])
    expect(planRowsIn(lists[0]!)[1]?.textContent).toContain('Cloudflare · R2 · Free')
    expect(planRowsIn(lists[1]!)[1]?.textContent).toContain('Supabase · Platform · Free')
    expect(articles.flatMap((article) => within(article).getAllByText('Cloudflare · Pages · Free'))).toHaveLength(2)
    expect(resultText()).not.toMatch(/1위|최적|Best|추천 순위|최고/)
  })

  it('shows the plan id when plan details are missing', () => {
    render(<RecommendationResult response={{ ...fixtureA, plans: {} }} />)

    expect(screen.getByRole('heading', { name: 'supabase-platform-free' })).toBeTruthy()
    expect(within(screen.getByRole('list', { name: '플랜' })).getByText('supabase-platform-free')).toBeTruthy()
  })
})

function planRowsIn(list: HTMLElement): HTMLElement[] {
  return [...list.querySelectorAll(':scope > li')].filter((node): node is HTMLElement => node instanceof HTMLElement)
}

function resultText(): string {
  return screen.getByRole('region', { name: '추천 결과' }).textContent ?? ''
}

function withoutRankDisclaimers(text: string): string {
  return text
    .replaceAll('표시 순서는 순위가 아닙니다.', '')
    .replaceAll('충족·확인 필요·미충족은 순위가 아니라 평가 상태입니다.', '')
}
