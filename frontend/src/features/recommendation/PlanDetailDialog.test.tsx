import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { StrictMode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { PlanDetail, Pricing } from '../../api/types.ts'
import { fixtureA, fixtureK } from './fixtures/recommendationResponses.ts'
import { PlanDetailDialog } from './PlanDetailDialog.tsx'

const originalShowModal = HTMLDialogElement.prototype.showModal
const originalClose = HTMLDialogElement.prototype.close

describe('PlanDetailDialog', () => {
  beforeEach(() => {
    HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
      this.setAttribute('open', '')
    }
    HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
      this.removeAttribute('open')
      this.dispatchEvent(new Event('close'))
    }
  })

  afterEach(() => {
    cleanup()
    HTMLDialogElement.prototype.showModal = originalShowModal
    HTMLDialogElement.prototype.close = originalClose
  })

  it('shows the plan label, catalog text, and capabilities', () => {
    renderDialog(renderPlan())

    const dialog = screen.getByRole('dialog')
    const title = screen.getByRole('heading', { level: 2, name: 'Render · Web Service · Free' })
    expect(dialog.getAttribute('aria-labelledby')).toBe(title.id)
    expect(screen.getByText('Application hosting platform.').lang).toBe('en')
    expect(screen.getByText('Hosted web application compute.').lang).toBe('en')
    expect(screen.getByText('Free Render web service instance.').lang).toBe('en')
    expect(within(screen.getByRole('list', { name: '제공 기능' })).getByText('서버 컴퓨트')).toBeTruthy()
  })

  it('keeps capability order from the plan', () => {
    renderDialog(supabasePlan())

    expect(within(screen.getByRole('list', { name: '제공 기능' })).getAllByRole('listitem').map((item) => item.textContent)).toEqual([
      '서버리스 함수',
      '데이터베이스',
      '파일 저장',
      '인증',
      '실시간',
    ])
  })

  it('does not present missing pricing as zero dollars', () => {
    renderDialog(renderPlan())

    expect(screen.getByText('가격 정보 없음')).toBeTruthy()
    expect(screen.getByText('이 플랜의 가격 정보가 아직 등록되지 않았습니다.')).toBeTruthy()
    expect(screen.queryByText(/\$0/)).toBeNull()
    expect(screen.queryByText('무료')).toBeNull()
  })

  it('formats a zero base fee and its source', () => {
    renderDialog(withFee(renderPlan(), 0, 'render-compute-plans'))

    const price = screen.getByText(/월 기본 요금/).closest('p')
    expect(price?.textContent).toContain('월 기본 요금 $0')
    expect(within(price as HTMLElement).getByRole('link', { name: '[출처 1]' })).toBeTruthy()
    expect(screen.getByText('사용량을 넘으면: 초과 요금 · 사용 중지 · 기능 제한')).toBeTruthy()
    expect(screen.queryByText('무료')).toBeNull()
  })

  it('formats a fractional base fee', () => {
    renderDialog(withFee(renderPlan(), 499, 'render-free'))

    expect(screen.getByText(/월 기본 요금 \$4\.99/).textContent).toContain('[출처 2]')
  })

  it('says when there are no caveats', () => {
    renderDialog({ ...renderPlan(), caveats: [] })

    expect(screen.getByRole('heading', { name: '주의사항 (0)' })).toBeTruthy()
    expect(screen.getByText('등록된 주의사항이 없습니다.')).toBeTruthy()
  })

  it('keeps fixture K caveat order and source numbers', () => {
    renderDialog(renderPlan())

    const items = within(screen.getByRole('list', { name: '주의사항' })).getAllByRole('listitem')
    expect(items).toHaveLength(11)
    expect(items[0]?.textContent).toContain('Each workspace receives 750 Free instance hours per calendar month.')
    expect(items[0]?.lang).toBe('en')
    expect(items[10]?.textContent).toContain('The Free web service compute plan provides 512 MB of RAM.')
    expect(within(items[0]!).getByRole('link', { name: '[출처 2]' })).toBeTruthy()
    expect(within(items[10]!).getByRole('link', { name: '[출처 1]' })).toBeTruthy()
  })

  it('shows fixture A as one source', () => {
    renderDialog(supabasePlan())

    const sources = within(screen.getByRole('list', { name: '이 결과에 사용된 출처' })).getAllByRole('listitem')
    expect(sources).toHaveLength(1)
    const link = within(sources[0]!).getByRole('link')
    expect(link.getAttribute('href')).toBe('https://supabase.com/docs/guides/platform/billing-on-supabase')
    expect(link.getAttribute('target')).toBe('_blank')
    expect(link.getAttribute('rel')).toContain('noopener')
    expect(link.getAttribute('rel')).toContain('noreferrer')
    expect(link.textContent).toContain('(새 탭에서 열림)')
    expect(sources[0]?.textContent).toContain('확인일 2026년 9월 30일')
    expect(sources[0]?.textContent).toContain('Official Supabase billing documentation.')
  })

  it('keeps fixture K source order', () => {
    renderDialog(renderPlan())

    const sources = within(screen.getByRole('list', { name: '이 결과에 사용된 출처' })).getAllByRole('listitem')
    expect(sources.map((item) => item.querySelector('a')?.getAttribute('href'))).toEqual([
      'https://render.com/docs/compute-plans',
      'https://render.com/docs/free',
    ])
    expect(sources[0]?.textContent).toContain('확인일 2026년 9월 30일')
    expect(sources[0]?.textContent).toContain('Official Render compute plan specifications.')
    expect(sources[1]?.querySelector('p[lang="en"]')?.textContent).toBe('Official Render Free instance documentation.')
  })

  it('omits empty source notes', () => {
    const detail = supabasePlan()
    const source = detail.sources[0]
    expect(source).toBeDefined()
    if (source === undefined) {
      return
    }
    renderDialog({ ...detail, sources: [{ ...source, notes: '' }] })

    expect(screen.getByText('확인일 2026년 9월 30일')).toBeTruthy()
    expect(screen.queryByText('Official Supabase billing documentation.')).toBeNull()
  })

  it('says when there are no sources', () => {
    renderDialog({ ...renderPlan(), sources: [], caveats: [] })

    expect(screen.getByText('출처 정보가 없습니다.')).toBeTruthy()
    expect(screen.queryByRole('list', { name: '이 결과에 사용된 출처' })).toBeNull()
  })

  it('points a caveat citation at the matching source item', () => {
    renderDialog(renderPlan())

    const caveats = within(screen.getByRole('list', { name: '주의사항' })).getAllByRole('listitem')
    const sources = within(screen.getByRole('list', { name: '이 결과에 사용된 출처' })).getAllByRole('listitem')
    const firstCitation = within(caveats[0]!).getByRole('link', { name: '[출처 2]' })
    const lastCitation = within(caveats[10]!).getByRole('link', { name: '[출처 1]' })
    expect(firstCitation.getAttribute('href')).toBe(`#${sources[1]?.id}`)
    expect(lastCitation.getAttribute('href')).toBe(`#${sources[0]?.id}`)
  })

  it('notifies the parent from the close button and the close event', () => {
    const onClose = vi.fn()
    renderDialog(renderPlan(), onClose)

    const dialog = screen.getByRole('dialog')
    fireEvent.click(screen.getByRole('button', { name: '닫기' }))
    expect(onClose).toHaveBeenCalledTimes(1)

    dialog.dispatchEvent(new Event('close'))
    expect(onClose).toHaveBeenCalledTimes(2)
  })

  it('does not treat a strict-mode remount as a user close', () => {
    const onClose = vi.fn()
    render(
      <StrictMode>
        <PlanDetailDialog detail={renderPlan()} onClose={onClose} />
      </StrictMode>,
    )

    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByRole('dialog', { name: 'Render · Web Service · Free' })).toBeTruthy()
  })

  it('restores focus when the dialog unmounts', () => {
    const opener = document.createElement('button')
    opener.textContent = '열기'
    document.body.append(opener)
    opener.focus()
    const { unmount } = render(<PlanDetailDialog detail={renderPlan()} onClose={() => undefined} />)

    unmount()

    expect(document.activeElement).toBe(opener)
    opener.remove()
  })
})

function renderDialog(detail: PlanDetail, onClose: () => void = () => undefined) {
  return render(<PlanDetailDialog detail={detail} onClose={onClose} />)
}

function renderPlan(): PlanDetail {
  const detail = fixtureK.plans['render-web-service-free']
  if (detail === undefined) {
    throw new Error('fixture K is missing the Render plan')
  }
  return detail
}

function supabasePlan(): PlanDetail {
  const detail = fixtureA.plans['supabase-platform-free']
  if (detail === undefined) {
    throw new Error('fixture A is missing the Supabase plan')
  }
  return detail
}

function withFee(detail: PlanDetail, cents: number, sourceId: string): PlanDetail {
  const pricing = {
    plan_id: detail.plan.id,
    monthly_base_fee_usd_cents: cents,
    exceed_behaviors: ['charged', 'suspended', 'restricted'],
    source_id: sourceId,
  } satisfies Pricing
  return { ...detail, pricing }
}
