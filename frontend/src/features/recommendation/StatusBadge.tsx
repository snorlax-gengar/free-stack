import { Badge, type BadgeVariant } from 'gengarileo-design-system'
import type { EvaluationStatus } from '../../api/types.ts'
import { evaluationStatusLabels, labelOf } from '../../labels/recommendation.ts'
import styles from './RecommendationResult.module.css'

export type StatusBadgeProps = {
  status: EvaluationStatus
}

const statusBadgeVariantMap: Record<EvaluationStatus, BadgeVariant> = {
  compatible: 'sky',
  unknown: 'butter',
  incompatible: 'coral',
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge
      variant={statusBadgeVariantMap[status] ?? 'slate'}
      size="sm"
      dot={true}
      className={styles.badge}
      data-status={status}
    >
      {labelOf(status, evaluationStatusLabels)}
    </Badge>
  )
}
