import type { QuantityUnit } from '../../lib/units.ts'
import styles from './RequirementForm.module.css'

type Preset = {
  label: string
  amount: string
  unit?: QuantityUnit
}

type AmountFieldProps = {
  id: string
  label: string
  legendPrefix?: string
  amount: string
  hint: string
  error?: string
  prefix?: string
  unit?: QuantityUnit
  presets: readonly Preset[]
  onAmountChange: (amount: string) => void
  onUnitChange?: (unit: QuantityUnit) => void
  onPreset: (preset: Preset) => void
  onClear: () => void
}

export function AmountField({
  id,
  label,
  legendPrefix,
  amount,
  hint,
  error,
  prefix,
  unit,
  presets,
  onAmountChange,
  onUnitChange,
  onPreset,
  onClear,
}: AmountFieldProps) {
  const legendId = `${id}-legend`
  const hintId = `${id}-hint`
  const errorId = `${id}-error`
  const describedBy = error ? `${hintId} ${errorId}` : hintId

  return (
    <fieldset className={styles.amount}>
      <legend>
        {legendPrefix ? <span aria-hidden="true">{legendPrefix}</span> : null}
        <span id={legendId}>{label}</span>
      </legend>
      <div className={styles.amountRow}>
        {prefix ? (
          <span className={styles.prefix} aria-hidden="true">
            {prefix}
          </span>
        ) : null}
        <input
          id={id}
          className={styles.input}
          type="text"
          inputMode="numeric"
          value={amount}
          aria-labelledby={legendId}
          aria-describedby={describedBy}
          aria-invalid={error ? true : undefined}
          onChange={(event) => onAmountChange(event.target.value)}
        />
        {unit && onUnitChange ? (
          <>
            <label className={styles.unitLabel} htmlFor={`${id}-unit`}>
              {label} 단위
            </label>
            <select
              id={`${id}-unit`}
              className={styles.input}
              value={unit}
              onChange={(event) => onUnitChange(event.target.value as QuantityUnit)}
            >
              <option value="MB">MB</option>
              <option value="GB">GB</option>
            </select>
          </>
        ) : null}
      </div>
      <div className={styles.presets}>
        {presets.map((preset) => (
          <button
            key={preset.label}
            className={styles.preset}
            type="button"
            onClick={() => onPreset(preset)}
          >
            {preset.label}
          </button>
        ))}
        <button className={styles.preset} type="button" onClick={onClear}>
          지우기
        </button>
      </div>
      <p id={hintId} className={styles.hint}>
        {hint}
      </p>
      {error ? (
        <p id={errorId} className={styles.error}>
          오류: {error}
        </p>
      ) : null}
    </fieldset>
  )
}
