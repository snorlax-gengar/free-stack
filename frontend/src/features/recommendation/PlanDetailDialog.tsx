import { useEffect, useId, useRef } from 'react'
import type { PlanDetail, Source } from '../../api/types.ts'
import { formatUsdCents } from '../../lib/money.ts'
import {
  capabilityKeyLabels,
  exceedBehaviorLabels,
  labelOf,
} from '../../labels/recommendation.ts'
import { formatCheckedAt, formatSourceLink, planLabel, sourceElementId, sourceNumber } from './resultModel.ts'
import { SourceCitation } from './SourceCitation.tsx'
import styles from './RecommendationResult.module.css'

export type PlanDetailDialogProps = {
  detail: PlanDetail
  onClose: () => void
  focusSourceId?: string | null
}

export function PlanDetailDialog({ detail, onClose, focusSourceId = null }: PlanDetailDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  // close() removes `open` before the close event, and StrictMode reopens the dialog
  // before that event runs. The flag stays set until the event so a cleanup close
  // is not treated as the user dismissing the dialog.
  const closedByCleanup = useRef(false)
  const detailRef = useRef(detail)
  const focusSourceIdRef = useRef(focusSourceId)
  const titleId = useId()
  const label = planLabel(detail, detail.plan.id)

  useEffect(() => {
    const dialog = dialogRef.current
    const previous = document.activeElement
    if (dialog !== null && !dialog.open) {
      dialog.showModal()
    }
    closeButtonRef.current?.focus()
    focusRequestedSource(detailRef.current, focusSourceIdRef.current)
    return () => {
      if (dialog !== null && dialog.open) {
        closedByCleanup.current = true
        dialog.close()
      }
      if (previous instanceof HTMLElement && previous.isConnected) {
        previous.focus()
      }
    }
  }, [])

  function handleClose() {
    if (closedByCleanup.current) {
      closedByCleanup.current = false
      return
    }
    onClose()
  }

  return (
    <dialog
      ref={dialogRef}
      role="dialog"
      aria-labelledby={titleId}
      className={styles.dialog}
      onClose={handleClose}
    >
      <div className={styles.dialogHeader}>
        <h2 id={titleId} className={styles.dialogTitle}>
          {label}
        </h2>
        <button
          ref={closeButtonRef}
          type="button"
          className={styles.detailButton}
          onClick={() => dialogRef.current?.close()}
        >
          닫기
        </button>
      </div>
      <div className={styles.dialogBody}>
      <section className={styles.dialogSection}>
        <h3 className={styles.dialogHeading}>제공자</h3>
        <p lang="en">{detail.provider.name}</p>
        <p lang="en">{detail.provider.description}</p>
        <h3 className={styles.dialogHeading}>서비스</h3>
        <p lang="en">{detail.service.name}</p>
        <p lang="en">{detail.service.description}</p>
        <h3 className={styles.dialogHeading}>플랜</h3>
        <p lang="en">{detail.plan.name}</p>
        <p lang="en">{detail.plan.description}</p>
      </section>
      <section className={styles.dialogSection}>
        <h3 className={styles.dialogHeading}>제공 기능</h3>
        <ul className={styles.dialogList} aria-label="제공 기능">
          {detail.plan.capabilities.map((capability) => (
            <li key={capability}>{labelOf(capability, capabilityKeyLabels)}</li>
          ))}
        </ul>
      </section>
      <section className={styles.dialogSection}>
        <h3 className={styles.dialogHeading}>가격</h3>
        {detail.pricing === null ? (
          <>
            <p>가격 정보 없음</p>
            <p>이 플랜의 가격 정보가 아직 등록되지 않았습니다.</p>
          </>
        ) : (
          <>
            <p>
              월 기본 요금 {formatUsdCents(detail.pricing.monthly_base_fee_usd_cents)}
              <SourceCitation planId={detail.plan.id} sources={detail.sources} sourceId={detail.pricing.source_id} />
            </p>
            {detail.pricing.exceed_behaviors.length === 0 ? null : (
              <p>
                사용량을 넘으면:{' '}
                {detail.pricing.exceed_behaviors
                  .map((behavior) => labelOf(behavior, exceedBehaviorLabels))
                  .join(' · ')}
              </p>
            )}
          </>
        )}
      </section>
      <section className={styles.dialogSection}>
        <h3 className={styles.dialogHeading}>주의사항 ({detail.caveats.length})</h3>
        {detail.caveats.length === 0 ? (
          <p>등록된 주의사항이 없습니다.</p>
        ) : (
          <ul className={styles.dialogList} aria-label="주의사항">
            {detail.caveats.map((caveat, index) => (
              <li key={`${caveat.source_id}-${index}`} lang="en">
                {caveat.statement}
                <SourceCitation planId={detail.plan.id} sources={detail.sources} sourceId={caveat.source_id} />
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className={styles.dialogSection}>
        <h3 className={styles.dialogHeading}>이 결과에 사용된 출처</h3>
        {detail.sources.length === 0 ? (
          <p>출처 정보가 없습니다.</p>
        ) : (
          <ol className={styles.sources} aria-label="이 결과에 사용된 출처">
            {detail.sources.map((source, index) => (
              <SourceItem key={source.id} source={source} id={sourceElementId(detail.plan.id, index + 1)} />
            ))}
          </ol>
        )}
      </section>
      </div>
    </dialog>
  )
}

function focusRequestedSource(detail: PlanDetail, sourceId: string | null) {
  if (sourceId === null) {
    return
  }
  const number = sourceNumber(detail.sources, sourceId)
  if (number === null) {
    return
  }
  const target = document.getElementById(sourceElementId(detail.plan.id, number))
  if (!(target instanceof HTMLElement)) {
    return
  }
  if (typeof target.scrollIntoView === 'function') {
    target.scrollIntoView({ block: 'nearest' })
  }
  target.focus()
}

function SourceItem({ source, id }: { source: Source; id: string }) {
  const link = formatSourceLink(source.url)
  return (
    <li id={id} tabIndex={-1}>
      {link.href === null ? (
        <span className={styles.sourceLink}>{link.text}</span>
      ) : (
        <a className={styles.sourceLink} href={link.href} target="_blank" rel="noopener noreferrer">
          {link.text}
          <span className={styles.srOnly}> (새 탭에서 열림)</span>
        </a>
      )}
      <p>확인일 {formatCheckedAt(source.checked_at)}</p>
      {source.notes === '' ? null : <p lang="en">{source.notes}</p>}
    </li>
  )
}
