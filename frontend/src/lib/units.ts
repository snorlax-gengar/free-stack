const MB = 1_000_000
const GB = 1_000_000_000

export type QuantityUnit = 'MB' | 'GB'

export function toBytes(amount: number, unit: QuantityUnit): number {
  if (!Number.isSafeInteger(amount) || amount <= 0) {
    throw new RangeError('Byte amount must be a positive safe integer')
  }
  const bytes = amount * (unit === 'MB' ? MB : GB)
  if (!Number.isSafeInteger(bytes)) {
    throw new RangeError('Byte amount is outside the safe integer range')
  }
  return bytes
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) {
    throw new RangeError('Byte amount must be a finite number greater than or equal to zero')
  }
  if (bytes >= GB) {
    return `${formatQuantity(bytes / GB)} GB`
  }
  if (bytes >= MB) {
    return `${formatQuantity(bytes / MB)} MB`
  }
  return `${formatQuantity(bytes)} B`
}

function formatQuantity(value: number): string {
  const rounded = Math.round((value + Number.EPSILON) * 100) / 100
  return rounded.toLocaleString('en-US', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  })
}
