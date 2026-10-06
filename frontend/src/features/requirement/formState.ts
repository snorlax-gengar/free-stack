import type { Feature, RecommendationRequest } from '../../api/types.ts'
import type { QuantityUnit } from '../../lib/units.ts'

export type QuantityKey = 'fileStorage' | 'databaseSize' | 'monthlyBandwidth'

export type QuantityRequestKey = Exclude<
  keyof RecommendationRequest,
  'features' | 'monthly_budget_usd_cents'
>

export type QuantityInput = {
  amount: string
  unit: QuantityUnit
}

export const BANDWIDTH_RANGES = [
  { id: 'up-to-5', label: '5GB 이하', gigabytes: 5 },
  { id: 'over-5', label: '5GB 초과', gigabytes: 6 },
] as const

export type BandwidthRangeId = (typeof BANDWIDTH_RANGES)[number]['id']

export type BudgetCurrency = 'USD' | 'KRW'

export type RequirementFormValues = {
  features: readonly Feature[]
  quantities: Record<QuantityKey, QuantityInput>
  bandwidthRange: BandwidthRangeId | null
  budgetAmount: string
  budgetCurrency: BudgetCurrency
}

export type QuantityPreset = {
  label: string
  amount: string
  unit: QuantityUnit
}

export type QuantityFieldConfig = {
  key: QuantityKey
  requestKey: QuantityRequestKey
  feature: Feature | null
  label: string
  hint: string
  defaultUnit: QuantityUnit
  presets: readonly QuantityPreset[]
}

const storagePresets = [
  { label: '100 MB', amount: '100', unit: 'MB' },
  { label: '500 MB', amount: '500', unit: 'MB' },
  { label: '1 GB', amount: '1', unit: 'GB' },
  { label: '5 GB', amount: '5', unit: 'GB' },
] as const satisfies readonly QuantityPreset[]

export const QUANTITY_FIELDS = [
  {
    key: 'fileStorage',
    requestKey: 'file_storage_bytes',
    feature: 'file-uploads',
    label: '파일 저장 용량',
    hint: '비워 두면 용량 조건 없이 추천합니다. (예: 1GB는 일반 스마트폰 사진 약 300~500장 분량입니다.)',
    defaultUnit: 'MB',
    presets: storagePresets,
  },
  {
    key: 'databaseSize',
    requestKey: 'database_size_bytes',
    feature: 'database',
    label: '데이터베이스 크기',
    hint: '비워 두면 크기 조건 없이 추천합니다. (예: 500MB는 회원 수천 명, 텍스트 데이터 수십만 건에 넉넉합니다.)',
    defaultUnit: 'MB',
    presets: storagePresets,
  },
  {
    key: 'monthlyBandwidth',
    requestKey: 'monthly_bandwidth_bytes',
    feature: null,
    label: '월 트래픽(대역폭)',
    hint: '선택하지 않으면 트래픽 조건 없이 추천합니다. (5GB 이하는 개인 포트폴리오나 일 방문자 100~300명 수준 블로그에 충분합니다.)',
    defaultUnit: 'GB',
    presets: [],
  },
] as const satisfies readonly QuantityFieldConfig[]

export type ProjectTemplate = {
  id: 'portfolio' | 'fullstack' | 'content'
  label: string
  description: string
  features: readonly Feature[]
  bandwidthRange: BandwidthRangeId | null
  budgetAmount: string
  quantities?: Partial<Record<QuantityKey, QuantityInput>>
}

export const PROJECT_TEMPLATES: readonly ProjectTemplate[] = [
  {
    id: 'portfolio',
    label: '개인 포트폴리오 / 소개 페이지',
    description: '방문자에게 보여주는 정적 웹사이트 (React, Vue, HTML)',
    features: ['static-frontend'],
    bandwidthRange: null,
    budgetAmount: '',
  },
  {
    id: 'fullstack',
    label: '풀스택 웹 서비스 (MVP)',
    description: '로그인과 데이터 저장이 필요한 스타트업/사이드 프로젝트',
    features: ['static-frontend', 'database', 'authentication'],
    bandwidthRange: null,
    budgetAmount: '',
    quantities: {
      databaseSize: { amount: '500', unit: 'MB' },
    },
  },
  {
    id: 'content',
    label: '블로그 / 콘텐츠 갤러리',
    description: '이미지 업로드와 글 작성이 필요한 미디어/블로그 서비스',
    features: ['static-frontend', 'file-uploads', 'database'],
    bandwidthRange: null,
    budgetAmount: '',
    quantities: {
      fileStorage: { amount: '1', unit: 'GB' },
      databaseSize: { amount: '500', unit: 'MB' },
    },
  },
] as const

export const BUDGET_PRESETS = {
  USD: [
    { label: '$0', amount: '0' },
    { label: '$5', amount: '5' },
    { label: '$10', amount: '10' },
    { label: '$20', amount: '20' },
  ],
  KRW: [
    { label: '0원', amount: '0' },
    { label: '5,000원', amount: '5000' },
    { label: '10,000원', amount: '10000' },
    { label: '30,000원', amount: '30000' },
  ],
} as const

export type FormAction =
  | { type: 'toggleFeature'; feature: Feature }
  | { type: 'setQuantityAmount'; key: QuantityKey; amount: string }
  | { type: 'setQuantityUnit'; key: QuantityKey; unit: QuantityUnit }
  | { type: 'applyQuantityPreset'; key: QuantityKey; amount: string; unit: QuantityUnit }
  | { type: 'clearQuantity'; key: QuantityKey }
  | { type: 'setBandwidthRange'; range: BandwidthRangeId | null }
  | { type: 'setBudget'; amount: string }
  | { type: 'setBudgetCurrency'; currency: BudgetCurrency }
  | { type: 'applyBudgetPreset'; amount: string }
  | { type: 'clearBudget' }
  | { type: 'applyProjectTemplate'; template: ProjectTemplate }

export const initialFormValues: RequirementFormValues = {
  features: [],
  quantities: {
    fileStorage: { amount: '', unit: 'MB' },
    databaseSize: { amount: '', unit: 'MB' },
    monthlyBandwidth: { amount: '', unit: 'GB' },
  },
  bandwidthRange: null,
  budgetAmount: '',
  budgetCurrency: 'USD',
}

export function formReducer(state: RequirementFormValues, action: FormAction): RequirementFormValues {
  switch (action.type) {
    case 'applyProjectTemplate': {
      return {
        ...state,
        features: action.template.features,
        bandwidthRange: action.template.bandwidthRange,
        budgetAmount: action.template.budgetAmount,
        quantities: {
          fileStorage: action.template.quantities?.fileStorage ?? initialFormValues.quantities.fileStorage,
          databaseSize: action.template.quantities?.databaseSize ?? initialFormValues.quantities.databaseSize,
          monthlyBandwidth: action.template.quantities?.monthlyBandwidth ?? initialFormValues.quantities.monthlyBandwidth,
        },
      }
    }
    case 'toggleFeature': {
      const selected = state.features.includes(action.feature)
      return {
        ...state,
        features: selected
          ? state.features.filter((feature) => feature !== action.feature)
          : [...state.features, action.feature],
      }
    }
    case 'setQuantityAmount':
      return updateQuantity(state, action.key, { amount: action.amount })
    case 'setQuantityUnit':
      return updateQuantity(state, action.key, { unit: action.unit })
    case 'applyQuantityPreset':
      return updateQuantity(state, action.key, { amount: action.amount, unit: action.unit })
    case 'clearQuantity':
      return updateQuantity(state, action.key, {
        amount: '',
        unit: defaultUnit(action.key),
      })
    case 'setBandwidthRange':
      return { ...state, bandwidthRange: action.range }
    case 'setBudget':
    case 'applyBudgetPreset':
      return { ...state, budgetAmount: action.amount }
    case 'setBudgetCurrency':
      return { ...state, budgetCurrency: action.currency, budgetAmount: '' }
    case 'clearBudget':
      return { ...state, budgetAmount: '' }
    default:
      return state
  }
}

function updateQuantity(
  state: RequirementFormValues,
  key: QuantityKey,
  patch: Partial<QuantityInput>,
): RequirementFormValues {
  return {
    ...state,
    quantities: {
      ...state.quantities,
      [key]: { ...state.quantities[key], ...patch },
    },
  }
}

function defaultUnit(key: QuantityKey): QuantityUnit {
  const field = QUANTITY_FIELDS.find((item) => item.key === key)
  return field?.defaultUnit ?? 'MB'
}
