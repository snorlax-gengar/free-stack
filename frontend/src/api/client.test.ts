import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, getHealth, requestJson } from './client.ts'

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('API base URL', () => {
  it.each(['http://localhost:8000/', 'http://localhost:8000'])(
    'joins %s without a double slash',
    async (baseUrl) => {
      vi.stubEnv('VITE_API_BASE_URL', baseUrl)
      const fetchMock = vi.fn(async () => Response.json({ status: 'ok' }))
      vi.stubGlobal('fetch', fetchMock)

      await getHealth()

      expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/health', undefined)
    },
  )

  it('throws when the base URL is missing', async () => {
    vi.stubEnv('VITE_API_BASE_URL', '')

    await expect(getHealth()).rejects.toThrow('VITE_API_BASE_URL is not set')
  })
})

describe('requestJson', () => {
  it('returns a network error when fetch rejects', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(new TypeError('offline'))))

    await expect(requestJson('/health')).rejects.toMatchObject({
      name: 'ApiError',
      kind: 'network',
      status: null,
      code: null,
    })
  })

  it('rethrows an abort error', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
    const abortError = new DOMException('The operation was aborted.', 'AbortError')
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(abortError)))

    await expect(requestJson('/health')).rejects.toBe(abortError)
  })

  it('reports a non-JSON error response', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('<html>bad gateway</html>', { status: 502 })),
    )

    await expect(requestJson('/health')).rejects.toMatchObject({
      kind: 'unexpected-response',
      status: 502,
      code: null,
    })
  })

  it('reads an API error body', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:8000')
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          Response.json(
            { error: { code: 'INVALID_REQUIREMENT', message: 'invalid features' } },
            { status: 422 },
          ),
      ),
    )

    const error = await requestJson('/health').catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      kind: 'http',
      status: 422,
      code: 'INVALID_REQUIREMENT',
      message: 'invalid features',
    })
  })
})
