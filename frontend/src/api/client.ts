export type HealthResponse = {
  status: string
}

export type ApiErrorKind = 'network' | 'http' | 'unexpected-response'

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly code: string | null

  constructor(kind: ApiErrorKind, status: number | null, code: string | null, message: string) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
    this.code = code
  }
}

function getApiBaseUrl(): string {
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  if (!baseUrl) {
    throw new Error('VITE_API_BASE_URL is not set')
  }
  return baseUrl.replace(/\/$/, '')
}

function isAbortError(error: unknown): boolean {
  return typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError'
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function readErrorBody(body: unknown): { code: string; message: string } | null {
  if (!isRecord(body)) {
    return null
  }
  const error = body.error
  if (!isRecord(error)) {
    return null
  }
  const { code, message } = error
  if (typeof code !== 'string' || typeof message !== 'string') {
    return null
  }
  return { code, message }
}

async function errorFromResponse(response: Response): Promise<ApiError> {
  try {
    const body: unknown = await response.json()
    const error = readErrorBody(body)
    if (error) {
      return new ApiError('http', response.status, error.code, error.message)
    }
  } catch (error) {
    if (isAbortError(error)) {
      throw error
    }
  }
  return new ApiError(
    'unexpected-response',
    response.status,
    null,
    'The response did not match the API error contract',
  )
}

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${getApiBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`
  let response: Response
  try {
    response = await fetch(url, init)
  } catch (error) {
    if (isAbortError(error)) {
      throw error
    }
    throw new ApiError('network', null, null, 'The network request failed')
  }

  if (!response.ok) {
    throw await errorFromResponse(response)
  }

  try {
    return (await response.json()) as T
  } catch (error) {
    if (isAbortError(error)) {
      throw error
    }
    throw new ApiError('unexpected-response', response.status, null, 'The response was not JSON')
  }
}

export async function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/health')
}
