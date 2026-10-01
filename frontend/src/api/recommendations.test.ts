import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from './client.ts'
import { postRecommendation } from './recommendations.ts'
import type { RecommendationRequest, RecommendationResponse } from './types.ts'

const request = {
  features: ['database'],
  database_size_bytes: null,
  monthly_budget_usd_cents: 0,
} satisfies RecommendationRequest

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

function mockFetch(response: Response): ReturnType<typeof vi.fn> {
  vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
  const fetchMock = vi.fn(async () => response)
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('postRecommendation', () => {
  it('posts the request without changing null or zero', async () => {
    const fetchMock = mockFetch(Response.json(composedResponse()))

    await postRecommendation(request)

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/v1/recommendations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: undefined,
    })
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toEqual(request)
  })

  it('returns a successful recommendation', async () => {
    const body = composedResponse()
    mockFetch(Response.json(body))

    await expect(postRecommendation(request)).resolves.toEqual(body)
  })

  it('resolves a blocked composition', async () => {
    const body = composedResponse()
    body.composition.status = 'blocked'
    body.composition.blocked_roles = [{ feature: 'database', reason: 'all-incompatible' }]
    mockFetch(Response.json(body))

    const result = await postRecommendation(request)

    expect(result.composition.status).toBe('blocked')
  })

  it.each(['REQUEST_VALIDATION_FAILED', 'INVALID_REQUIREMENT'] as const)(
    'preserves %s from a 422 response',
    async (code) => {
      mockFetch(Response.json({ error: { code, message: 'rejected' } }, { status: 422 }))

      const error = await postRecommendation(request).catch((caught: unknown) => caught)

      expect(error).toBeInstanceOf(ApiError)
      expect(error).toMatchObject({ kind: 'http', status: 422, code, message: 'rejected' })
    },
  )

  it('preserves an internal error', async () => {
    mockFetch(
      Response.json(
        { error: { code: 'INTERNAL_ERROR', message: 'An internal error occurred.' } },
        { status: 500 },
      ),
    )

    const error = await postRecommendation(request).catch((caught: unknown) => caught)

    expect(error).toMatchObject({
      kind: 'http',
      status: 500,
      code: 'INTERNAL_ERROR',
      message: 'An internal error occurred.',
    })
  })
})

function composedResponse(): RecommendationResponse {
  return {
    requirement: {
      features: ['database'],
      file_storage_bytes: null,
      database_size_bytes: null,
      monthly_bandwidth_bytes: null,
      monthly_budget_usd_cents: 0,
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
