import type { MouseEvent } from 'react'
import type { Source } from '../../api/types.ts'
import { sourceElementId, sourceNumber } from './resultModel.ts'

export type SourceCitationProps = {
  planId: string
  sources: Source[]
  sourceId: string
  onUnavailable?: (planId: string, sourceId: string) => void
}

export function SourceCitation({ planId, sources, sourceId, onUnavailable }: SourceCitationProps) {
  const number = sourceNumber(sources, sourceId)
  if (number === null) {
    return null
  }
  const id = sourceElementId(planId, number)
  return (
    <>
      {' '}
      <a
        href={`#${id}`}
        onClick={(event) => {
          focusCitedSource(event)
          if (document.getElementById(id) === null) {
            onUnavailable?.(planId, sourceId)
          }
        }}
      >
        [출처 {number}]
      </a>
    </>
  )
}

function focusCitedSource(event: MouseEvent<HTMLAnchorElement>) {
  event.preventDefault()
  const href = event.currentTarget.getAttribute('href')
  if (href === null || !href.startsWith('#')) {
    return
  }
  const target = document.getElementById(href.slice(1))
  if (!(target instanceof HTMLElement)) {
    return
  }
  if (typeof target.scrollIntoView === 'function') {
    target.scrollIntoView({ block: 'nearest' })
  }
  target.focus()
}
