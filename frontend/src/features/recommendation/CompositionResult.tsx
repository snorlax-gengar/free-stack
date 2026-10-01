import type { Composition, PlanDetail, RecommendationResponse } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import { evaluationStatusLabels, labelOf, reasonCodeLabels } from '../../labels/recommendation.ts'
import {
  describeStackBudget,
  planRows,
  stackGroups,
  stackTitle,
  type PlanRow,
} from './resultModel.ts'
import styles from './RecommendationResult.module.css'

export type CompositionResultProps = {
  composition: Composition
  plans: RecommendationResponse['plans']
}

export function CompositionResult({ composition, plans }: CompositionResultProps) {
  const groups = stackGroups(composition)
  const stackCount = groups.reduce((count, group) => count + group.stacks.length, 0)

  return (
    <div className={styles.composition}>
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
                <p className={styles.status}>{labelOf(stack.status, evaluationStatusLabels)}</p>
                <ul className={styles.plans} aria-label="플랜">
                  {planRows(stack, plans).map((row) => (
                    <PlanRowView key={row.planId} row={row} />
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

function PlanRowView({ row }: { row: PlanRow }) {
  const features = row.assignments.map((assignment) => featureLabels[assignment.feature]).join(' · ')
  return (
    <li className={styles.plan}>
      <PlanIdentity detail={row.detail} planId={row.planId} />
      <p className={styles.features}>{features}</p>
    </li>
  )
}

function PlanIdentity({ detail, planId }: { detail: PlanDetail | null; planId: string }) {
  if (detail === null) {
    return <p className={styles.planId}>{planId}</p>
  }
  return (
    <>
      <p>{detail.provider.name}</p>
      <p>{detail.service.name}</p>
      <p>{detail.plan.name}</p>
    </>
  )
}
