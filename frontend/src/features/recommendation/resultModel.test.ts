import { describe, expect, it } from 'vitest'
import type { Limit, PlanBudgetCheck, PlanEvaluation, RecommendationResponse, Stack } from '../../api/types.ts'
import { assertNever } from '../../lib/assertNever.ts'
import {
  fixtureA,
  fixtureB,
  fixtureB2,
  fixtureC,
  fixtureD,
  fixtureE,
  fixtureF,
  fixtureG,
  fixtureH,
  fixtureI,
} from './fixtures/recommendationResponses.ts'
import {
  byStatus,
  describeStackBudget,
  evaluationChecks,
  describeCheckDetail,
  formatBudgetLimit,
  formatCheckedAt,
  formatLimit,
  formatSourceLink,
  planLabel,
  planRows,
  stackGroups,
  stackTitle,
} from './resultModel.ts'

function stacksOf(response: RecommendationResponse) {
  return [
    ...response.composition.compatible,
    ...response.composition.unknown,
    ...response.composition.incompatible,
  ]
}

function evaluationsOf(response: RecommendationResponse) {
  return response.roles.flatMap((role) => [
    ...role.compatible,
    ...role.unknown,
    ...role.incompatible,
  ])
}

describe('byStatus', () => {
  it('keeps API order inside a status and skips empty groups', () => {
    const role = fixtureA.roles.find((item) => item.role === 'database')
    expect(role).toBeDefined()
    if (role === undefined) {
      return
    }
    const groups = byStatus(role)
    expect(groups.map((group) => group.status)).toEqual(['compatible'])
    expect(groups[0]?.evaluations[0]).toBe(role.compatible[0])
  })

  it('emits status groups in API status order', () => {
    const role = fixtureG.roles.find((item) => item.role === 'file-uploads')
    expect(role).toBeDefined()
    if (role === undefined) {
      return
    }
    expect(byStatus(role).map((group) => group.status)).toEqual(['compatible', 'incompatible'])
    expect(byStatus(role)[0]?.evaluations[0]).toBe(role.compatible[0])
    expect(byStatus(role)[1]?.evaluations[0]).toBe(role.incompatible[0])
  })

  it('returns no groups when a role has no candidates', () => {
    const role = fixtureB.roles.find((item) => item.role === 'scheduled-jobs')
    expect(role).toBeDefined()
    if (role === undefined) {
      return
    }
    expect(byStatus(role)).toEqual([])
  })
})

describe('stackGroups', () => {
  it('returns the compatible stack from fixture A', () => {
    const groups = stackGroups(fixtureA.composition)
    expect(groups).toHaveLength(1)
    expect(groups[0]?.status).toBe('compatible')
    expect(groups[0]?.stacks).toHaveLength(1)
    expect(groups[0]?.stacks[0]).toBe(fixtureA.composition.compatible[0])
  })

  it('returns the unknown stack from fixture F', () => {
    const groups = stackGroups(fixtureF.composition)
    expect(groups).toHaveLength(1)
    expect(groups[0]?.status).toBe('unknown')
    expect(groups[0]?.stacks).toHaveLength(1)
    expect(groups[0]?.stacks[0]).toBe(fixtureF.composition.unknown[0])
  })

  it('returns groups in evaluation status order', () => {
    const groups = stackGroups(fixtureH.composition)
    expect(groups.map((group) => group.status)).toEqual(['compatible', 'unknown', 'incompatible'])
  })

  it('keeps stack order and object references inside a group', () => {
    const first = fixtureA.composition.compatible[0]
    const second = fixtureD.composition.compatible[0]
    expect(first).toBeDefined()
    expect(second).toBeDefined()
    if (first === undefined || second === undefined) {
      return
    }
    const groups = stackGroups({
      status: 'composed',
      compatible: [first, second],
      unknown: [],
      incompatible: [],
      blocked_roles: [],
      combination_count: 2,
      unevaluated_features: [],
    })
    expect(groups).toHaveLength(1)
    expect(groups[0]?.stacks[0]).toBe(first)
    expect(groups[0]?.stacks[1]).toBe(second)
  })

  it('omits empty status groups', () => {
    const groups = stackGroups(fixtureA.composition)
    expect(groups.map((group) => group.status)).toEqual(['compatible'])
  })

  it('returns no groups for a blocked composition without stacks', () => {
    expect(fixtureB.composition.status).toBe('blocked')
    expect(stackGroups(fixtureB.composition)).toEqual([])
  })
})

describe('planLabel', () => {
  it('joins provider, service, and plan names', () => {
    const detail = fixtureA.plans['supabase-platform-free']
    expect(detail).toBeDefined()
    if (detail === undefined) {
      return
    }
    expect(planLabel(detail, 'supabase-platform-free')).toBe('Supabase · Platform · Free')
    expect(planLabel(null, 'missing-plan')).toBe('missing-plan')
  })
})

describe('describeCheckDetail', () => {
  it('formats a quantity limit without recomputing it', () => {
    const role = fixtureG.roles.find((item) => item.role === 'file-uploads')
    const check = role?.incompatible[0]?.global_quantity_checks.find(
      (item) => item.reason_code === 'exceeds-limit',
    )
    expect(describeCheckDetail(check ?? { reason_code: 'capability-provided', outcome: 'satisfied' })).toBe(
      '대역폭 월 5 GB',
    )
  })

  it('lists other-period limits and leaves an empty quantity check blank', () => {
    const mismatch = fixtureI.roles[0]?.unknown[0]?.global_quantity_checks[0]
    expect(mismatch).toBeDefined()
    if (mismatch !== undefined) {
      expect(describeCheckDetail(mismatch)).toBe('대역폭 일 1 GB')
    }
    const pages = fixtureG.roles.find((item) => item.role === 'static-frontend')
    const missing = pages?.unknown[0]?.global_quantity_checks.find(
      (item) => item.reason_code === 'limit-not-found',
    )
    expect(describeCheckDetail(missing ?? { reason_code: 'capability-provided', outcome: 'satisfied' })).toBeNull()
  })

  it('formats a priced budget and does not turn missing pricing into a price', () => {
    const priced = {
      reason_code: 'within-budget',
      outcome: 'satisfied',
      pricing: {
        plan_id: 'priced-plan',
        monthly_base_fee_usd_cents: 500,
        exceed_behaviors: [],
        source_id: 'source',
      },
    } satisfies PlanBudgetCheck
    expect(describeCheckDetail(priced)).toBe('월 기본 요금 $5')

    const missing = fixtureF.roles[0]?.unknown[0]?.budget_check
    expect(missing?.pricing).toBeNull()
    expect(describeCheckDetail(missing ?? priced)).toBeNull()
    expect(describeCheckDetail(fixtureA.roles[0]?.compatible[0]?.capability_check ?? priced)).toBeNull()
  })
})

describe('planRows', () => {
  it('keeps one row per plan id and the original assignment objects', () => {
    const stack = fixtureA.composition.compatible[0]
    expect(stack).toBeDefined()
    if (stack === undefined) {
      return
    }
    const rows = planRows(stack, fixtureA.plans)
    expect(rows).toHaveLength(1)
    expect(rows[0]?.planId).toBe('supabase-platform-free')
    expect(rows[0]?.detail?.plan.id).toBe(rows[0]?.planId)
    expect(rows[0]?.assignments).toHaveLength(stack.assignments.length)
    expect(rows[0]?.assignments[0]).toBe(stack.assignments[0])
    expect(rows[0]?.assignments.map((assignment) => assignment.feature)).toEqual(
      stack.assignments.map((assignment) => assignment.feature),
    )
  })

  it('follows plan_ids order and does not merge assignment status', () => {
    const stack = {
      key: 'custom',
      assignments: [
        { feature: 'database', plan_id: 'z-plan', status: 'compatible' },
        { feature: 'authentication', plan_id: 'a-plan', status: 'unknown' },
        { feature: 'realtime', plan_id: 'z-plan', status: 'incompatible' },
      ],
      plan_ids: ['z-plan', 'a-plan'],
      status: 'unknown',
      budget_check: null,
    } satisfies Stack
    const rows = planRows(stack, {})
    expect(rows.map((row) => row.planId)).toEqual(['z-plan', 'a-plan'])
    expect(rows[0]?.detail).toBeNull()
    expect(rows[0]?.assignments.map((assignment) => assignment.status)).toEqual([
      'compatible',
      'incompatible',
    ])
    expect(rows[0]?.assignments[0]).toBe(stack.assignments[0])
  })
})

describe('stackTitle', () => {
  it('joins provider and service names in plan_ids order', () => {
    const stack = fixtureA.composition.compatible[0]
    expect(stack).toBeDefined()
    if (stack === undefined) {
      return
    }
    expect(stackTitle(stack, fixtureA.plans)).toBe('Supabase Platform')
  })

  it('uses the plan id when plan details are missing', () => {
    const stack = stacksOf(fixtureG)[0]
    expect(stack).toBeDefined()
    if (stack === undefined) {
      return
    }
    expect(stackTitle(stack, fixtureG.plans)).toBe('Cloudflare Pages + Cloudflare R2')
    expect(stackTitle(stack, {})).toBe(stack.plan_ids.join(' + '))
  })
})

describe('evaluationChecks', () => {
  it('walks capability, role quantity, global quantity, then budget', () => {
    const evaluation = evaluationsOf(fixtureG).find((item) =>
      item.global_quantity_checks.some((check) => check.reason_code === 'exceeds-limit'),
    )
    expect(evaluation).toBeDefined()
    if (evaluation === undefined) {
      return
    }
    const checks = evaluationChecks(evaluation)
    expect(checks.map((check) => check.scope)).toEqual([
      'capability',
      'role-quantity',
      'global-quantity',
    ])
    expect(checks[0]?.check).toBe(evaluation.capability_check)
    expect(checks[1]?.check).toBe(evaluation.quantity_checks[0])
    expect(checks[2]?.check).toBe(evaluation.global_quantity_checks[0])
    expect(checks.map((check) => check.outcome)).toEqual(['satisfied', 'satisfied', 'violated'])
  })

  it('uses the API outcome instead of inferring it from the reason', () => {
    const evaluation = {
      plan_id: 'synthetic-plan',
      role: 'database',
      status: 'unknown',
      capability_check: {
        reason_code: 'exceeds-limit',
        outcome: 'unknown',
      },
      quantity_checks: [],
      global_quantity_checks: [],
      budget_check: null,
    } satisfies PlanEvaluation
    const [check] = evaluationChecks(evaluation)
    expect(check?.reasonCode).toBe('exceeds-limit')
    expect(check?.outcome).toBe('unknown')
  })
})

describe('formatLimit', () => {
  it('formats byte limits with the shared byte formatter', () => {
    expect(
      formatLimit({
        plan_id: 'plan',
        metric: 'database-size-bytes',
        period: 'none',
        value: 500_000_000,
        source_id: 'source',
      }),
    ).toBe('500 MB')
    expect(
      formatLimit({
        plan_id: 'plan',
        metric: 'file-storage-bytes',
        period: 'none',
        value: 1_000_000_000,
        source_id: 'source',
      }),
    ).toBe('1 GB')
    expect(
      formatLimit({
        plan_id: 'plan',
        metric: 'bandwidth-bytes',
        period: 'month',
        value: 5_000_000_000,
        source_id: 'source',
      }),
    ).toBe('월 5 GB')
  })

  it('keeps a null value unlimited and a zero value as zero', () => {
    const unlimited: Limit = {
      plan_id: 'plan',
      metric: 'bandwidth-bytes',
      period: 'month',
      value: null,
      source_id: 'source',
    }
    expect(formatLimit(unlimited)).toBe('월 제한 없음')
    expect(formatLimit({ ...unlimited, period: 'none', value: 0 })).toBe('0 B')
  })

  it('formats requests and build seconds', () => {
    expect(
      formatLimit({
        plan_id: 'plan',
        metric: 'requests',
        period: 'day',
        value: 100_000,
        source_id: 'source',
      }),
    ).toBe('일 100,000회')
    expect(
      formatLimit({
        plan_id: 'plan',
        metric: 'build-seconds',
        period: 'none',
        value: 120,
        source_id: 'source',
      }),
    ).toBe('2분')
    expect(
      formatLimit({
        plan_id: 'plan',
        metric: 'build-seconds',
        period: 'none',
        value: 90,
        source_id: 'source',
      }),
    ).toBe('90초')
  })
})

describe('describeStackBudget', () => {
  it('formats a known within-budget total without recomputing it', () => {
    const check = fixtureH.composition.compatible[0]?.budget_check
    expect(check?.reason).toBe('within-budget')
    if (check === null || check === undefined) {
      return
    }
    expect(describeStackBudget(check)).toEqual({
      budgetText: '$10',
      knownTotalText: '$5',
      partial: false,
      pricedCount: 1,
      unpricedCount: 0,
      reason: 'within-budget',
      outcome: 'satisfied',
    })
  })

  it('keeps an over-budget outcome from the API', () => {
    const check = fixtureH.composition.incompatible[0]?.budget_check
    expect(check?.reason).toBe('over-budget')
    if (check === null || check === undefined) {
      return
    }
    const description = describeStackBudget(check)
    expect(description.knownTotalText).toBe('$20')
    expect(description.outcome).toBe('violated')
    expect(description.reason).toBe('over-budget')
  })

  it('does not present pricing-not-found with a zero known total as a confirmed price', () => {
    const check = fixtureF.composition.unknown[0]?.budget_check
    expect(check).toMatchObject({
      reason: 'pricing-not-found',
      known_total_usd_cents: 0,
      outcome: 'unknown',
    })
    if (check === null || check === undefined) {
      return
    }
    const description = describeStackBudget(check)
    expect(description.knownTotalText).toBeNull()
    expect(description.budgetText).toBe('$0')
    expect(description.partial).toBe(true)
    expect(description.pricedCount).toBe(0)
    expect(description.unpricedCount).toBe(check.unpriced_plan_ids.length)
    expect(description.pricedCount).toBe(check.priced_plan_ids.length)
  })

  it('keeps a synthetic pricing-not-found total unconfirmed', () => {
    const check = fixtureH.composition.unknown[0]?.budget_check
    expect(check?.known_total_usd_cents).toBe(0)
    if (check === null || check === undefined) {
      return
    }
    expect(describeStackBudget(check).knownTotalText).toBeNull()
    expect(describeStackBudget(check).partial).toBe(true)
  })
})

describe('formatBudgetLimit', () => {
  it('distinguishes no budget from a zero budget', () => {
    expect(formatBudgetLimit(null)).toBe('예산 조건 없음')
    expect(formatBudgetLimit(0)).toBe('월 $0 상한')
    expect(formatBudgetLimit(500)).toBe('월 $5 상한')
  })
})

describe('formatCheckedAt', () => {
  it('formats a calendar date without shifting it', () => {
    const source = fixtureA.sources['supabase-billing']
    expect(source?.checked_at).toBe('2026-09-30')
    expect(formatCheckedAt('2026-09-30')).toBe('2026년 9월 30일')
    expect(formatCheckedAt('2026-09-30T00:00:00Z')).toBe('2026-09-30T00:00:00Z')
    expect(formatCheckedAt('not-a-date')).toBe('not-a-date')
  })
})

describe('formatSourceLink', () => {
  it('preserves the source id and http url', () => {
    const source = fixtureA.sources['supabase-billing']
    expect(source?.id).toBe('supabase-billing')
    expect(source?.url).toBe('https://supabase.com/docs/guides/platform/billing-on-supabase')
    expect(formatSourceLink(source?.url ?? '')).toEqual({
      href: 'https://supabase.com/docs/guides/platform/billing-on-supabase',
      text: 'supabase.com/docs/guides/platform/billing-on-supabase',
    })
  })

  it('does not link a non-http url', () => {
    expect(formatSourceLink('javascript:alert(1)')).toEqual({
      href: null,
      text: 'javascript:alert(1)',
    })
    expect(formatSourceLink('not a url')).toEqual({ href: null, text: 'not a url' })
  })
})

describe('recommendation fixtures', () => {
  it('keeps blocked responses free of stacks', () => {
    expect(fixtureB.composition.status).toBe('blocked')
    expect(fixtureB.composition.blocked_roles).toEqual([
      { feature: 'scheduled-jobs', reason: 'no-candidates' },
    ])
    expect(stacksOf(fixtureB)).toEqual([])
    expect(fixtureB2.composition.status).toBe('blocked')
    expect(fixtureB2.composition.blocked_roles).toEqual([
      { feature: 'authentication', reason: 'all-incompatible' },
      { feature: 'realtime', reason: 'all-incompatible' },
    ])
    expect(stacksOf(fixtureB2)).toEqual([])
  })

  it('keeps ai-api unevaluated instead of incompatible', () => {
    expect(fixtureC.composition.status).toBe('no-roles')
    expect(fixtureC.unevaluated_features).toEqual(['ai-api'])
    expect(fixtureC.composition.unevaluated_features).toEqual(['ai-api'])
    expect(fixtureC.roles).toEqual([])
    expect(fixtureC.composition.blocked_roles).toEqual([])
    expect(fixtureD.composition.status).toBe('composed')
    expect(fixtureD.unevaluated_features).toEqual(['ai-api'])
    expect(evaluationsOf(fixtureD).some((evaluation) => evaluation.role === 'ai-api')).toBe(false)
    expect(evaluationsOf(fixtureD).some((evaluation) => evaluation.status === 'incompatible')).toBe(
      false,
    )
  })

  it('records too many combinations without stacks', () => {
    expect(fixtureE.composition.status).toBe('too-many-combinations')
    expect(fixtureE.composition.combination_count).toBe(12)
    expect(stacksOf(fixtureE)).toEqual([])
  })

  it('includes mixed limit reasons and a period mismatch', () => {
    const reasons = evaluationsOf(fixtureG).flatMap((evaluation) =>
      evaluationChecks(evaluation).map((check) => check.reasonCode),
    )
    expect(reasons).toContain('within-limit')
    expect(reasons).toContain('exceeds-limit')
    expect(reasons).toContain('limit-period-mismatch')
    const mismatch = evaluationsOf(fixtureI)[0]?.global_quantity_checks[0]
    expect(mismatch?.reason_code).toBe('limit-period-mismatch')
    expect(mismatch?.reason_code).not.toBe('limit-not-found')
    expect(mismatch?.limit).toBeNull()
    expect(mismatch?.other_period_limits[0]?.period).toBe('day')
    expect(mismatch?.other_period_limits[0]?.metric).toBe('bandwidth-bytes')
    if (mismatch?.other_period_limits[0] !== undefined) {
      expect(formatLimit(mismatch.other_period_limits[0])).toBe('일 1 GB')
    }
  })
})

describe('assertNever', () => {
  it('throws for a value that should have been unreachable', () => {
    const value: never = JSON.parse('"future"') as never
    expect(() => assertNever(value)).toThrow('Unexpected value: future')
  })
})
