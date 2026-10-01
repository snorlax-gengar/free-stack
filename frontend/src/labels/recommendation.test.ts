import { describe, expect, it } from 'vitest'
import {
  blockReasonValues,
  capabilityKeyValues,
  checkOutcomeValues,
  compositionStatusValues,
  evaluationStatusValues,
  exceedBehaviorValues,
  limitMetricValues,
  limitPeriodValues,
  reasonCodeValues,
} from '../api/schema.gen.ts'
import {
  blockReasonLabels,
  capabilityKeyLabels,
  checkOutcomeLabels,
  compositionStatusLabels,
  evaluationStatusLabels,
  exceedBehaviorLabels,
  labelOf,
  limitMetricLabels,
  limitPeriodLabels,
  reasonCodeLabels,
} from './recommendation.ts'

const banned = ['최고', '추천', '우수', '비추천', '최적', 'Best', '1위', '순위']

describe('recommendation labels', () => {
  it('labels every evaluation status', () => {
    expect(evaluationStatusLabels).toEqual({
      compatible: '충족',
      unknown: '확인 필요',
      incompatible: '미충족',
    })
    expect(Object.keys(evaluationStatusLabels)).toEqual([...evaluationStatusValues])
  })

  it('labels every check outcome', () => {
    expect(checkOutcomeLabels).toEqual({
      satisfied: '충족',
      violated: '미충족',
      unknown: '확인 필요',
    })
    expect(Object.keys(checkOutcomeLabels)).toEqual([...checkOutcomeValues])
  })

  it('labels every reason code', () => {
    expect(reasonCodeLabels).toEqual({
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
    })
    expect(Object.keys(reasonCodeLabels)).toEqual([...reasonCodeValues])
  })

  it('labels every block reason', () => {
    expect(blockReasonLabels).toEqual({
      'no-candidates': '후보 없음',
      'all-incompatible': '모두 미충족',
    })
    expect(Object.keys(blockReasonLabels)).toEqual([...blockReasonValues])
  })

  it('labels every composition status', () => {
    expect(compositionStatusLabels).toEqual({
      composed: '조합됨',
      blocked: '조합 불가',
      'too-many-combinations': '조합이 너무 많음',
      'no-roles': '평가할 역할 없음',
    })
    expect(Object.keys(compositionStatusLabels)).toEqual([...compositionStatusValues])
  })

  it('labels every limit metric', () => {
    expect(limitMetricLabels).toEqual({
      'file-storage-bytes': '파일 저장 용량',
      'database-size-bytes': '데이터베이스 크기',
      'bandwidth-bytes': '대역폭',
      requests: '요청 수',
      'build-seconds': '빌드 시간',
    })
    expect(Object.keys(limitMetricLabels)).toEqual([...limitMetricValues])
  })

  it('labels every limit period', () => {
    expect(limitPeriodLabels).toEqual({
      none: '',
      day: '일',
      month: '월',
    })
    expect(Object.keys(limitPeriodLabels)).toEqual([...limitPeriodValues])
  })

  it('labels every exceed behavior', () => {
    expect(exceedBehaviorLabels).toEqual({
      charged: '초과 요금',
      suspended: '사용 중지',
      restricted: '기능 제한',
    })
    expect(Object.keys(exceedBehaviorLabels)).toEqual([...exceedBehaviorValues])
  })

  it('labels every capability key', () => {
    expect(capabilityKeyLabels).toEqual({
      'static-hosting': '정적 호스팅',
      'server-compute': '서버 컴퓨트',
      'serverless-functions': '서버리스 함수',
      database: '데이터베이스',
      'file-storage': '파일 저장',
      authentication: '인증',
      realtime: '실시간',
      'scheduled-jobs': '예약 작업',
    })
    expect(Object.keys(capabilityKeyLabels)).toEqual([...capabilityKeyValues])
  })

  it('returns the original code for an unknown value', () => {
    expect(labelOf('future-code', evaluationStatusLabels)).toBe('future-code')
    expect(labelOf('compatible', evaluationStatusLabels)).toBe('충족')
    expect(labelOf('none', limitPeriodLabels)).toBe('')
  })

  it('does not use ranking language', () => {
    const labels = [
      ...Object.values(evaluationStatusLabels),
      ...Object.values(checkOutcomeLabels),
      ...Object.values(reasonCodeLabels),
      ...Object.values(blockReasonLabels),
      ...Object.values(compositionStatusLabels),
      ...Object.values(limitMetricLabels),
      ...Object.values(limitPeriodLabels),
      ...Object.values(exceedBehaviorLabels),
      ...Object.values(capabilityKeyLabels),
    ]
    for (const label of labels) {
      for (const word of banned) {
        expect(label.includes(word)).toBe(false)
      }
    }
  })
})
