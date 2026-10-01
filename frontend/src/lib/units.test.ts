import { describe, expect, it } from 'vitest'
import { formatBytes, toBytes } from './units.ts'

describe('toBytes', () => {
  it('uses decimal megabytes and gigabytes', () => {
    expect(toBytes(500, 'MB')).toBe(500_000_000)
    expect(toBytes(1, 'GB')).toBe(1_000_000_000)
    expect(toBytes(5, 'GB')).toBe(5_000_000_000)
    expect(toBytes(10, 'GB')).toBe(10_000_000_000)
  })

  it.each([0, -1, 1.5, Number.NaN, Number.POSITIVE_INFINITY, Number.MAX_SAFE_INTEGER + 1])(
    'rejects %s',
    (amount) => {
      expect(() => toBytes(amount, 'MB')).toThrow(RangeError)
    },
  )

  it('rejects a product outside the safe integer range', () => {
    expect(() => toBytes(Number.MAX_SAFE_INTEGER, 'GB')).toThrow(RangeError)
  })
})

describe('formatBytes', () => {
  it('formats bytes, megabytes, and gigabytes', () => {
    expect(formatBytes(1_234)).toBe('1,234 B')
    expect(formatBytes(999_999)).toBe('999,999 B')
    expect(formatBytes(1_000_000)).toBe('1 MB')
    expect(formatBytes(500_000_000)).toBe('500 MB')
    expect(formatBytes(1_000_000_000)).toBe('1 GB')
    expect(formatBytes(1_500_000_000)).toBe('1.5 GB')
    expect(formatBytes(1_250_000_000)).toBe('1.25 GB')
    expect(formatBytes(1_200_000_000)).toBe('1.2 GB')
    expect(formatBytes(1_500_000_000_000)).toBe('1,500 GB')
  })
})
