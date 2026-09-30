from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from freestack.domain.feature import Feature
from freestack.domain.limit import Limit
from freestack.domain.needs import CapabilityNeed, DerivedNeeds
from freestack.domain.plan import Plan
from freestack.domain.pricing import PlanPricing
from freestack.domain.recommendation.checks import (
    CheckOutcome,
    CheckResult,
    check_budget,
    check_capability,
    check_limit,
)

_FEATURE_ORDER = {feature: index for index, feature in enumerate(Feature)}


class EvaluationStatus(StrEnum):
    """Aggregated check status for one plan in one role.

    ``compatible`` means the stated checks are not violated or unknown.
    It does not rank plans or choose a winner.
    """

    COMPATIBLE = "compatible"
    UNKNOWN = "unknown"
    INCOMPATIBLE = "incompatible"


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanEvaluation:
    """Checks for one candidate plan in one role. This is not a ranking."""

    plan: Plan
    role: Feature
    capability_check: CheckResult
    quantity_checks: tuple[CheckResult, ...]
    global_quantity_checks: tuple[CheckResult, ...]
    budget_check: CheckResult | None

    def __post_init__(self) -> None:
        if not isinstance(self.plan, Plan):
            raise ValueError(f"invalid plan: {self.plan!r}")
        if not isinstance(self.role, Feature):
            raise ValueError(f"invalid role: {self.role!r}")
        if not isinstance(self.capability_check, CheckResult):
            raise ValueError(f"invalid capability_check: {self.capability_check!r}")
        _require_check_results(self.quantity_checks, "quantity_checks")
        _require_check_results(self.global_quantity_checks, "global_quantity_checks")
        if self.budget_check is not None and not isinstance(self.budget_check, CheckResult):
            raise ValueError(f"invalid budget_check: {self.budget_check!r}")

    @property
    def status(self) -> EvaluationStatus:
        checks = [
            self.capability_check,
            *self.quantity_checks,
            *self.global_quantity_checks,
        ]
        if self.budget_check is not None:
            checks.append(self.budget_check)
        if any(check.outcome is CheckOutcome.VIOLATED for check in checks):
            return EvaluationStatus.INCOMPATIBLE
        if any(check.outcome is CheckOutcome.UNKNOWN for check in checks):
            return EvaluationStatus.UNKNOWN
        return EvaluationStatus.COMPATIBLE


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleEvaluation:
    """Candidate plan checks for one feature role, grouped by status."""

    role: Feature
    compatible: tuple[PlanEvaluation, ...]
    unknown: tuple[PlanEvaluation, ...]
    incompatible: tuple[PlanEvaluation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.role, Feature):
            raise ValueError(f"invalid role: {self.role!r}")
        _require_plan_bucket(self.compatible, EvaluationStatus.COMPATIBLE, "compatible")
        _require_plan_bucket(self.unknown, EvaluationStatus.UNKNOWN, "unknown")
        _require_plan_bucket(
            self.incompatible,
            EvaluationStatus.INCOMPATIBLE,
            "incompatible",
        )
        for evaluation in (*self.compatible, *self.unknown, *self.incompatible):
            if evaluation.role is not self.role:
                raise ValueError(f"invalid role: {evaluation.role!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class RecommendationEvaluation:
    """Role evaluations for one requirement. This does not choose a winner."""

    roles: tuple[RoleEvaluation, ...]
    unevaluated_features: frozenset[Feature]

    def __post_init__(self) -> None:
        if not isinstance(self.roles, tuple) or any(
            not isinstance(role, RoleEvaluation) for role in self.roles
        ):
            raise ValueError(f"invalid roles: {self.roles!r}")
        if not isinstance(self.unevaluated_features, frozenset) or any(
            not isinstance(feature, Feature) for feature in self.unevaluated_features
        ):
            raise ValueError(f"invalid unevaluated_features: {self.unevaluated_features!r}")


def evaluate_plan(
    plan: Plan,
    role: Feature,
    needs: DerivedNeeds,
    limits: Sequence[Limit],
    pricing: PlanPricing | None,
) -> PlanEvaluation | None:
    """Evaluate one plan for one role. A missing capability means it is not a candidate."""

    capability_need = _capability_need(needs, role)
    if capability_need is None or capability_need.capability not in plan.capabilities:
        return None

    role_checks: list[CheckResult] = []
    global_checks: list[CheckResult] = []
    for quantity in needs.quantities:
        if quantity.applies_to is role:
            role_checks.append(check_limit(limits, quantity))
        elif quantity.applies_to is None:
            global_checks.append(check_limit(limits, quantity))

    budget_check = None
    if needs.budget is not None:
        budget_check = check_budget(pricing, needs.budget)

    return PlanEvaluation(
        plan=plan,
        role=role,
        capability_check=check_capability(plan, capability_need),
        quantity_checks=tuple(role_checks),
        global_quantity_checks=tuple(global_checks),
        budget_check=budget_check,
    )


def evaluate_role(
    role: Feature,
    plans: Sequence[Plan],
    needs: DerivedNeeds,
    limits_by_plan: Mapping[str, Sequence[Limit]],
    pricing_by_plan: Mapping[str, PlanPricing],
) -> RoleEvaluation:
    """Group candidate plans for one role. Results are ordered by plan id."""

    evaluations = []
    for plan in plans:
        evaluation = evaluate_plan(
            plan,
            role,
            needs,
            limits_by_plan.get(plan.id, ()),
            pricing_by_plan.get(plan.id),
        )
        if evaluation is not None:
            evaluations.append(evaluation)
    ordered = tuple(sorted(evaluations, key=lambda evaluation: evaluation.plan.id))
    return RoleEvaluation(
        role=role,
        compatible=_with_status(ordered, EvaluationStatus.COMPATIBLE),
        unknown=_with_status(ordered, EvaluationStatus.UNKNOWN),
        incompatible=_with_status(ordered, EvaluationStatus.INCOMPATIBLE),
    )


def evaluate(
    needs: DerivedNeeds,
    plans: Sequence[Plan],
    limits_by_plan: Mapping[str, Sequence[Limit]],
    pricing_by_plan: Mapping[str, PlanPricing],
) -> RecommendationEvaluation:
    """Evaluate each capability role. This does not call a repository."""

    roles = tuple(
        evaluate_role(role, plans, needs, limits_by_plan, pricing_by_plan)
        for role in _roles(needs)
    )
    return RecommendationEvaluation(
        roles=roles,
        unevaluated_features=needs.unevaluated_features,
    )


def _capability_need(needs: DerivedNeeds, role: Feature) -> CapabilityNeed | None:
    for need in needs.capabilities:
        if need.feature is role:
            return need
    return None


def _roles(needs: DerivedNeeds) -> tuple[Feature, ...]:
    features = {need.feature for need in needs.capabilities}
    return tuple(sorted(features, key=_FEATURE_ORDER.__getitem__))


def _with_status(
    evaluations: tuple[PlanEvaluation, ...],
    status: EvaluationStatus,
) -> tuple[PlanEvaluation, ...]:
    return tuple(evaluation for evaluation in evaluations if evaluation.status is status)


def _require_check_results(values: object, field_name: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(item, CheckResult) for item in values):
        raise ValueError(f"invalid {field_name}: {values!r}")


def _require_plan_bucket(
    values: object,
    status: EvaluationStatus,
    field_name: str,
) -> None:
    if not isinstance(values, tuple) or any(
        not isinstance(item, PlanEvaluation) or item.status is not status for item in values
    ):
        raise ValueError(f"invalid {field_name}: {values!r}")
