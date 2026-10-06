import { useState } from 'react'
import type { PlanDetail, Stack } from '../../api/types.ts'
import { KNOWN_CAVEAT_KOREAN } from './caveatSummaries.ts'
import styles from './RecommendationResult.module.css'

export type StackCaveatsCalloutProps = {
  stack: Stack
  plans: Readonly<Record<string, PlanDetail>>
}

type ExtractedCaveat = {
  key: string
  serviceName: string
  koreanSummary: string
  originalStatement: string
}

export function StackCaveatsCallout({ stack, plans }: StackCaveatsCalloutProps) {
  const [expanded, setExpanded] = useState(false)

  const caveats: ExtractedCaveat[] = []
  for (const id of stack.plan_ids) {
    const detail = plans[id]
    if (!detail) {
      continue
    }
    const serviceName = `${detail.provider.name} ${detail.service.name}`
    for (let index = 0; index < detail.caveats.length; index++) {
      const c = detail.caveats[index]!
      caveats.push({
        key: `${id}-${index}`,
        serviceName,
        koreanSummary: KNOWN_CAVEAT_KOREAN[c.statement] ?? c.statement,
        originalStatement: c.statement,
      })
    }
  }

  if (caveats.length === 0) {
    return null
  }

  const initialVisibleCount = 3
  const visibleCaveats = expanded ? caveats : caveats.slice(0, initialVisibleCount)
  const hasMore = caveats.length > initialVisibleCount

  return (
    <div className={styles.caveatsCallout} aria-label="무료 티어 제약 및 주의사항">
      <div className={styles.caveatsHeader}>
        <span className={styles.caveatsIcon} aria-hidden="true">⚠️</span>
        <p className={styles.caveatsTitle}>
          무료 티어 핵심 제약 & 주의사항 <span className={styles.caveatsCount}>({caveats.length}개 팩트체크)</span>
        </p>
      </div>
      <ul className={styles.caveatsList}>
        {visibleCaveats.map((c) => (
          <li key={c.key} className={styles.caveatsItem}>
            <span className={styles.caveatsBadge}>{c.serviceName}</span>
            <span className={styles.caveatsSummary}>{c.koreanSummary}</span>
          </li>
        ))}
      </ul>
      {hasMore ? (
        <button
          type="button"
          className={styles.caveatsToggleButton}
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
        >
          {expanded ? '주의사항 접기 ▲' : `+ 주의사항 ${caveats.length - initialVisibleCount}개 더 보기 ▼`}
        </button>
      ) : null}
    </div>
  )
}
