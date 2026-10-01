import { useEffect, useId, useRef } from 'react'
import type { RecommendationResponse } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import { compositionStatusLabels, labelOf, limitMetricLabels } from '../../labels/recommendation.ts'
import { formatBytes } from '../../lib/units.ts'
import { assertNever } from '../../lib/assertNever.ts'
import { formatBudgetLimit } from './resultModel.ts'
import { CompositionResult } from './CompositionResult.tsx'
import styles from './RecommendationResult.module.css'

export type RecommendationResultProps = {
  response: RecommendationResponse
}

export function RecommendationResult({ response }: RecommendationResultProps) {
  const headingRef = useRef<HTMLHeadingElement>(null)
  const headingId = useId()
  const { requirement } = response

  useEffect(() => {
    headingRef.current?.focus()
  }, [])

  return (
    <section className={styles.result} aria-labelledby={headingId}>
      <h2 id={headingId} ref={headingRef} tabIndex={-1} className={styles.heading}>
        추천 결과
      </h2>
      <div className={styles.requirement}>
        <ul className={styles.featureList} aria-label="선택한 기능">
          {requirement.features.map((feature) => (
            <li key={feature}>{featureLabels[feature]}</li>
          ))}
        </ul>
        <QuantityLine metric="file-storage-bytes" bytes={requirement.file_storage_bytes} />
        <QuantityLine metric="database-size-bytes" bytes={requirement.database_size_bytes} />
        <QuantityLine metric="bandwidth-bytes" bytes={requirement.monthly_bandwidth_bytes} />
        <p>{formatBudgetLimit(requirement.monthly_budget_usd_cents)}</p>
      </div>
      {renderComposition(response)}
    </section>
  )
}

function QuantityLine({
  metric,
  bytes,
}: {
  metric: 'file-storage-bytes' | 'database-size-bytes' | 'bandwidth-bytes'
  bytes: number | null
}) {
  if (bytes === null) {
    return null
  }
  return (
    <p>
      {limitMetricLabels[metric]} {formatBytes(bytes)}
    </p>
  )
}

function renderComposition(response: RecommendationResponse) {
  switch (response.composition.status) {
    case 'composed':
      return (
        <>
          <CompositionResult composition={response.composition} plans={response.plans} />
          <UnevaluatedFeatures features={response.unevaluated_features} />
        </>
      )
    case 'blocked':
    case 'too-many-combinations':
    case 'no-roles':
      return <p>{labelOf(response.composition.status, compositionStatusLabels)}</p>
    default:
      return assertNever(response.composition.status)
  }
}

function UnevaluatedFeatures({ features }: { features: RecommendationResponse['unevaluated_features'] }) {
  if (features.length === 0) {
    return null
  }
  const names = features.map((feature) => featureLabels[feature]).join(', ')
  return <p>평가되지 않은 기능: {names}</p>
}
