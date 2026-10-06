import { useId } from 'react'
import type { RecommendationResponse, RoleEvaluation } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import {
  checkOutcomeLabels,
  evaluationStatusLabels,
  labelOf,
  reasonCodeLabels,
} from '../../labels/recommendation.ts'
import {
  byStatus,
  checkSourceIds,
  describeCheckDetail,
  evaluationChecks,
  planLabel,
  type CheckScope,
  type EvaluationCheck,
} from './resultModel.ts'
import { SourceCitation } from './SourceCitation.tsx'
import { StatusBadge } from './StatusBadge.tsx'
import { ProviderIcon } from './ProviderIcon.tsx'
import styles from './RecommendationResult.module.css'

const scopeLabels = {
  capability: '기능',
  'role-quantity': '이 역할의 사용량',
  'global-quantity': '공통 사용량',
  budget: '예산',
} satisfies Record<CheckScope, string>

export type RoleEvaluationsProps = {
  roles: RoleEvaluation[]
  plans: RecommendationResponse['plans']
  onOpenPlan: (planId: string) => void
  onOpenPlanSource: (planId: string, sourceId: string) => void
  initiallyOpenRoles?: readonly RoleEvaluation['role'][]
}

export function RoleEvaluations({
  roles,
  plans,
  onOpenPlan,
  onOpenPlanSource,
  initiallyOpenRoles = [],
}: RoleEvaluationsProps) {
  const openRoles = new Set(initiallyOpenRoles)
  const headingId = useId()

  return (
    <section className={styles.roles} aria-labelledby={headingId}>
      <h3 id={headingId} className={styles.groupTitle}>
        역할별 후보 평가
      </h3>
      <p className={styles.summary}>충족·확인 필요·미충족은 순위가 아니라 평가 상태입니다.</p>
      {roles.map((role) => {
        const groups = byStatus(role)
        return (
          <details
            key={role.role}
            className={styles.role}
            {...(openRoles.has(role.role) ? { open: true } : {})}
          >
            <summary className={styles.roleSummary}>{roleSummary(role, groups)}</summary>
            {groups.length === 0 ? (
              <p>사용 가능한 후보가 없습니다.</p>
            ) : groups.map((group) => (
              <div key={group.status} className={styles.candidateGroup}>
                <h4 className={styles.stackTitle}>
                  {labelOf(group.status, evaluationStatusLabels)} ({group.evaluations.length})
                </h4>
                <ul className={styles.candidates}>
                  {group.evaluations.map((evaluation) => {
                    const detail = plans[evaluation.plan_id]
                    const label = planLabel(detail ?? null, evaluation.plan_id)
                    const providerId = detail?.provider.id
                    return (
                    <li key={evaluation.plan_id} className={styles.candidate}>
                      <div className={styles.planIdentity}>
                        <div className={styles.planNameGroup}>
                          <span className={styles.planIconWrapper}>
                            <ProviderIcon providerId={providerId} size="md" />
                          </span>
                          <p>{label}</p>
                        </div>
                        {detail === undefined ? null : (
                          <button
                            type="button"
                            className={styles.detailButton}
                            aria-label={`${label} 상세 보기`}
                            onClick={() => onOpenPlan(evaluation.plan_id)}
                          >
                            상세 보기
                          </button>
                        )}
                      </div>
                      <StatusBadge status={evaluation.status} />
                      <ul className={styles.checks}>
                        {evaluationChecks(evaluation).map((item, index) => (
                          <li key={`${item.scope}-${index}`}>
                            {formatCheck(item)}
                            {checkSourceIds(item.check).map((sourceId) => (
                              <SourceCitation
                                key={sourceId}
                                planId={evaluation.plan_id}
                                sources={detail?.sources ?? []}
                                sourceId={sourceId}
                                onUnavailable={onOpenPlanSource}
                              />
                            ))}
                          </li>
                        ))}
                      </ul>
                    </li>
                    )
                  })}
                </ul>
              </div>
            ))}
          </details>
        )
      })}
    </section>
  )
}

function roleSummary(
  role: RoleEvaluation,
  groups: ReturnType<typeof byStatus>,
): string {
  const name = featureLabels[role.role]
  if (groups.length === 0) {
    return `${name} — 평가된 후보가 없습니다`
  }
  const counts = groups
    .map((group) => `${labelOf(group.status, evaluationStatusLabels)} ${group.evaluations.length}`)
    .join(' · ')
  return `${name} — ${counts}`
}

function formatCheck(item: EvaluationCheck): string {
  const detail = describeCheckDetail(item.check)
  const reason = labelOf(item.reasonCode, reasonCodeLabels)
  const tail = detail === null ? reason : `${detail} · ${reason}`
  return `${scopeLabels[item.scope]}: ${labelOf(item.outcome, checkOutcomeLabels)} — ${tail}`
}
