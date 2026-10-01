import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { RecommendationRequest, RecommendationResponse } from '../../api/types.ts'
import { postRecommendation } from '../../api/recommendations.ts'
import { ApiError } from '../../api/client.ts'
import { useRecommendationSubmit } from './useRecommendationSubmit.ts'

vi.mock('../../api/recommendations.ts', () => ({
  postRecommendation: vi.fn(),
}))

const request = {
  features: ['database'],
  file_storage_bytes: null,
  database_size_bytes: null,
  monthly_bandwidth_bytes: null,
  monthly_budget_usd_cents: null,
} satisfies RecommendationRequest

describe('useRecommendationSubmit', () => {
  afterEach(() => {
    cleanup()
  })

  beforeEach(() => {
    vi.mocked(postRecommendation).mockReset()
  })

  it('stores a successful response with the submitted request', async () => {
    const response = composedResponse()
    vi.mocked(postRecommendation).mockResolvedValue(response)
    const { result } = renderHook(() => useRecommendationSubmit())

    await act(async () => {
      await result.current.submit(request)
    })

    expect(result.current.state).toEqual({ status: 'success', request, response })
  })

  it('treats a blocked business status as success', async () => {
    const response = composedResponse()
    response.composition.status = 'blocked'
    vi.mocked(postRecommendation).mockResolvedValue(response)
    const { result } = renderHook(() => useRecommendationSubmit())

    await act(async () => {
      await result.current.submit(request)
    })

    expect(result.current.state.status).toBe('success')
  })

  it.each([
    ['network', new ApiError('network', null, null, 'offline')],
    ['INVALID_REQUIREMENT', new ApiError('http', 422, 'INVALID_REQUIREMENT', 'raw')],
    ['REQUEST_VALIDATION_FAILED', new ApiError('http', 422, 'REQUEST_VALIDATION_FAILED', 'raw')],
    ['INTERNAL_ERROR', new ApiError('http', 500, 'INTERNAL_ERROR', 'raw')],
  ] as const)('stores %s as an error', async (_label, error) => {
    vi.mocked(postRecommendation).mockRejectedValue(error)
    const { result } = renderHook(() => useRecommendationSubmit())

    await act(async () => {
      await result.current.submit(request)
    })

    expect(result.current.state).toEqual({ status: 'error', request, error })
  })

  it('ignores a second submit while the first is in flight', async () => {
    let resolveRequest: (response: RecommendationResponse) => void = () => {}
    vi.mocked(postRecommendation).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRequest = resolve
        }),
    )
    const { result } = renderHook(() => useRecommendationSubmit())

    await act(async () => {
      void result.current.submit(request)
      void result.current.submit(request)
    })

    expect(postRecommendation).toHaveBeenCalledTimes(1)
    await act(async () => {
      resolveRequest(composedResponse())
    })
  })

  it('aborts the in-flight request on unmount', async () => {
    let signal: AbortSignal | undefined
    vi.mocked(postRecommendation).mockImplementation((_request, options) => {
      signal = options?.signal
      return new Promise(() => {})
    })
    const { result, unmount } = renderHook(() => useRecommendationSubmit())

    await act(async () => {
      void result.current.submit(request)
    })
    unmount()

    expect(signal?.aborted).toBe(true)
  })

  it('does not enter the error state for AbortError', async () => {
    vi.mocked(postRecommendation).mockRejectedValue(new DOMException('stopped', 'AbortError'))
    const { result } = renderHook(() => useRecommendationSubmit())

    await act(async () => {
      await result.current.submit(request)
    })

    expect(result.current.state.status).toBe('idle')
  })
})

function composedResponse(): RecommendationResponse {
  return {
    requirement: {
      features: ['database'],
      file_storage_bytes: null,
      database_size_bytes: null,
      monthly_bandwidth_bytes: null,
      monthly_budget_usd_cents: null,
    },
    roles: [],
    composition: {
      status: 'composed',
      compatible: [],
      unknown: [],
      incompatible: [],
      blocked_roles: [],
      combination_count: 0,
      unevaluated_features: [],
    },
    unevaluated_features: [],
    plans: {},
    sources: {},
  }
}
