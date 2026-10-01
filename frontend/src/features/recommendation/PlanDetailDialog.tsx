import { useEffect, useId, useRef } from 'react'
import type { PlanDetail, Source } from '../../api/types.ts'
import { formatUsdCents } from '../../lib/money.ts'
import {
  capabilityKeyLabels,
  exceedBehaviorLabels,
  labelOf,
} from '../../labels/recommendation.ts'
import { formatCheckedAt, formatSourceLink, planLabel, sourceNumber } from './resultModel.ts'
import styles from './RecommendationResult.module.css'

export type PlanDetailDialogProps = {
  detail: PlanDetail
  onClose: () => void
}

export function PlanDetailDialog({ detail, onClose }: PlanDetailDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const ignoreClose = useRef(false)
  const titleId = useId()
  const sourcePrefix = `source${useId().replaceAll(':', '')}`
  const label = planLabel(detail, detail.plan.id)

  useEffect(() => {
    const dialog = dialogRef.current
    const previous = document.activeElement
    if (dialog !== null && !dialog.open) {
      dialog.showModal()
    }
    return () => {
      if (dialog !== null && dialog.open) {
        ignoreClose.current = true
        dialog.close()
        ignoreClose.current = false
      }
      if (previous instanceof HTMLElement && previous.isConnected) {
        previous.focus()
      }
    }
  }, [])

  function handleClose() {
    if (ignoreClose.current) {
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
      <button type="button" className={styles.detailButton} onClick={() => dialogRef.current?.close()}>
        닫기
      </button>
      <h2 id={titleId} className={styles.dialogTitle}>
        {label}
      </h2>
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
              <SourceCitation sources={detail.sources} sourceId={detail.pricing.source_id} prefix={sourcePrefix} />
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
                <SourceCitation sources={detail.sources} sourceId={caveat.source_id} prefix={sourcePrefix} />
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
              <SourceItem key={source.id} source={source} id={`${sourcePrefix}-${index + 1}`} />
            ))}
          </ol>
        )}
      </section>
    </dialog>
  )
}

function SourceCitation({
  sources,
  sourceId,
  prefix,
}: {
  sources: Source[]
  sourceId: string
  prefix: string
}) {
  const number = sourceNumber(sources, sourceId)
  if (number === null) {
    return null
  }
  return (
    <>
      {' '}
      <a href={`#${prefix}-${number}`}>[출처 {number}]</a>
    </>
  )
}

function SourceItem({ source, id }: { source: Source; id: string }) {
  const link = formatSourceLink(source.url)
  return (
    <li id={id}>
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
