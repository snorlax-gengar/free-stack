import { useEffect, useId, useRef, useState } from 'react'
import type { Composition, RecommendationResponse } from '../../api/types.ts'
import { featureLabels } from '../../labels/features.ts'
import {
  blockReasonLabels,
  compositionStatusLabels,
  labelOf,
  limitMetricLabels,
} from '../../labels/recommendation.ts'
import { formatBytes } from '../../lib/units.ts'
import { assertNever } from '../../lib/assertNever.ts'
import { formatBudgetLimit } from './resultModel.ts'
import { CompositionResult } from './CompositionResult.tsx'
import { PlanDetailDialog } from './PlanDetailDialog.tsx'
import { RoleEvaluations } from './RoleEvaluations.tsx'
import styles from './RecommendationResult.module.css'

export type RecommendationResultProps = {
  response: RecommendationResponse
}

export function RecommendationResult({ response }: RecommendationResultProps) {
  const headingRef = useRef<HTMLHeadingElement>(null)
  const headingId = useId()
  const [openPlanId, setOpenPlanId] = useState<string | null>(null)
  const [focusSourceId, setFocusSourceId] = useState<string | null>(null)
  const { requirement } = response
  const openDetail = openPlanId === null ? undefined : response.plans[openPlanId]

  useEffect(() => {
    headingRef.current?.focus()
  }, [])

  function openPlan(planId: string) {
    setFocusSourceId(null)
    setOpenPlanId(planId)
  }

  function openPlanSource(planId: string, sourceId: string) {
    setFocusSourceId(sourceId)
    setOpenPlanId(planId)
  }

  return (
    <section className={styles.result} aria-labelledby={headingId}>
      <h2 id={headingId} ref={headingRef} tabIndex={-1} className={styles.heading}>
        추천 결과
      </h2>
      <RequestSummary requirement={requirement} />
      <CompositionSection response={response} onOpenPlan={openPlan} />
      <UnevaluatedFeatures features={response.unevaluated_features} />
      {response.roles.length > 0 ? (
        <RoleEvaluations
          roles={response.roles}
          plans={response.plans}
          onOpenPlan={openPlan}
          onOpenPlanSource={openPlanSource}
          initiallyOpenRoles={response.composition.blocked_roles.map((role) => role.feature)}
        />
      ) : null}
      {openDetail === undefined ? null : (
        <PlanDetailDialog
          detail={openDetail}
          focusSourceId={focusSourceId}
          onClose={() => {
            setOpenPlanId(null)
            setFocusSourceId(null)
          }}
        />
      )}
    </section>
  )
}

function RequestSummary({ requirement }: { requirement: RecommendationResponse['requirement'] }) {
  const headingId = useId()
  return (
    <section className={styles.requirement} aria-labelledby={headingId}>
      <h3 id={headingId} className={styles.groupTitle}>
        요청 조건
      </h3>
      <ul className={styles.conditionList}>
        <li>
          <p className={styles.conditionLabel}>기능</p>
          <ul className={styles.featureList} aria-label="선택한 기능">
            {requirement.features.map((feature) => (
              <li key={feature}>{featureLabels[feature]}</li>
            ))}
          </ul>
        </li>
        <QuantityLine metric="file-storage-bytes" bytes={requirement.file_storage_bytes} />
        <QuantityLine metric="database-size-bytes" bytes={requirement.database_size_bytes} />
        <QuantityLine metric="bandwidth-bytes" bytes={requirement.monthly_bandwidth_bytes} />
        <li>
          <p>{formatBudgetLimit(requirement.monthly_budget_usd_cents)}</p>
        </li>
      </ul>
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
    <li>
      <p>
        {limitMetricLabels[metric]} {formatBytes(bytes)}
      </p>
    </li>
  )
}

function CompositionSection({
  response,
  onOpenPlan,
}: {
  response: RecommendationResponse
  onOpenPlan: (planId: string) => void
}) {
  const headingId = useId()
  return (
    <section className={styles.composition} aria-labelledby={headingId}>
      <h3 id={headingId} className={styles.groupTitle}>
        조합
      </h3>
      {renderComposition(response, onOpenPlan)}
    </section>
  )
}

function renderComposition(response: RecommendationResponse, onOpenPlan: (planId: string) => void) {
  switch (response.composition.status) {
    case 'composed':
      return <CompositionResult composition={response.composition} plans={response.plans} onOpenPlan={onOpenPlan} />
    case 'blocked':
      return <BlockedComposition composition={response.composition} />
    case 'too-many-combinations':
      return <TooManyCombinations count={response.composition.combination_count} />
    case 'no-roles':
      return <NoRoles />
    default:
      return assertNever(response.composition.status)
  }
}

function BlockedComposition({ composition }: { composition: Composition }) {
  const headingId = useId()
  return (
    <div className={styles.statusNote}>
      <h4 id={headingId} className={styles.statusTitle}>
        {labelOf('blocked', compositionStatusLabels)}
      </h4>
      <p>다음 역할에서 사용 가능한 플랜을 찾지 못했습니다.</p>
      {composition.blocked_roles.length === 0 ? null : (
        <ul className={styles.statusList} aria-label="막힌 역할">
          {composition.blocked_roles.map((role) => (
            <li key={role.feature}>
              <p>{featureLabels[role.feature]}</p>
              <p>{labelOf(role.reason, blockReasonLabels)}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function TooManyCombinations({ count }: { count: number }) {
  const headingId = useId()
  const formatted = formatCombinationCount(count)
  return (
    <div className={styles.statusNote}>
      <h4 id={headingId} className={styles.statusTitle}>
        {labelOf('too-many-combinations', compositionStatusLabels)}
      </h4>
      {formatted === null ? null : (
        <p>
          현재 조건에서 {formatted}개의 조합이 만들어질 수 있어 모든 조합을 표시하지 않았습니다.
        </p>
      )}
    </div>
  )
}

function formatCombinationCount(count: number): string | null {
  if (!Number.isSafeInteger(count) || count < 0) {
    return null
  }
  return count.toLocaleString('ko-KR')
}

function NoRoles() {
  const headingId = useId()
  return (
    <div className={styles.statusNote}>
      <h4 id={headingId} className={styles.statusTitle}>
        {labelOf('no-roles', compositionStatusLabels)}
      </h4>
      <p>선택한 기능 중 현재 추천 엔진에서 평가하는 기능이 없습니다.</p>
    </div>
  )
}

function UnevaluatedFeatures({ features }: { features: RecommendationResponse['unevaluated_features'] }) {
  const headingId = useId()
  if (features.length === 0) {
    return null
  }
  return (
    <section className={styles.statusNote} aria-labelledby={headingId}>
      <h3 id={headingId} className={styles.groupTitle}>
        평가하지 않은 기능
      </h3>
      <ul className={styles.statusList} aria-label="평가하지 않은 기능">
        {features.map((feature) => (
          <li key={feature}>{featureLabels[feature]}</li>
        ))}
      </ul>
    </section>
  )
}
