from freestack.api.schemas import (
    AssignmentResponse,
    BlockedRoleResponse,
    CaveatResponse,
    CheckResponse,
    CompositionResponse,
    LimitResponse,
    PlanBudgetCheckResponse,
    PlanDetailResponse,
    PlanEvaluationResponse,
    PlanResponse,
    PricingResponse,
    ProviderResponse,
    QuantityCheckResponse,
    RecommendationRequest,
    RecommendationResponse,
    RequirementResponse,
    RoleEvaluationResponse,
    ServiceResponse,
    SourceResponse,
    StackBudgetCheckResponse,
    StackResponse,
)
from freestack.application.composition import StackCompositionResult
from freestack.application.recommendation import PlanDetail
from freestack.domain.capability import CapabilityKey
from freestack.domain.caveat import Caveat
from freestack.domain.composition.models import (
    BlockedRole,
    CompositionResult,
    RoleAssignment,
    Stack,
    StackBudgetCheck,
)
from freestack.domain.feature import Feature
from freestack.domain.limit import Limit
from freestack.domain.pricing import ExceedBehavior, PlanPricing
from freestack.domain.provider import Provider
from freestack.domain.recommendation.checks import BudgetCheck, CheckResult, LimitCheck
from freestack.domain.recommendation.evaluation import PlanEvaluation, RoleEvaluation
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.service import Service
from freestack.domain.source import Source

_FEATURE_ORDER = {feature: index for index, feature in enumerate(Feature)}
_CAPABILITY_ORDER = {capability: index for index, capability in enumerate(CapabilityKey)}
_EXCEED_ORDER = {behavior: index for index, behavior in enumerate(ExceedBehavior)}


def to_requirement(dto: RecommendationRequest) -> ProjectRequirement:
    """Copy a request DTO into a project requirement. Domain validation stays in the domain."""

    return ProjectRequirement(
        features=frozenset(dto.features),
        file_storage_bytes=dto.file_storage_bytes,
        database_size_bytes=dto.database_size_bytes,
        monthly_bandwidth_bytes=dto.monthly_bandwidth_bytes,
        monthly_budget_usd_cents=dto.monthly_budget_usd_cents,
    )


def to_response(result: StackCompositionResult) -> RecommendationResponse:
    """Copy one composition result into an API response. This does not judge or reprice it."""

    sources: dict[str, SourceResponse] = {}
    plans: dict[str, PlanDetailResponse] = {}
    for detail in result.recommendation.plans:
        plans[detail.plan.id] = _plan_detail(detail)
        for source in detail.sources:
            sources.setdefault(source.id, _source(source))
    return RecommendationResponse(
        requirement=_requirement(result.requirement),
        roles=[_role(role) for role in result.recommendation.evaluation.roles],
        composition=_composition(result.composition),
        unevaluated_features=_features(result.recommendation.evaluation.unevaluated_features),
        plans=plans,
        sources=sources,
    )


def _requirement(requirement: ProjectRequirement) -> RequirementResponse:
    return RequirementResponse(
        features=_features(requirement.features),
        file_storage_bytes=requirement.file_storage_bytes,
        database_size_bytes=requirement.database_size_bytes,
        monthly_bandwidth_bytes=requirement.monthly_bandwidth_bytes,
        monthly_budget_usd_cents=requirement.monthly_budget_usd_cents,
    )


def _features(features: frozenset[Feature]) -> list[Feature]:
    return sorted(features, key=_FEATURE_ORDER.__getitem__)


def _plan_detail(detail: PlanDetail) -> PlanDetailResponse:
    return PlanDetailResponse(
        plan=PlanResponse(
            id=detail.plan.id,
            service_id=detail.plan.service_id,
            name=detail.plan.name,
            slug=detail.plan.slug,
            description=detail.plan.description,
            capabilities=sorted(detail.plan.capabilities, key=_CAPABILITY_ORDER.__getitem__),
        ),
        service=_service(detail.service),
        provider=_provider(detail.provider),
        pricing=_pricing(detail.pricing),
        caveats=[_caveat(caveat) for caveat in detail.caveats],
        sources=[_source(source) for source in detail.sources],
    )


def _service(service: Service) -> ServiceResponse:
    return ServiceResponse(
        id=service.id,
        provider_id=service.provider_id,
        name=service.name,
        slug=service.slug,
        description=service.description,
    )


def _provider(provider: Provider) -> ProviderResponse:
    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        slug=provider.slug,
        description=provider.description,
    )


def _pricing(pricing: PlanPricing | None) -> PricingResponse | None:
    if pricing is None:
        return None
    return PricingResponse(
        plan_id=pricing.plan_id,
        monthly_base_fee_usd_cents=pricing.monthly_base_fee_usd_cents,
        exceed_behaviors=sorted(pricing.exceed_behaviors, key=_EXCEED_ORDER.__getitem__),
        source_id=pricing.source_id,
    )


def _caveat(caveat: Caveat) -> CaveatResponse:
    return CaveatResponse(
        plan_id=caveat.plan_id,
        statement=caveat.statement,
        source_id=caveat.source_id,
    )


def _source(source: Source) -> SourceResponse:
    return SourceResponse(
        id=source.id,
        url=source.url,
        checked_at=source.checked_at,
        notes=source.notes,
    )


def _role(role: RoleEvaluation) -> RoleEvaluationResponse:
    return RoleEvaluationResponse(
        role=role.role,
        compatible=[_plan_evaluation(item) for item in role.compatible],
        unknown=[_plan_evaluation(item) for item in role.unknown],
        incompatible=[_plan_evaluation(item) for item in role.incompatible],
    )


def _plan_evaluation(item: PlanEvaluation) -> PlanEvaluationResponse:
    return PlanEvaluationResponse(
        plan_id=item.plan.id,
        role=item.role,
        status=item.status,
        capability_check=_check(item.capability_check),
        quantity_checks=[_quantity(check) for check in item.quantity_checks],
        global_quantity_checks=[_quantity(check) for check in item.global_quantity_checks],
        budget_check=_plan_budget(item.budget_check),
    )


def _check(check: CheckResult) -> CheckResponse:
    return CheckResponse(reason_code=check.reason_code, outcome=check.outcome)


def _quantity(check: CheckResult) -> QuantityCheckResponse:
    if not isinstance(check, LimitCheck):
        return QuantityCheckResponse(
            reason_code=check.reason_code,
            outcome=check.outcome,
            limit=None,
            other_period_limits=[],
        )
    return QuantityCheckResponse(
        reason_code=check.reason_code,
        outcome=check.outcome,
        limit=_limit(check.limit) if check.limit is not None else None,
        other_period_limits=[_limit(limit) for limit in check.other_period_limits],
    )


def _limit(limit: Limit) -> LimitResponse:
    return LimitResponse(
        plan_id=limit.plan_id,
        metric=limit.metric,
        period=limit.period,
        value=limit.value,
        source_id=limit.source_id,
    )


def _plan_budget(check: CheckResult | None) -> PlanBudgetCheckResponse | None:
    if check is None:
        return None
    pricing = check.pricing if isinstance(check, BudgetCheck) else None
    return PlanBudgetCheckResponse(
        reason_code=check.reason_code,
        outcome=check.outcome,
        pricing=_pricing(pricing),
    )


def _composition(composition: CompositionResult) -> CompositionResponse:
    return CompositionResponse(
        status=composition.status,
        compatible=[_stack(stack) for stack in composition.compatible],
        unknown=[_stack(stack) for stack in composition.unknown],
        incompatible=[_stack(stack) for stack in composition.incompatible],
        blocked_roles=[_blocked_role(role) for role in composition.blocked_roles],
        combination_count=composition.combination_count,
        unevaluated_features=_features(composition.unevaluated_features),
    )


def _stack(stack: Stack) -> StackResponse:
    return StackResponse(
        key=_stack_key(stack),
        assignments=[_assignment(item) for item in stack.assignments],
        plan_ids=list(stack.plan_ids),
        status=stack.status,
        budget_check=_stack_budget(stack.budget_check),
    )


def _stack_key(stack: Stack) -> str:
    return ";".join(
        f"{assignment.feature.value}={assignment.plan_id}" for assignment in stack.assignments
    )


def _assignment(assignment: RoleAssignment) -> AssignmentResponse:
    return AssignmentResponse(
        feature=assignment.feature,
        plan_id=assignment.plan_id,
        status=assignment.status,
    )


def _stack_budget(check: StackBudgetCheck | None) -> StackBudgetCheckResponse | None:
    if check is None:
        return None
    return StackBudgetCheckResponse(
        budget_usd_cents=check.budget_usd_cents,
        priced_plan_ids=list(check.priced_plan_ids),
        unpriced_plan_ids=list(check.unpriced_plan_ids),
        known_total_usd_cents=check.known_total_usd_cents,
        reason=check.reason,
        outcome=check.outcome,
    )


def _blocked_role(role: BlockedRole) -> BlockedRoleResponse:
    return BlockedRoleResponse(feature=role.feature, reason=role.reason)
