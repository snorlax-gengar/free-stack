import { useReducer, useState, type FormEvent } from 'react'
import { featureValues } from '../../api/schema.gen.ts'
import { featureDescriptions, featureLabels } from '../../labels/features.ts'
import { AmountField } from './AmountField.tsx'
import {
  BUDGET_PRESETS,
  QUANTITY_FIELDS,
  formReducer,
  initialFormValues,
  type QuantityKey,
} from './formState.ts'
import styles from './RequirementForm.module.css'
import { submitErrorMessage } from './submitError.ts'
import { toRecommendationRequest, type RequestField } from './toRecommendationRequest.ts'
import { useRecommendationSubmit } from './useRecommendationSubmit.ts'

export function RequirementForm() {
  const [values, dispatch] = useReducer(formReducer, initialFormValues)
  const [errors, setErrors] = useState<readonly { field: RequestField; message: string }[]>([])
  const submission = useRecommendationSubmit()
  const submitting = submission.state.status === 'submitting'

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
    void submission.submit(result.request)
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
          <QuantityControl
            fieldKey="monthlyBandwidth"
            values={values}
            error={messageFor('monthlyBandwidth')}
            dispatch={dispatch}
          />
        </fieldset>
        <AmountField
            id="budget-amount"
            label="월 예산 (USD)"
            legendPrefix="3. "
            prefix="$"
            amount={values.budgetUsd}
            hint={'비워 두면 예산 조건 없이 추천합니다.\n0은 월 $0 상한으로 처리됩니다.'}
            error={messageFor('budget')}
            presets={BUDGET_PRESETS}
            onAmountChange={(amount) => dispatch({ type: 'setBudget', amount })}
            onPreset={(preset) => dispatch({ type: 'applyBudgetPreset', amount: preset.amount })}
            onClear={() => dispatch({ type: 'clearBudget' })}
          />
        <button className={styles.submit} type="submit" aria-disabled={submitting} aria-busy={submitting}>
          {submitting ? '추천 받는 중…' : '무료 스택 추천받기'}
        </button>
        {submission.state.status === 'submitting' ? (
          <p className={styles.status} role="status">
            추천 받는 중…
          </p>
        ) : null}
        {submission.state.status === 'success' ? (
          <p className={styles.status} role="status">
            추천 결과를 받았습니다.
          </p>
        ) : null}
        {submission.state.status === 'error' ? (
          <p className={styles.alert} role="alert">
            {submitErrorMessage(submission.state.error)}
          </p>
        ) : null}
      </div>
    </form>
  )
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
