export function formatUsdCents(cents: number): string {
  if (!Number.isSafeInteger(cents) || cents < 0) {
    throw new RangeError('Cents must be a non-negative safe integer')
  }
  const dollars = Math.floor(cents / 100)
  const remainder = cents % 100
  const dollarText = dollars.toLocaleString('en-US')
  if (remainder === 0) {
    return `$${dollarText}`
  }
  return `$${dollarText}.${String(remainder).padStart(2, '0')}`
}

export const KRW_PER_USD = 1_400

export function wholeKrwToUsdCents(won: number): number {
  if (!Number.isSafeInteger(won) || won < 0) {
    throw new RangeError('Won must be a non-negative safe integer')
  }
  const cents = Math.round((won * 100) / KRW_PER_USD)
  if (!Number.isSafeInteger(cents)) {
    throw new RangeError('Won amount is outside the safe integer range')
  }
  if (won > 0 && cents === 0) {
    return 1
  }
  return cents
}

export function wholeUsdToCents(dollars: number): number {
  if (!Number.isSafeInteger(dollars) || dollars < 0) {
    throw new RangeError('Dollars must be a non-negative safe integer')
  }
  const cents = dollars * 100
  if (!Number.isSafeInteger(cents)) {
    throw new RangeError('Dollar amount is outside the safe integer range')
  }
  return cents
}
