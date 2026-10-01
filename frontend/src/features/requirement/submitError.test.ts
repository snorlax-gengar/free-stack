import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../api/client.ts'
import { submitErrorMessage } from './submitError.ts'

describe('submitErrorMessage', () => {
  it('maps API failures without using the server message', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(message(new ApiError('http', 422, 'INVALID_REQUIREMENT', 'raw requirement'))).toBe(
      '선택한 기능과 입력값의 조합을 처리할 수 없습니다. 입력 내용을 확인해 주세요.',
    )
    expect(message(new ApiError('http', 422, 'REQUEST_VALIDATION_FAILED', 'raw validation'))).toBe(
      '요청을 처리할 수 없습니다. 입력 내용을 확인한 뒤 다시 시도해 주세요.',
    )
    expect(message(new ApiError('http', 500, 'INTERNAL_ERROR', 'An internal error occurred.'))).toBe(
      '일시적인 서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
    )
    expect(message(new ApiError('http', 400, 'UNKNOWN_CODE', 'raw unknown'))).toBe(
      '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.',
    )
    expect(message(new ApiError('network', null, null, 'offline'))).toBe(
      '서버에 연결할 수 없습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.',
    )
    expect(message(new ApiError('unexpected-response', 500, null, 'bad body'))).toBe(
      '요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.',
    )
    expect(message(new DOMException('stopped', 'AbortError'))).toBeNull()
    expect(message(new Error('boom'))).toBe('요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.')
  })
})

function message(error: unknown): string | null {
  return submitErrorMessage(error)
}
