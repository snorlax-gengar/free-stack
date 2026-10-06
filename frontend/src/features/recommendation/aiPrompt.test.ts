import { describe, expect, it } from 'vitest'
import type { PlanDetail, Stack } from '../../api/types.ts'
import { buildAiPrompt } from './aiPrompt.ts'

describe('buildAiPrompt', () => {
  const mockPlans: Record<string, PlanDetail> = {
    'cf-pages': {
      plan: {
        id: 'cf-pages',
        service_id: 'cf-pages-srv',
        name: 'Free',
        slug: 'free',
        description: 'Pages free',
        capabilities: ['static-hosting'],
      },
      service: {
        id: 'cf-pages-srv',
        provider_id: 'cloudflare',
        name: 'Pages',
        slug: 'pages',
        description: 'Pages service',
      },
      provider: {
        id: 'cloudflare',
        name: 'Cloudflare',
        slug: 'cloudflare',
        description: 'Cloudflare provider',
      },
      pricing: null,
      caveats: [
        {
          plan_id: 'cf-pages',
          statement: 'The Free plan includes 500 builds per month.',
          source_id: 'src-1',
        },
      ],
      sources: [],
    },
    'supa-free': {
      plan: {
        id: 'supa-free',
        service_id: 'supa-srv',
        name: 'Free',
        slug: 'free',
        description: 'Supabase free',
        capabilities: ['database', 'authentication'],
      },
      service: {
        id: 'supa-srv',
        provider_id: 'supabase',
        name: 'Platform',
        slug: 'platform',
        description: 'Supabase platform',
      },
      provider: {
        id: 'supabase',
        name: 'Supabase',
        slug: 'supabase',
        description: 'Supabase provider',
      },
      pricing: null,
      caveats: [
        {
          plan_id: 'supa-free',
          statement: 'The 500 MB database size quota applies per project.',
          source_id: 'src-2',
        },
      ],
      sources: [],
    },
  }

  const mockStack: Stack = {
    key: 'cf-pages+supa-free',
    plan_ids: ['cf-pages', 'supa-free'],
    status: 'compatible',
    assignments: [
      {
        feature: 'static-frontend',
        plan_id: 'cf-pages',
        status: 'compatible',
      },
      {
        feature: 'database',
        plan_id: 'supa-free',
        status: 'compatible',
      },
      {
        feature: 'authentication',
        plan_id: 'supa-free',
        status: 'compatible',
      },
    ],
    budget_check: null,
  }

  it('generates a structured prompt with services, caveats, and instructions', () => {
    const prompt = buildAiPrompt(mockStack, mockPlans)

    expect(prompt).toContain('# FreeStack 추천 무료 기술 스택 기반 프로젝트 개발 프롬프트')
    expect(prompt).toContain('Cloudflare Pages + Supabase Platform')
    expect(prompt).toContain('[정적 프론트엔드] Cloudflare Pages (Free 플랜)')
    expect(prompt).toContain('[데이터베이스, 인증] Supabase Platform (Free 플랜)')
    expect(prompt).toContain('준수해야 할 무료 티어 핵심 제약사항')
    expect(prompt).toContain('[Cloudflare Pages] The Free plan includes 500 builds per month.')
    expect(prompt).toContain('[Supabase Platform] The 500 MB database size quota applies per project.')
    expect(prompt).toContain('AI Agent (Cursor / Claude / ChatGPT) 지침 및 요청 사항')
    expect(prompt).toContain('.env.example')
  })

  it('omits caveats section when there are no caveats', () => {
    const plansWithoutCaveats: Record<string, PlanDetail> = {
      'cf-pages': { ...mockPlans['cf-pages']!, caveats: [] },
      'supa-free': { ...mockPlans['supa-free']!, caveats: [] },
    }

    const prompt = buildAiPrompt(mockStack, plansWithoutCaveats)
    expect(prompt).not.toContain('준수해야 할 무료 티어 핵심 제약사항')
    expect(prompt).toContain('Cloudflare Pages + Supabase Platform')
  })
})
