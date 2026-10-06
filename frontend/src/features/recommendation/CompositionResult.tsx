import type { Composition, RecommendationResponse } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import { evaluationStatusLabels, labelOf, reasonCodeLabels } from '../../labels/recommendation.ts'
import { ProviderIcon } from './ProviderIcon.tsx'
import {
  describeStackBudget,
  planLabel,
  planRows,
  stackGroups,
  stackTitle,
  type PlanRow,
} from './resultModel.ts'
import { getStackGuidance } from './stackGuidance.ts'
import { StackCaveatsCallout } from './StackCaveatsCallout.tsx'
import { CopyAiPromptButton } from './CopyAiPromptButton.tsx'
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
    <>
      <p className={styles.summary}>
        조합 {stackCount}개를 구성했습니다. 표시 순서는 순위가 아닙니다.
      </p>
      {groups.map((group) => (
        <section key={group.status} className={styles.group} aria-label={labelOf(group.status, evaluationStatusLabels)}>
          <p className={styles.groupLabel}>
            {labelOf(group.status, evaluationStatusLabels)} ({group.stacks.length})
          </p>
          {group.stacks.map((stack) => {
            const budget = stack.budget_check === null ? null : describeStackBudget(stack.budget_check)
            const guidance = getStackGuidance(stack, plans)
            const providers = Array.from(
              new Set(
                stack.plan_ids
                  .map((id) => plans[id]?.provider.id)
                  .filter((id): id is string => Boolean(id)),
              ),
            )
            return (
              <article key={stack.key} className={styles.stack}>
                <div className={styles.stackHeader}>
                  <div className={styles.stackHeaderLeft}>
                    {providers.length > 0 ? (
                      <div className={styles.stackProviderIcons} aria-hidden="true">
                        {providers.map((pId) => (
                          <span key={pId} className={styles.stackProviderChip}>
                            <ProviderIcon providerId={pId} size="sm" />
                          </span>
                        ))}
                      </div>
                    ) : null}
                    <h4 className={styles.stackTitle}>{stackTitle(stack, plans)}</h4>
                  </div>
                  <StatusBadge status={stack.status} />
                </div>
                {guidance.tags.length > 0 ? (
                  <div className={styles.stackTagList} aria-label="조합 특징">
                    {guidance.tags.map((tag) => (
                      <span key={tag} className={styles.stackTag}>
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : null}
                <p className={styles.stackGuidanceText}>{guidance.description}</p>
                <ul className={styles.plans} aria-label="플랜">
                  {planRows(stack, plans).map((row) => (
                    <PlanRowView key={row.planId} row={row} onOpenPlan={onOpenPlan} />
                  ))}
                </ul>
                <StackCaveatsCallout stack={stack} plans={plans} />
                {budget === null ? null : (
                  <div className={styles.budget}>
                    <p>예산 {budget.budgetText}</p>
                    {budget.knownTotalText === null ? null : <p>확인된 합계 {budget.knownTotalText}</p>}
                    <p>{labelOf(budget.reason, reasonCodeLabels)}</p>
                  </div>
                )}
                <CopyAiPromptButton stack={stack} plans={plans} />
              </article>
            )
          })}
        </section>
      ))}
    </>
  )
}

function PlanRowView({ row, onOpenPlan }: { row: PlanRow; onOpenPlan: (planId: string) => void }) {
  const label = planLabel(row.detail, row.planId)
  const providerId = row.detail?.provider.id
  return (
    <li className={styles.plan}>
      <div className={styles.planIdentity}>
        <div className={styles.planNameGroup}>
          <span className={styles.planIconWrapper}>
            <ProviderIcon providerId={providerId} size="md" />
          </span>
          <p>{label}</p>
        </div>
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
