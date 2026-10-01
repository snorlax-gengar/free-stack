import type { EvaluationStatus } from '../../api/types.ts'
import { evaluationStatusLabels, labelOf } from '../../labels/recommendation.ts'
import styles from './RecommendationResult.module.css'

export type StatusBadgeProps = {
  status: EvaluationStatus
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span className={styles.badge} data-status={status}>
      {labelOf(status, evaluationStatusLabels)}
    </span>
  )
}
