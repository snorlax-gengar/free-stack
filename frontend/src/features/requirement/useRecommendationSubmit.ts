import { useCallback, useEffect, useRef, useState } from 'react'
import type { RecommendationRequest, RecommendationResponse } from '../../api/types.ts'
import { postRecommendation } from '../../api/recommendations.ts'
import { isAbortError } from './submitError.ts'

export type SubmitState =
  | { status: 'idle' }
  | { status: 'submitting'; request: RecommendationRequest }
  | { status: 'success'; request: RecommendationRequest; response: RecommendationResponse }
  | { status: 'error'; request: RecommendationRequest; error: unknown }

export function useRecommendationSubmit(): {
  state: SubmitState
  submit: (request: RecommendationRequest) => Promise<void>
} {
  const [state, setState] = useState<SubmitState>({ status: 'idle' })
  const abortRef = useRef<AbortController | null>(null)
  const submittingRef = useRef(false)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      abortRef.current?.abort()
    }
  }, [])

  const submit = useCallback(async (request: RecommendationRequest) => {
    if (submittingRef.current) {
      return
    }
    submittingRef.current = true
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setState({ status: 'submitting', request })
    try {
      const response = await postRecommendation(request, { signal: controller.signal })
      if (!mountedRef.current || controller.signal.aborted) {
        return
      }
      setState({ status: 'success', request, response })
    } catch (error) {
      if (!mountedRef.current) {
        return
      }
      if (isAbortError(error) || controller.signal.aborted) {
        if (abortRef.current === controller) {
          setState({ status: 'idle' })
        }
        return
      }
      setState({ status: 'error', request, error })
    } finally {
      if (abortRef.current === controller) {
        submittingRef.current = false
      }
    }
  }, [])

  return { state, submit }
}
