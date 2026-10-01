import type { Composition, RecommendationResponse } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import { evaluationStatusLabels, labelOf, reasonCodeLabels } from '../../labels/recommendation.ts'
import {
  describeStackBudget,
  planLabel,
  planRows,
  stackGroups,
  stackTitle,
  type PlanRow,
} from './resultModel.ts'
import { StatusBadge } from './StatusBadge.tsx'
import styles from './RecommendationResult.module.css'

export type CompositionResultProps = {
  composition: Composition
  plans: RecommendationResponse['plans']
  onOpenPlan: (planId: string) => void
}

export function CompositionResult({ composition, plans, onOpenPlan }: CompositionResultProps) {
  const groups = stackGroups(composition)
  const stackCount = groups.reduce((count, group) => count + group.stacks.length, 0)

  return (
    <div className={styles.composition} role="region" aria-label="구성">
      <p className={styles.summary}>
        조합 {stackCount}개를 구성했습니다. 표시 순서는 순위가 아닙니다.
      </p>
      {groups.map((group) => (
        <section key={group.status} className={styles.group}>
          <h3 className={styles.groupTitle}>
            {labelOf(group.status, evaluationStatusLabels)} ({group.stacks.length})
          </h3>
          {group.stacks.map((stack) => {
            const budget = stack.budget_check === null ? null : describeStackBudget(stack.budget_check)
            return (
              <article key={stack.key} className={styles.stack}>
                <h4 className={styles.stackTitle}>{stackTitle(stack, plans)}</h4>
                <StatusBadge status={stack.status} />
                <ul className={styles.plans} aria-label="플랜">
                  {planRows(stack, plans).map((row) => (
                    <PlanRowView key={row.planId} row={row} onOpenPlan={onOpenPlan} />
                  ))}
                </ul>
                {budget === null ? null : (
                  <div className={styles.budget}>
                    <p>예산 {budget.budgetText}</p>
                    {budget.knownTotalText === null ? null : <p>확인된 합계 {budget.knownTotalText}</p>}
                    <p>{labelOf(budget.reason, reasonCodeLabels)}</p>
                  </div>
                )}
              </article>
            )
          })}
        </section>
      ))}
    </div>
  )
}

function PlanRowView({ row, onOpenPlan }: { row: PlanRow; onOpenPlan: (planId: string) => void }) {
  const label = planLabel(row.detail, row.planId)
  return (
    <li className={styles.plan}>
      <div className={styles.planIdentity}>
        <p>{label}</p>
        {row.detail === null ? null : (
          <button
            type="button"
            className={styles.detailButton}
            aria-label={`${label} 상세 보기`}
            onClick={() => onOpenPlan(row.planId)}
          >
            상세 보기
          </button>
        )}
      </div>
      <ul className={styles.assignments} aria-label="배정된 기능">
        {row.assignments.map((assignment) => (
          <li key={assignment.feature} className={styles.assignment}>
            <span>{featureLabels[assignment.feature]}</span>
            <StatusBadge status={assignment.status} />
          </li>
        ))}
      </ul>
    </li>
  )
}
