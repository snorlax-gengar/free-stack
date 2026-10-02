import { describe, expect, it } from 'vitest'
import { formatUsdCents, wholeKrwToUsdCents, wholeUsdToCents } from './money.ts'

describe('formatUsdCents', () => {
  it('formats cents as dollars', () => {
    expect(formatUsdCents(0)).toBe('$0')
    expect(formatUsdCents(5)).toBe('$0.05')
    expect(formatUsdCents(499)).toBe('$4.99')
    expect(formatUsdCents(1000)).toBe('$10')
    expect(formatUsdCents(100050)).toBe('$1,000.50')
  })

  it.each([-1, 1.5, Number.MAX_SAFE_INTEGER + 1])('rejects %s', (cents) => {
    expect(() => formatUsdCents(cents)).toThrow(RangeError)
  })
})

describe('wholeUsdToCents', () => {
  it('converts whole dollars', () => {
    expect(wholeUsdToCents(0)).toBe(0)
    expect(wholeUsdToCents(10)).toBe(1000)
  })

  it.each([-1, 1.5, Number.MAX_SAFE_INTEGER])('rejects %s', (dollars) => {
    expect(() => wholeUsdToCents(dollars)).toThrow(RangeError)
  })
})

describe('wholeKrwToUsdCents', () => {
  it('converts won at 1400 per dollar and keeps a positive amount above zero cents', () => {
    expect(wholeKrwToUsdCents(0)).toBe(0)
    expect(wholeKrwToUsdCents(1400)).toBe(100)
    expect(wholeKrwToUsdCents(1)).toBe(1)
  })
})
