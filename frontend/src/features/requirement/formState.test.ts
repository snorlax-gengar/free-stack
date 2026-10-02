import { describe, expect, it } from 'vitest'
import { formReducer, initialFormValues, type RequirementFormValues } from './formState.ts'

describe('formReducer', () => {
  it('starts with empty features, amounts, and budget', () => {
    expect(initialFormValues).toEqual({
      features: [],
      quantities: {
        fileStorage: { amount: '', unit: 'MB' },
        databaseSize: { amount: '', unit: 'MB' },
        monthlyBandwidth: { amount: '', unit: 'GB' },
      },
      bandwidthRange: null,
      budgetAmount: '',
      budgetCurrency: 'USD',
    })
  })

  it('toggles a feature on and off', () => {
    const selected = formReducer(initialFormValues, { type: 'toggleFeature', feature: 'database' })
    expect(selected.features).toEqual(['database'])

    const cleared = formReducer(selected, { type: 'toggleFeature', feature: 'database' })
    expect(cleared.features).toEqual([])
  })

  it('allows backend-server and backend-functions together', () => {
    const state = formReducer(
      formReducer(initialFormValues, { type: 'toggleFeature', feature: 'backend-server' }),
      { type: 'toggleFeature', feature: 'backend-functions' },
    )
    expect(state.features).toEqual(['backend-server', 'backend-functions'])
  })

  it('applies a quantity preset and unit change, then clears back to the default unit', () => {
    const preset = formReducer(initialFormValues, {
      type: 'applyQuantityPreset',
      key: 'databaseSize',
      amount: '1',
      unit: 'GB',
    })
    expect(preset.quantities.databaseSize).toEqual({ amount: '1', unit: 'GB' })

    const changed = formReducer(preset, {
      type: 'setQuantityUnit',
      key: 'databaseSize',
      unit: 'MB',
    })
    expect(changed.quantities.databaseSize.unit).toBe('MB')

    const typed = formReducer(changed, {
      type: 'setQuantityAmount',
      key: 'databaseSize',
      amount: '500',
    })
    const cleared = formReducer(typed, { type: 'clearQuantity', key: 'databaseSize' })
    expect(cleared.quantities.databaseSize).toEqual({ amount: '', unit: 'MB' })
  })

  it('keeps a quantity after the related feature is unchecked', () => {
    let state: RequirementFormValues = formReducer(initialFormValues, {
      type: 'toggleFeature',
      feature: 'database',
    })
    state = formReducer(state, {
      type: 'applyQuantityPreset',
      key: 'databaseSize',
      amount: '500',
      unit: 'MB',
    })
    state = formReducer(state, { type: 'toggleFeature', feature: 'database' })

    expect(state.features).toEqual([])
    expect(state.quantities.databaseSize).toEqual({ amount: '500', unit: 'MB' })

    state = formReducer(state, { type: 'toggleFeature', feature: 'database' })
    expect(state.quantities.databaseSize).toEqual({ amount: '500', unit: 'MB' })
  })

  it('sets, presets, and clears budget independently', () => {
    const typed = formReducer(initialFormValues, { type: 'setBudget', amount: '4' })
    const preset = formReducer(typed, { type: 'applyBudgetPreset', amount: '10' })
    expect(preset.budgetAmount).toBe('10')
    expect(formReducer(preset, { type: 'clearBudget' }).budgetAmount).toBe('')
  })

  it('clears the budget amount when the currency changes', () => {
    const typed = formReducer(initialFormValues, { type: 'setBudget', amount: '10' })
    const won = formReducer(typed, { type: 'setBudgetCurrency', currency: 'KRW' })
    expect(won.budgetCurrency).toBe('KRW')
    expect(won.budgetAmount).toBe('')
  })

  it('selects a bandwidth range and clears it', () => {
    const selected = formReducer(initialFormValues, { type: 'setBandwidthRange', range: 'over-5' })
    expect(selected.bandwidthRange).toBe('over-5')
    expect(formReducer(selected, { type: 'setBandwidthRange', range: null }).bandwidthRange).toBe(null)
  })
})
