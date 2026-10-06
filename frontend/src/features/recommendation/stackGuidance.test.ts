import { describe, expect, it } from 'vitest'
import type { PlanDetail, Stack } from '../../api/types.ts'
import { getStackGuidance } from './stackGuidance.ts'

describe('stackGuidance', () => {
  const dummyPlans: Record<string, PlanDetail> = {
    'cloudflare-pages-free': {
      provider: { id: 'cloudflare', name: 'Cloudflare', slug: 'cloudflare', description: '' },
      service: { id: 'cloudflare-pages', provider_id: 'cloudflare', name: 'Pages', slug: 'pages', description: '' },
      plan: { id: 'cloudflare-pages-free', service_id: 'cloudflare-pages', name: 'Free', slug: 'free', description: '', capabilities: [] },
      sources: [],
      pricing: { plan_id: 'cloudflare-pages-free', monthly_base_fee_usd_cents: 0, source_id: 'src-1', exceed_behaviors: [] },
      caveats: [],
    },
    'supabase-platform-free': {
      provider: { id: 'supabase', name: 'Supabase', slug: 'supabase', description: '' },
      service: { id: 'supabase-platform', provider_id: 'supabase', name: 'Platform', slug: 'platform', description: '' },
      plan: { id: 'supabase-platform-free', service_id: 'supabase-platform', name: 'Free Plan', slug: 'free', description: '', capabilities: [] },
      sources: [],
      pricing: { plan_id: 'supabase-platform-free', monthly_base_fee_usd_cents: 0, source_id: 'src-2', exceed_behaviors: [] },
      caveats: [],
    },
    'render-web-service-free': {
      provider: { id: 'render', name: 'Render', slug: 'render', description: '' },
      service: { id: 'render-web-service', provider_id: 'render', name: 'Web Service', slug: 'web-service', description: '' },
      plan: { id: 'render-web-service-free', service_id: 'render-web-service', name: 'Free', slug: 'free', description: '', capabilities: [] },
      sources: [],
      pricing: { plan_id: 'render-web-service-free', monthly_base_fee_usd_cents: 0, source_id: 'src-3', exceed_behaviors: [] },
      caveats: [],
    },
  }

  it('generates serverless and BaaS tags for Cloudflare Pages + Supabase', () => {
    const stack: Stack = {
      key: 'cf-pages+sb-platform',
      status: 'compatible',
      plan_ids: ['cloudflare-pages-free', 'supabase-platform-free'],
      assignments: [],
      budget_check: {
        outcome: 'satisfied',
        reason: 'within-budget',
        budget_usd_cents: 0,
        known_total_usd_cents: 0,
        priced_plan_ids: ['cloudflare-pages-free', 'supabase-platform-free'],
        unpriced_plan_ids: [],
      },
    }

    const guidance = getStackGuidance(stack, dummyPlans)
    expect(guidance.tags).toContain('💰 완전 무료 $0')
    expect(guidance.tags).toContain('⚡ 서버리스/간편 배포')
    expect(guidance.tags).toContain('📦 올인원 BaaS')
    expect(guidance.description).toContain('Supabase 백엔드로 시작하는 대중적인 조합')
    expect(guidance.description).not.toMatch(/1위|최적|Best|추천 순위|최고/)
  })

  it('generates backend server tag when Render web service is included', () => {
    const stack: Stack = {
      key: 'cf-pages+render-web',
      status: 'compatible',
      plan_ids: ['cloudflare-pages-free', 'render-web-service-free'],
      assignments: [],
      budget_check: null,
    }

    const guidance = getStackGuidance(stack, dummyPlans)
    expect(guidance.tags).toContain('💰 완전 무료 $0')
    expect(guidance.tags).toContain('🖥️ 백엔드 서버형')
    expect(guidance.tags).toContain('⚡ 서버리스/간편 배포')
    expect(guidance.description).toContain('상시 실행 백엔드 API 서버')
  })
})
