import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { copyToClipboard } from './clipboard.ts'

describe('copyToClipboard', () => {
  const originalClipboard = navigator.clipboard

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    Object.defineProperty(navigator, 'clipboard', {
      value: originalClipboard,
      configurable: true,
      writable: true,
    })
  })

  it('uses navigator.clipboard.writeText when available and resolves', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      configurable: true,
      writable: true,
    })

    const result = await copyToClipboard('test prompt')
    expect(result).toBe(true)
    expect(writeTextMock).toHaveBeenCalledWith('test prompt')
  })

  it('falls back to document.execCommand when navigator.clipboard fails', async () => {
    const writeTextMock = vi.fn().mockRejectedValue(new Error('Permission denied'))
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      configurable: true,
      writable: true,
    })

    const execCommandMock = vi.fn().mockReturnValue(true)
    document.execCommand = execCommandMock

    const result = await copyToClipboard('fallback prompt')
    expect(result).toBe(true)
    expect(execCommandMock).toHaveBeenCalledWith('copy')
  })
})
