import { useReducer, useState, type FormEvent } from 'react'
import { featureValues } from '../../api/schema.gen.ts'
import type { RecommendationRequest } from '../../api/types.ts'
import { featureDescriptions, featureLabels } from '../../labels/features.ts'
import { AmountField } from './AmountField.tsx'
import {
  BANDWIDTH_RANGES,
  BUDGET_PRESETS,
  QUANTITY_FIELDS,
  formReducer,
  initialFormValues,
  type BandwidthRangeId,
  type BudgetCurrency,
  type QuantityKey,
} from './formState.ts'
import styles from './RequirementForm.module.css'
import { submitErrorMessage } from './submitError.ts'
import { toRecommendationRequest, type RequestField } from './toRecommendationRequest.ts'

export type RequirementFormProps = {
  submitting: boolean
  error: unknown
  onSubmit: (request: RecommendationRequest) => void
}

export function RequirementForm({ submitting, error, onSubmit }: RequirementFormProps) {
  const [values, dispatch] = useReducer(formReducer, initialFormValues)
  const [errors, setErrors] = useState<readonly { field: RequestField; message: string }[]>([])

  function messageFor(field: RequestField): string | undefined {
    return errors.find((error) => error.field === field)?.message
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) {
      return
    }
    const result = toRecommendationRequest(values)
    if (!result.ok) {
      setErrors(result.errors)
      focusField(result.errors[0]?.field)
      return
    }
    setErrors([])
    onSubmit(result.request)
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      <div className={styles.hero}>
        <p className={styles.heroTitle}>내 프로젝트에 필요한 기능을 선택하세요.</p>
        <p className={styles.heroText}>조건을 입력하면 적합한 인프라 조합을 찾아드립니다.</p>
      </div>
      <div className={styles.card}>
        <fieldset className={styles.group}>
          <legend className={styles.legend}>1. 필요한 기능</legend>
          {messageFor('features') ? <p className={styles.error}>오류: {messageFor('features')}</p> : null}
          <div className={styles.features}>
            {featureValues.map((feature) => {
              const inputId = `feature-${feature}`
              return (
                <label key={feature} className={styles.featureCard} htmlFor={inputId}>
                  <span className={styles.feature}>
                    <input
                      id={inputId}
                      className={styles.checkbox}
                      type="checkbox"
                      checked={values.features.includes(feature)}
                      aria-labelledby={`${inputId}-title`}
                      aria-describedby={`${inputId}-desc`}
                      onChange={() => dispatch({ type: 'toggleFeature', feature })}
                    />
                    <span id={`${inputId}-title`} className={styles.featureText}>
                      {featureLabels[feature]}
                    </span>
                  </span>
                  <span id={`${inputId}-desc`} className={styles.description}>
                    {featureDescriptions[feature]}
                  </span>
                </label>
              )
            })}
          </div>
        </fieldset>
        <fieldset className={styles.group}>
          <legend className={styles.legend}>2. 사용량 조건</legend>
          {QUANTITY_FIELDS.filter(
            (field) => field.feature !== null && values.features.includes(field.feature),
          ).map((field) => (
            <QuantityControl
              key={field.key}
              fieldKey={field.key}
              values={values}
              error={messageFor(field.key)}
              dispatch={dispatch}
            />
          ))}
          <BandwidthRangeField
            range={values.bandwidthRange}
            onChange={(range) => dispatch({ type: 'setBandwidthRange', range })}
          />
        </fieldset>
        <AmountField
            id="budget-amount"
            label="월 예산"
            legendPrefix="3. "
            prefix={values.budgetCurrency === 'KRW' ? '₩' : '$'}
            amount={values.budgetAmount}
            currency={values.budgetCurrency}
            hint={budgetHint(values.budgetCurrency)}
            error={messageFor('budget')}
            presets={BUDGET_PRESETS[values.budgetCurrency]}
            onCurrencyChange={(currency) => dispatch({ type: 'setBudgetCurrency', currency })}
            onAmountChange={(amount) => dispatch({ type: 'setBudget', amount })}
            onPreset={(preset) => dispatch({ type: 'applyBudgetPreset', amount: preset.amount })}
            onClear={() => dispatch({ type: 'clearBudget' })}
          />
        <button className={styles.submit} type="submit" aria-disabled={submitting} aria-busy={submitting}>
          {submitting ? '추천 받는 중…' : '무료 스택 추천받기'}
        </button>
        {submitting ? (
          <p className={styles.status} role="status">
            추천 받는 중…
          </p>
        ) : null}
        {error != null ? (
          <p className={styles.alert} role="alert">
            {submitErrorMessage(error)}
          </p>
        ) : null}
      </div>
    </form>
  )
}

function BandwidthRangeField({
  range,
  onChange,
}: {
  range: BandwidthRangeId | null
  onChange: (range: BandwidthRangeId | null) => void
}) {
  const field = QUANTITY_FIELDS.find((item) => item.key === 'monthlyBandwidth')
  return (
    <fieldset className={styles.amount}>
      <legend id="quantity-monthlyBandwidth-legend" className={styles.subLegend}>
        {field?.label}
      </legend>
      <div className={styles.presets} role="group" aria-labelledby="quantity-monthlyBandwidth-legend">
        {BANDWIDTH_RANGES.map((item) => (
          <button
            key={item.id}
            className={styles.preset}
            type="button"
            aria-pressed={range === item.id}
            onClick={() => onChange(range === item.id ? null : item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <p className={styles.hint}>{field?.hint}</p>
    </fieldset>
  )
}

function budgetHint(currency: BudgetCurrency): string {
  if (currency === 'KRW') {
    return '비워 두면 예산 조건 없이 추천합니다.\n0은 월 0원 상한으로 처리됩니다.\n원화는 1달러 = 1,400원으로 바꿔 비교합니다.'
  }
  return '비워 두면 예산 조건 없이 추천합니다.\n0은 월 $0 상한으로 처리됩니다.'
}

function QuantityControl({
  fieldKey,
  values,
  error,
  dispatch,
}: {
  fieldKey: QuantityKey
  values: typeof initialFormValues
  error: string | undefined
  dispatch: (action: Parameters<typeof formReducer>[1]) => void
}) {
  const field = QUANTITY_FIELDS.find((item) => item.key === fieldKey)
  if (!field) {
    return null
  }
  const quantity = values.quantities[fieldKey]
  return (
    <AmountField
      id={`quantity-${fieldKey}`}
      label={field.label}
      amount={quantity.amount}
      unit={quantity.unit}
      hint={field.hint}
      error={error}
      presets={field.presets}
      onAmountChange={(amount) => dispatch({ type: 'setQuantityAmount', key: fieldKey, amount })}
      onUnitChange={(unit) => dispatch({ type: 'setQuantityUnit', key: fieldKey, unit })}
      onPreset={(preset) =>
        dispatch({
          type: 'applyQuantityPreset',
          key: fieldKey,
          amount: preset.amount,
          unit: preset.unit ?? quantity.unit,
        })
      }
      onClear={() => dispatch({ type: 'clearQuantity', key: fieldKey })}
    />
  )
}

function focusField(field: RequestField | undefined) {
  const id =
    field === 'budget'
      ? 'budget-amount'
      : field === 'features' || field === undefined
        ? 'feature-static-frontend'
        : `quantity-${field}`
  document.getElementById(id)?.focus()
}
