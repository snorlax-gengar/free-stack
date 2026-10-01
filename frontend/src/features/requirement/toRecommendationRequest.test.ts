import { describe, expect, it } from 'vitest'
import { initialFormValues, type RequirementFormValues } from './formState.ts'
import { toRecommendationRequest } from './toRecommendationRequest.ts'

function values(
  patch: Partial<Omit<RequirementFormValues, 'quantities'>> & {
    quantities?: Partial<RequirementFormValues['quantities']>
  } = {},
): RequirementFormValues {
  return {
    ...initialFormValues,
    ...patch,
    quantities: {
      ...initialFormValues.quantities,
      ...patch.quantities,
    },
  }
}

describe('toRecommendationRequest', () => {
  it('converts 500 MB, 1 GB, and 10 GB with decimal SI units', () => {
    const result = toRecommendationRequest(
      values({
        features: ['database', 'file-uploads'],
        quantities: {
          databaseSize: { amount: '500', unit: 'MB' },
          fileStorage: { amount: '1', unit: 'GB' },
          monthlyBandwidth: { amount: '10', unit: 'GB' },
        },
      }),
    )

    expect(result.ok).toBe(true)
    if (!result.ok) {
      return
    }
    expect(result.request.database_size_bytes).toBe(500_000_000)
    expect(result.request.file_storage_bytes).toBe(1_000_000_000)
    expect(result.request.monthly_bandwidth_bytes).toBe(10_000_000_000)
  })

  it('maps an empty budget to null, zero dollars to 0 cents, and 10 dollars to 1000 cents', () => {
    const empty = toRecommendationRequest(values({ features: ['static-frontend'], budgetUsd: '' }))
    const zero = toRecommendationRequest(values({ features: ['static-frontend'], budgetUsd: '0' }))
    const ten = toRecommendationRequest(values({ features: ['static-frontend'], budgetUsd: '10' }))

    expect(empty.ok && empty.request.monthly_budget_usd_cents).toBe(null)
    expect(zero.ok && zero.request.monthly_budget_usd_cents).toBe(0)
    expect(ten.ok && ten.request.monthly_budget_usd_cents).toBe(1000)
  })

  it('omits an empty quantity and rejects zero, decimals, signs, text, and exponents', () => {
    const empty = toRecommendationRequest(
      values({
        features: ['database'],
        quantities: { databaseSize: { amount: '', unit: 'MB' } },
      }),
    )
    expect(empty.ok && empty.request.database_size_bytes).toBe(null)

    expect(errorCode(values({
      features: ['database'],
      quantities: { databaseSize: { amount: '0', unit: 'MB' } },
    }), 'databaseSize')).toBe('not-positive')

    for (const amount of ['-1', '1.5', 'abc', '1e3']) {
      expect(errorCode(values({
        features: ['database'],
        quantities: { databaseSize: { amount, unit: 'MB' } },
      }), 'databaseSize')).toBe('not-integer')
    }
  })

  it('sends null and no error for a hidden quantity', () => {
    const result = toRecommendationRequest(
      values({
        features: ['static-frontend'],
        quantities: { databaseSize: { amount: '500', unit: 'MB' } },
      }),
    )

    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.request.database_size_bytes).toBe(null)
    }
  })

  it('requires at least one feature', () => {
    const result = toRecommendationRequest(values())
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.errors).toEqual([
        expect.objectContaining({ code: 'required-feature', field: 'features' }),
      ])
    }
  })

  it('orders features by the generated schema declaration', () => {
    const result = toRecommendationRequest(
      values({ features: ['realtime', 'static-frontend'] }),
    )
    expect(result.ok).toBe(true)
    if (result.ok) {
      expect(result.request.features).toEqual(['static-frontend', 'realtime'])
    }
  })

  it('always emits exactly the five request keys', () => {
    const result = toRecommendationRequest(
      values({
        features: ['database'],
        quantities: { databaseSize: { amount: '500', unit: 'MB' } },
      }),
    )
    expect(result.ok).toBe(true)
    if (!result.ok) {
      return
    }
    expect(Object.keys(result.request)).toEqual([
      'features',
      'file_storage_bytes',
      'database_size_bytes',
      'monthly_bandwidth_bytes',
      'monthly_budget_usd_cents',
    ])
    expect(result.request).toEqual({
      features: ['database'],
      file_storage_bytes: null,
      database_size_bytes: 500_000_000,
      monthly_bandwidth_bytes: null,
      monthly_budget_usd_cents: null,
    })
  })
})

function errorCode(input: RequirementFormValues, field: string): string | undefined {
  const result = toRecommendationRequest(input)
  if (result.ok) {
    return undefined
  }
  return result.errors.find((error) => error.field === field)?.code
}
