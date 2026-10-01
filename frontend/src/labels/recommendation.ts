import type {
  BlockReason,
  CapabilityKey,
  CheckOutcome,
  CompositionStatus,
  EvaluationStatus,
  ExceedBehavior,
  LimitMetric,
  LimitPeriod,
  ReasonCode,
} from '../api/types.ts'

export const evaluationStatusLabels = {
  compatible: '충족',
  unknown: '확인 필요',
  incompatible: '미충족',
} satisfies Record<EvaluationStatus, string>

export const checkOutcomeLabels = {
  satisfied: '충족',
  violated: '미충족',
  unknown: '확인 필요',
} satisfies Record<CheckOutcome, string>

export const reasonCodeLabels = {
  'capability-provided': '기능 제공',
  'capability-not-provided': '기능 미제공',
  'within-limit': '한도 이내',
  unlimited: '제한 없음',
  'exceeds-limit': '한도 초과',
  'limit-not-found': '한도 정보 없음',
  'limit-period-mismatch': '한도 기간 불일치',
  'within-budget': '예산 이내',
  'over-budget': '예산 초과',
  'pricing-not-found': '가격 확인 필요',
} satisfies Record<ReasonCode, string>

export const blockReasonLabels = {
  'no-candidates': '후보 없음',
  'all-incompatible': '모두 미충족',
} satisfies Record<BlockReason, string>

export const compositionStatusLabels = {
  composed: '조합됨',
  blocked: '조합 불가',
  'too-many-combinations': '조합이 너무 많음',
  'no-roles': '평가할 역할 없음',
} satisfies Record<CompositionStatus, string>

export const limitMetricLabels = {
  'file-storage-bytes': '파일 저장 용량',
  'database-size-bytes': '데이터베이스 크기',
  'bandwidth-bytes': '대역폭',
  requests: '요청 수',
  'build-seconds': '빌드 시간',
} satisfies Record<LimitMetric, string>

export const limitPeriodLabels = {
  none: '',
  day: '일',
  month: '월',
} satisfies Record<LimitPeriod, string>

export const exceedBehaviorLabels = {
  charged: '초과 요금',
  suspended: '사용 중지',
  restricted: '기능 제한',
} satisfies Record<ExceedBehavior, string>

export const capabilityKeyLabels = {
  'static-hosting': '정적 호스팅',
  'server-compute': '서버 컴퓨트',
  'serverless-functions': '서버리스 함수',
  database: '데이터베이스',
  'file-storage': '파일 저장',
  authentication: '인증',
  realtime: '실시간',
  'scheduled-jobs': '예약 작업',
} satisfies Record<CapabilityKey, string>

export function labelOf(value: string, labels: object): string {
  if (!Object.hasOwn(labels, value)) {
    return value
  }
  const label = Reflect.get(labels, value)
  return typeof label === 'string' ? label : value
}
