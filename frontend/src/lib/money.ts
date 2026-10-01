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
