import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { PlanDetail, Stack } from '../../api/types.ts'
import { StackCaveatsCallout } from './StackCaveatsCallout.tsx'

describe('StackCaveatsCallout', () => {
  const mockPlans: Record<string, PlanDetail> = {
    'render-web': {
      plan: {
        id: 'render-web',
        service_id: 'render-srv',
        name: 'Free',
        slug: 'free',
        description: 'Render free',
        capabilities: ['server-compute'],
      },
      service: {
        id: 'render-srv',
        provider_id: 'render',
        name: 'Web Service',
        slug: 'web-service',
        description: 'Web service',
      },
      provider: {
        id: 'render',
        name: 'Render',
        slug: 'render',
        description: 'Render provider',
      },
      pricing: null,
      caveats: [
        {
          plan_id: 'render-web',
          statement: 'A Free web service spins down after 15 minutes without inbound traffic.',
          source_id: 'src-1',
        },
        {
          plan_id: 'render-web',
          statement: 'Spinning a Free web service back up takes about one minute.',
          source_id: 'src-2',
        },
        {
          plan_id: 'render-web',
          statement: 'Free web services have an ephemeral filesystem.',
          source_id: 'src-3',
        },
        {
          plan_id: 'render-web',
          statement: 'A persistent disk cannot be attached to a Free web service.',
          source_id: 'src-4',
        },
      ],
      sources: [],
    },
  }

  const mockStack: Stack = {
    key: 'render-web',
    plan_ids: ['render-web'],
    status: 'compatible',
    assignments: [],
    budget_check: null,
  }

  it('renders Korean summary for known caveat statements and expands list on toggle', () => {
    render(<StackCaveatsCallout stack={mockStack} plans={mockPlans} />)

    expect(screen.getByText(/무료 티어 핵심 제약 & 주의사항/)).toBeTruthy()
    expect(screen.getByText('15분 미요청 시 슬립(Spin down)')).toBeTruthy()
    expect(screen.getByText('슬립 후 첫 요청 시 재기동(Cold Start) 약 1분 소요')).toBeTruthy()

    // 4th caveat is hidden initially
    expect(screen.queryByText('영구 디스크 연결 불가')).toBeNull()

    const toggleButton = screen.getByRole('button', { name: /\+ 주의사항 1개 더 보기/ })
    fireEvent.click(toggleButton)

    // Now expanded
    expect(screen.getByText('영구 디스크 연결 불가')).toBeTruthy()
    expect(screen.getByRole('button', { name: /주의사항 접기/ })).toBeTruthy()
  })

  it('renders nothing when stack has no caveats', () => {
    const plansNoCaveats: Record<string, PlanDetail> = {
      'render-web': {
        ...mockPlans['render-web']!,
        caveats: [],
      },
    }
    const { container } = render(<StackCaveatsCallout stack={mockStack} plans={plansNoCaveats} />)
    expect(container.firstChild).toBeNull()
  })
})
