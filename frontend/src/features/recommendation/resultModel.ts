import { evaluationStatusValues } from '../../api/schema.gen.ts'
import type {
  Assignment,
  Check,
  CheckOutcome,
  Composition,
  EvaluationStatus,
  Limit,
  PlanBudgetCheck,
  PlanDetail,
  PlanEvaluation,
  QuantityCheck,
  ReasonCode,
  RoleEvaluation,
  Stack,
  StackBudgetCheck,
} from '../../api/types.ts'
import { limitPeriodLabels } from '../../labels/recommendation.ts'
import { assertNever } from '../../lib/assertNever.ts'
import { formatUsdCents } from '../../lib/money.ts'
import { formatBytes } from '../../lib/units.ts'

export type StatusGroup = {
  status: EvaluationStatus
  evaluations: PlanEvaluation[]
}

export function byStatus(role: RoleEvaluation): StatusGroup[] {
  const evaluationsByStatus = {
    compatible: role.compatible,
    unknown: role.unknown,
    incompatible: role.incompatible,
  } satisfies Record<EvaluationStatus, PlanEvaluation[]>

  return evaluationStatusValues.flatMap((status) => {
    const evaluations = evaluationsByStatus[status]
    if (evaluations === undefined || evaluations.length === 0) {
      return []
    }
    return [{ status, evaluations }]
  })
}

export type StackGroup = {
  status: EvaluationStatus
  stacks: Stack[]
}

export function stackGroups(composition: Composition): StackGroup[] {
  const stacksByStatus = {
    compatible: composition.compatible,
    unknown: composition.unknown,
    incompatible: composition.incompatible,
  } satisfies Record<EvaluationStatus, Stack[]>

  return evaluationStatusValues.flatMap((status) => {
    const stacks = stacksByStatus[status]
    if (stacks === undefined || stacks.length === 0) {
      return []
    }
    return [{ status, stacks }]
  })
}

export type PlanRow = {
  planId: string
  detail: PlanDetail | null
  assignments: Assignment[]
}

export function planRows(stack: Stack, plans: Readonly<Record<string, PlanDetail>>): PlanRow[] {
  return stack.plan_ids.map((planId) => ({
    planId,
    detail: plans[planId] ?? null,
    assignments: stack.assignments.filter((assignment) => assignment.plan_id === planId),
  }))
}

export function stackTitle(stack: Stack, plans: Readonly<Record<string, PlanDetail>>): string {
  return stack.plan_ids
    .map((planId) => {
      const detail = plans[planId]
      if (detail === undefined) {
        return planId
      }
      return `${detail.provider.name} ${detail.service.name}`
    })
    .join(' + ')
}

export type CheckScope = 'capability' | 'role-quantity' | 'global-quantity' | 'budget'

export type EvaluationCheck = {
  scope: CheckScope
  outcome: CheckOutcome
  reasonCode: ReasonCode
  check: Check | QuantityCheck | PlanBudgetCheck
}

export function evaluationChecks(evaluation: PlanEvaluation): EvaluationCheck[] {
  const checks: EvaluationCheck[] = [
    {
      scope: 'capability',
      outcome: evaluation.capability_check.outcome,
      reasonCode: evaluation.capability_check.reason_code,
      check: evaluation.capability_check,
    },
  ]
  for (const check of evaluation.quantity_checks) {
    checks.push({
      scope: 'role-quantity',
      outcome: check.outcome,
      reasonCode: check.reason_code,
      check,
    })
  }
  for (const check of evaluation.global_quantity_checks) {
    checks.push({
      scope: 'global-quantity',
      outcome: check.outcome,
      reasonCode: check.reason_code,
      check,
    })
  }
  if (evaluation.budget_check !== null) {
    checks.push({
      scope: 'budget',
      outcome: evaluation.budget_check.outcome,
      reasonCode: evaluation.budget_check.reason_code,
      check: evaluation.budget_check,
    })
  }
  return checks
}

export function formatLimit(limit: Limit): string {
  const valueText = formatLimitValue(limit)
  const period = limitPeriodLabels[limit.period]
  if (period === undefined || period === '') {
    return valueText
  }
  return `${period} ${valueText}`
}

function formatLimitValue(limit: Limit): string {
  if (limit.value === null) {
    return '제한 없음'
  }
  switch (limit.metric) {
    case 'file-storage-bytes':
    case 'database-size-bytes':
    case 'bandwidth-bytes':
      return formatBytes(limit.value)
    case 'requests':
      return `${limit.value.toLocaleString('en-US')}회`
    case 'build-seconds':
      return formatBuildSeconds(limit.value)
    default:
      return assertNever(limit.metric)
  }
}

function formatBuildSeconds(seconds: number): string {
  if (seconds % 60 === 0) {
    return `${(seconds / 60).toLocaleString('en-US')}분`
  }
  return `${seconds.toLocaleString('en-US')}초`
}

export type StackBudgetDescription = {
  budgetText: string
  knownTotalText: string | null
  partial: boolean
  pricedCount: number
  unpricedCount: number
  reason: ReasonCode
  outcome: CheckOutcome
}

export function describeStackBudget(check: StackBudgetCheck): StackBudgetDescription {
  const pricedCount = check.priced_plan_ids.length
  const unpricedCount = check.unpriced_plan_ids.length
  const knownTotalText =
    check.reason === 'pricing-not-found' || pricedCount === 0
      ? null
      : formatUsdCents(check.known_total_usd_cents)
  return {
    budgetText: formatUsdCents(check.budget_usd_cents),
    knownTotalText,
    partial: unpricedCount > 0,
    pricedCount,
    unpricedCount,
    reason: check.reason,
    outcome: check.outcome,
  }
}

export function formatBudgetLimit(cents: number | null): string {
  if (cents === null) {
    return '예산 조건 없음'
  }
  if (cents === 0) {
    return '월 $0 상한'
  }
  return `월 ${formatUsdCents(cents)} 상한`
}

const checkedAtPattern = /^(\d{4})-(\d{2})-(\d{2})$/

export function formatCheckedAt(checkedAt: string): string {
  const match = checkedAtPattern.exec(checkedAt)
  if (match === null) {
    return checkedAt
  }
  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return checkedAt
  }
  return `${year}년 ${month}월 ${day}일`
}

export function formatSourceLink(url: string): { href: string | null; text: string } {
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return { href: null, text: url }
    }
    return { href: url, text: `${parsed.host}${parsed.pathname}` }
  } catch {
    return { href: null, text: url }
  }
}
