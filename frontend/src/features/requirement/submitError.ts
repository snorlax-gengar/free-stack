import { ApiError } from '../../api/client.ts'

const INVALID_REQUIREMENT =
  '선택한 기능과 입력값의 조합을 처리할 수 없습니다. 입력 내용을 확인해 주세요.'
const REQUEST_VALIDATION_FAILED =
  '요청을 처리할 수 없습니다. 입력 내용을 확인한 뒤 다시 시도해 주세요.'
const SERVER_ERROR = '일시적인 서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
const NETWORK_ERROR = '서버에 연결할 수 없습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.'
const UNEXPECTED_ERROR = '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.'

export function isAbortError(error: unknown): boolean {
  return typeof error === 'object' && error !== null && 'name' in error && error.name === 'AbortError'
}

export function submitErrorMessage(error: unknown): string | null {
  if (isAbortError(error)) {
    return null
  }
  if (import.meta.env.DEV) {
    console.error(error)
  }
  if (!(error instanceof ApiError)) {
    return UNEXPECTED_ERROR
  }
  if (error.kind === 'network') {
    return NETWORK_ERROR
  }
  if (error.kind === 'http' && error.code === 'INVALID_REQUIREMENT') {
    return INVALID_REQUIREMENT
  }
  if (error.kind === 'http' && error.code === 'REQUEST_VALIDATION_FAILED') {
    return REQUEST_VALIDATION_FAILED
  }
  if (error.kind === 'http' && (error.code === 'INTERNAL_ERROR' || (error.status ?? 0) >= 500)) {
    return SERVER_ERROR
  }
  return UNEXPECTED_ERROR
}
