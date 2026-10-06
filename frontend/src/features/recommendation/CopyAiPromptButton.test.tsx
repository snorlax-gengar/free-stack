import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { PlanDetail, Stack } from '../../api/types.ts'
import { CopyAiPromptButton } from './CopyAiPromptButton.tsx'

describe('CopyAiPromptButton', () => {
  const originalClipboard = navigator.clipboard

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    Object.defineProperty(navigator, 'clipboard', {
      value: originalClipboard,
      configurable: true,
      writable: true,
    })
  })

  const mockPlans: Record<string, PlanDetail> = {
    'plan-a': {
      plan: {
        id: 'plan-a',
        service_id: 'srv-a',
        name: 'Free',
        slug: 'free',
        description: 'Plan A free',
        capabilities: ['static-hosting'],
      },
      service: {
        id: 'srv-a',
        provider_id: 'prov-a',
        name: 'Hosting',
        slug: 'hosting',
        description: 'Hosting service',
      },
      provider: {
        id: 'prov-a',
        name: 'Provider A',
        slug: 'provider-a',
        description: 'Provider A',
      },
      pricing: null,
      caveats: [],
      sources: [],
    },
  }

  const mockStack: Stack = {
    key: 'plan-a',
    plan_ids: ['plan-a'],
    status: 'compatible',
    assignments: [],
    budget_check: null,
  }

  it('renders default button and updates text when clicked and copied', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      configurable: true,
      writable: true,
    })

    render(<CopyAiPromptButton stack={mockStack} plans={mockPlans} />)

    const button = screen.getByRole('button', { name: /AI 개발 프롬프트 복사/ })
    expect(button).toBeTruthy()

    fireEvent.click(button)

    await waitFor(() => {
      expect(writeTextMock).toHaveBeenCalled()
      expect(screen.getByRole('button', { name: /AI 개발 프롬프트가 복사되었습니다!/ })).toBeTruthy()
    })
  })
})
