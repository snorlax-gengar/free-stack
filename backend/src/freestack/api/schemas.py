from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from freestack.domain.capability import CapabilityKey
from freestack.domain.composition.models import BlockReason, CompositionStatus
from freestack.domain.feature import Feature
from freestack.domain.limit import LimitMetric, LimitPeriod
from freestack.domain.pricing import ExceedBehavior
from freestack.domain.recommendation.checks import CheckOutcome, ReasonCode
from freestack.domain.recommendation.evaluation import EvaluationStatus

_STRICT_INT = Annotated[int, Field(strict=True)]


class RecommendationRequest(BaseModel):
    """JSON body for one stack composition request."""

    model_config = ConfigDict(extra="forbid")

    features: list[Feature]
    file_storage_bytes: _STRICT_INT | None = None
    database_size_bytes: _STRICT_INT | None = None
    monthly_bandwidth_bytes: _STRICT_INT | None = None
    monthly_budget_usd_cents: _STRICT_INT | None = None

    @field_validator("features")
    @classmethod
    def reject_duplicate_features(cls, features: list[Feature]) -> list[Feature]:
        if len(features) != len(set(features)):
            raise ValueError("duplicate features")
        return features


class RequirementResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features: list[Feature]
    file_storage_bytes: int | None
    database_size_bytes: int | None
    monthly_bandwidth_bytes: int | None
    monthly_budget_usd_cents: int | None


class PlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    service_id: str
    name: str
    slug: str
    description: str
    capabilities: list[CapabilityKey]


class ServiceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    provider_id: str
    name: str
    slug: str
    description: str


class ProviderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    slug: str
    description: str


class PricingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    monthly_base_fee_usd_cents: int
    exceed_behaviors: list[ExceedBehavior]
    source_id: str


class CaveatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    statement: str
    source_id: str


class SourceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    url: str
    checked_at: date
    notes: str


class PlanDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: PlanResponse
    service: ServiceResponse
    provider: ProviderResponse
    pricing: PricingResponse | None
    caveats: list[CaveatResponse]
    sources: list[SourceResponse]


class CheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason_code: ReasonCode
    outcome: CheckOutcome


class LimitResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    metric: LimitMetric
    period: LimitPeriod
    value: int | None
    source_id: str


class QuantityCheckResponse(CheckResponse):
    limit: LimitResponse | None
    other_period_limits: list[LimitResponse]


class PlanBudgetCheckResponse(CheckResponse):
    pricing: PricingResponse | None


class PlanEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    role: Feature
    status: EvaluationStatus
    capability_check: CheckResponse
    quantity_checks: list[QuantityCheckResponse]
    global_quantity_checks: list[QuantityCheckResponse]
    budget_check: PlanBudgetCheckResponse | None


class RoleEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Feature
    compatible: list[PlanEvaluationResponse]
    unknown: list[PlanEvaluationResponse]
    incompatible: list[PlanEvaluationResponse]


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature: Feature
    plan_id: str
    status: EvaluationStatus


class StackBudgetCheckResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_usd_cents: int
    priced_plan_ids: list[str]
    unpriced_plan_ids: list[str]
    known_total_usd_cents: int
    reason: ReasonCode
    outcome: CheckOutcome


class StackResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    assignments: list[AssignmentResponse]
    plan_ids: list[str]
    status: EvaluationStatus
    budget_check: StackBudgetCheckResponse | None


class BlockedRoleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feature: Feature
    reason: BlockReason


class CompositionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CompositionStatus
    compatible: list[StackResponse]
    unknown: list[StackResponse]
    incompatible: list[StackResponse]
    blocked_roles: list[BlockedRoleResponse]
    combination_count: int
    unevaluated_features: list[Feature]


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: RequirementResponse
    roles: list[RoleEvaluationResponse]
    composition: CompositionResponse
    unevaluated_features: list[Feature]
    plans: dict[str, PlanDetailResponse]
    sources: dict[str, SourceResponse]
