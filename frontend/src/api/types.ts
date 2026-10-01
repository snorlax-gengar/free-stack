import type { components } from './schema.gen.ts'

export type Schemas = components['schemas']

export type RecommendationRequest = Schemas['RecommendationRequest']
export type RecommendationResponse = Schemas['RecommendationResponse']
export type Requirement = Schemas['RequirementResponse']
export type Composition = Schemas['CompositionResponse']
export type RoleEvaluation = Schemas['RoleEvaluationResponse']
export type PlanEvaluation = Schemas['PlanEvaluationResponse']
export type Assignment = Schemas['AssignmentResponse']
export type Stack = Schemas['StackResponse']
export type StackBudgetCheck = Schemas['StackBudgetCheckResponse']
export type PlanDetail = Schemas['PlanDetailResponse']
export type Check = Schemas['CheckResponse']
export type QuantityCheck = Schemas['QuantityCheckResponse']
export type PlanBudgetCheck = Schemas['PlanBudgetCheckResponse']
export type Limit = Schemas['LimitResponse']
export type Pricing = Schemas['PricingResponse']
export type Caveat = Schemas['CaveatResponse']
export type Source = Schemas['SourceResponse']
export type Feature = Schemas['Feature']
export type CapabilityKey = Schemas['CapabilityKey']
export type EvaluationStatus = Schemas['EvaluationStatus']
export type CheckOutcome = Schemas['CheckOutcome']
export type ReasonCode = Schemas['ReasonCode']
export type CompositionStatus = Schemas['CompositionStatus']
export type BlockReason = Schemas['BlockReason']
export type LimitMetric = Schemas['LimitMetric']
export type LimitPeriod = Schemas['LimitPeriod']
export type ExceedBehavior = Schemas['ExceedBehavior']

export type KnownErrorCode =
  | 'REQUEST_VALIDATION_FAILED'
  | 'INVALID_REQUIREMENT'
  | 'INTERNAL_ERROR'
