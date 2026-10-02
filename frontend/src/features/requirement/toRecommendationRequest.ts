import { featureValues } from '../../api/schema.gen.ts'
import type { RecommendationRequest } from '../../api/types.ts'
import { wholeKrwToUsdCents, wholeUsdToCents } from '../../lib/money.ts'
import { toBytes } from '../../lib/units.ts'
import {
  BANDWIDTH_RANGES,
  QUANTITY_FIELDS,
  type QuantityKey,
  type RequirementFormValues,
} from './formState.ts'

export type RequestField = 'features' | QuantityKey | 'budget'

export type RequestErrorCode = 'required-feature' | 'not-integer' | 'not-positive' | 'too-large'

export type RequestError = {
  code: RequestErrorCode
  field: RequestField
  message: string
}

export type ToRequestResult =
  | { ok: true; request: RecommendationRequest }
  | { ok: false; errors: readonly RequestError[] }

const NOT_INTEGER_QUANTITY =
  '0보다 큰 정수로 입력해 주세요. 소수는 더 작은 단위로 바꿔 주세요(1.5 GB → 1500 MB).'
const NOT_POSITIVE_QUANTITY = '0보다 큰 값을 입력해 주세요. 조건이 없으면 비워 두세요.'
const TOO_LARGE = '입력할 수 있는 범위를 넘었습니다.'
const REQUIRED_FEATURE = '필요한 기능을 하나 이상 선택해 주세요.'
const NOT_INTEGER_BUDGET = '0 이상의 정수로 입력해 주세요.'

export function toRecommendationRequest(values: RequirementFormValues): ToRequestResult {
  const errors: RequestError[] = []
  const selected = new Set(values.features)
  const features = featureValues.filter((feature) => selected.has(feature))
  if (features.length === 0) {
    errors.push({ code: 'required-feature', field: 'features', message: REQUIRED_FEATURE })
  }

  const request: RecommendationRequest = {
    features,
    file_storage_bytes: null,
    database_size_bytes: null,
    monthly_bandwidth_bytes: null,
    monthly_budget_usd_cents: null,
  }

  for (const field of QUANTITY_FIELDS) {
    if (field.key === 'monthlyBandwidth' || (field.feature !== null && !selected.has(field.feature))) {
      continue
    }
    const parsed = parseQuantity(values.quantities[field.key].amount, values.quantities[field.key].unit)
    if (parsed.ok) {
      request[field.requestKey] = parsed.value
    } else if (parsed.empty) {
      request[field.requestKey] = null
    } else {
      errors.push({ code: parsed.code, field: field.key, message: parsed.message })
    }
  }

  const range = BANDWIDTH_RANGES.find((item) => item.id === values.bandwidthRange)
  request.monthly_bandwidth_bytes = range === undefined ? null : toBytes(range.gigabytes, 'GB')

  const budget = parseBudget(values.budgetAmount, values.budgetCurrency)
  if (budget.ok) {
    request.monthly_budget_usd_cents = budget.value
  } else if (!budget.empty) {
    errors.push({ code: budget.code, field: 'budget', message: budget.message })
  }

  if (errors.length > 0) {
    return { ok: false, errors }
  }
  return { ok: true, request }
}

function parseQuantity(
  amount: string,
  unit: RequirementFormValues['quantities'][QuantityKey]['unit'],
):
  | { ok: true; value: number | null; empty: boolean }
  | { ok: false; empty: false; code: Exclude<RequestErrorCode, 'required-feature'>; message: string } {
  const text = amount.trim()
  if (text === '') {
    return { ok: true, value: null, empty: true }
  }
  if (!/^[0-9]+$/.test(text)) {
    return { ok: false, empty: false, code: 'not-integer', message: NOT_INTEGER_QUANTITY }
  }
  const value = Number(text)
  if (!Number.isSafeInteger(value)) {
    return { ok: false, empty: false, code: 'too-large', message: TOO_LARGE }
  }
  if (value <= 0) {
    return { ok: false, empty: false, code: 'not-positive', message: NOT_POSITIVE_QUANTITY }
  }
  try {
    return { ok: true, value: toBytes(value, unit), empty: false }
  } catch {
    return { ok: false, empty: false, code: 'too-large', message: TOO_LARGE }
  }
}

function parseBudget(
  amount: string,
  currency: RequirementFormValues['budgetCurrency'],
):
  | { ok: true; value: number | null; empty: boolean }
  | { ok: false; empty: false; code: 'not-integer' | 'too-large'; message: string } {
  const text = amount.trim()
  if (text === '') {
    return { ok: true, value: null, empty: true }
  }
  if (!/^[0-9]+$/.test(text)) {
    return { ok: false, empty: false, code: 'not-integer', message: NOT_INTEGER_BUDGET }
  }
  const whole = Number(text)
  if (!Number.isSafeInteger(whole)) {
    return { ok: false, empty: false, code: 'too-large', message: TOO_LARGE }
  }
  try {
    const cents = currency === 'KRW' ? wholeKrwToUsdCents(whole) : wholeUsdToCents(whole)
    return { ok: true, value: cents, empty: false }
  } catch {
    return { ok: false, empty: false, code: 'too-large', message: TOO_LARGE }
  }
}
