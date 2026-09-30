from collections.abc import Mapping

from freestack.domain.composition.models import (
    CompositionResult,
    CompositionStatus,
    Stack,
    StackBudgetCheck,
)
from freestack.domain.pricing import PlanPricing
from freestack.domain.recommendation.checks import BudgetCheck, ReasonCode
from freestack.domain.recommendation.evaluation import (
    EvaluationStatus,
    PlanEvaluation,
    RecommendationEvaluation,
)


def collect_plan_pricing(
    evaluation: RecommendationEvaluation,
) -> Mapping[str, PlanPricing]:
    """Collect plan pricing carried by evaluation checks.

    Pricing is read from ``BudgetCheck.pricing``. A missing check or a
    ``None`` price is omitted. The same plan must not disagree with itself.
    """

    found: dict[str, PlanPricing | None] = {}
    for role in evaluation.roles:
        for bucket in (role.compatible, role.unknown, role.incompatible):
            for item in bucket:
                pricing = _pricing_from(item)
                previous = found.get(item.plan.id, pricing)
                if item.plan.id in found and previous != pricing:
                    raise ValueError(f"inconsistent pricing: {item.plan.id}")
                found[item.plan.id] = pricing
    return {
        plan_id: pricing
        for plan_id, pricing in sorted(found.items())
        if pricing is not None
    }


def evaluate_stack_budget(
    plan_ids: tuple[str, ...],
    *,
    monthly_budget_usd_cents: int,
    pricing_by_plan: Mapping[str, PlanPricing],
) -> StackBudgetCheck:
    """Compare unique plan base fees with one monthly budget."""

    _require_budget(monthly_budget_usd_cents)
    _require_pricing_keys(pricing_by_plan)
    priced: list[str] = []
    unpriced: list[str] = []
    known_total = 0
    for plan_id in tuple(sorted(set(plan_ids))):
        pricing = pricing_by_plan.get(plan_id)
        if pricing is None:
            unpriced.append(plan_id)
            continue
        priced.append(plan_id)
        known_total += pricing.monthly_base_fee_usd_cents
    return StackBudgetCheck(
        budget_usd_cents=monthly_budget_usd_cents,
        priced_plan_ids=tuple(priced),
        unpriced_plan_ids=tuple(unpriced),
        known_total_usd_cents=known_total,
        reason=_budget_reason(monthly_budget_usd_cents, known_total, tuple(unpriced)),
    )


def apply_stack_budget(
    result: CompositionResult,
    *,
    monthly_budget_usd_cents: int,
    pricing_by_plan: Mapping[str, PlanPricing],
) -> CompositionResult:
    """Attach a stack budget check and regroup stacks by the model's status."""

    _require_budget(monthly_budget_usd_cents)
    if result.status is not CompositionStatus.COMPOSED:
        return result
    stacks = (*result.compatible, *result.unknown, *result.incompatible)
    if any(stack.budget_check is not None for stack in stacks):
        raise ValueError("budget already applied")
    updated = tuple(
        Stack(
            assignments=stack.assignments,
            budget_check=evaluate_stack_budget(
                stack.plan_ids,
                monthly_budget_usd_cents=monthly_budget_usd_cents,
                pricing_by_plan=pricing_by_plan,
            ),
        )
        for stack in stacks
    )
    grouped: dict[EvaluationStatus, list[Stack]] = {
        EvaluationStatus.COMPATIBLE: [],
        EvaluationStatus.UNKNOWN: [],
        EvaluationStatus.INCOMPATIBLE: [],
    }
    for stack in updated:
        grouped[stack.status].append(stack)
    return CompositionResult(
        status=CompositionStatus.COMPOSED,
        compatible=_sorted(grouped[EvaluationStatus.COMPATIBLE]),
        unknown=_sorted(grouped[EvaluationStatus.UNKNOWN]),
        incompatible=_sorted(grouped[EvaluationStatus.INCOMPATIBLE]),
        blocked_roles=result.blocked_roles,
        combination_count=result.combination_count,
        unevaluated_features=result.unevaluated_features,
    )


def _pricing_from(item: PlanEvaluation) -> PlanPricing | None:
    if isinstance(item.budget_check, BudgetCheck):
        return item.budget_check.pricing
    return None


def _budget_reason(
    monthly_budget_usd_cents: int,
    known_total_usd_cents: int,
    unpriced_plan_ids: tuple[str, ...],
) -> ReasonCode:
    if known_total_usd_cents > monthly_budget_usd_cents:
        return ReasonCode.OVER_BUDGET
    if unpriced_plan_ids:
        return ReasonCode.PRICING_NOT_FOUND
    return ReasonCode.WITHIN_BUDGET


def _require_budget(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"invalid monthly_budget_usd_cents: {value!r}")


def _require_pricing_keys(pricing_by_plan: Mapping[str, PlanPricing]) -> None:
    for plan_id, pricing in pricing_by_plan.items():
        if not isinstance(pricing, PlanPricing) or pricing.plan_id != plan_id:
            raise ValueError(f"invalid pricing: {plan_id!r} does not match {pricing!r}")


def _sorted(stacks: list[Stack]) -> tuple[Stack, ...]:
    return tuple(sorted(stacks, key=lambda stack: stack.sort_key))
