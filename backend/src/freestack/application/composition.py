from dataclasses import dataclass

from freestack.application.recommendation import PlanDetail, RecommendationResult, RecommendationService
from freestack.domain.composition.budget import apply_stack_budget, collect_plan_pricing
from freestack.domain.composition.composer import compose
from freestack.domain.composition.models import CompositionResult, Stack
from freestack.domain.requirement import ProjectRequirement


@dataclass(frozen=True, slots=True, kw_only=True)
class StackCompositionResult:
    """One requirement, its recommendation, and the stacks composed from it."""

    recommendation: RecommendationResult
    composition: CompositionResult
    requirement: ProjectRequirement

    def __post_init__(self) -> None:
        if not isinstance(self.recommendation, RecommendationResult):
            raise ValueError(f"invalid recommendation: {self.recommendation!r}")
        if not isinstance(self.composition, CompositionResult):
            raise ValueError(f"invalid composition: {self.composition!r}")
        if not isinstance(self.requirement, ProjectRequirement):
            raise ValueError(f"invalid requirement: {self.requirement!r}")
        known_plan_ids = {detail.plan.id for detail in self.recommendation.plans}
        for stack in _stacks(self.composition):
            missing = tuple(plan_id for plan_id in stack.plan_ids if plan_id not in known_plan_ids)
            if missing:
                raise ValueError(f"invalid stack plans: {missing!r}")
        if (
            self.composition.unevaluated_features
            != self.recommendation.evaluation.unevaluated_features
        ):
            raise ValueError(
                f"invalid unevaluated_features: {self.composition.unevaluated_features!r}"
            )
        budget = self.requirement.monthly_budget_usd_cents
        for stack in _stacks(self.composition):
            check = stack.budget_check
            if budget is None:
                if check is not None:
                    raise ValueError(f"invalid budget_check: {check!r}")
            elif check is not None and check.budget_usd_cents != budget:
                raise ValueError(
                    f"invalid budget_check: {check.budget_usd_cents!r} does not match {budget!r}"
                )

    def plan_detail(self, plan_id: str) -> PlanDetail:
        for detail in self.recommendation.plans:
            if detail.plan.id == plan_id:
                return detail
        raise KeyError(plan_id)

    def stack_plan_details(self, stack: Stack) -> tuple[PlanDetail, ...]:
        return tuple(self.plan_detail(plan_id) for plan_id in stack.plan_ids)


class StackCompositionService:
    """Run recommendation, then composition, then an optional stack budget."""

    def __init__(self, *, recommendations: RecommendationService, max_combinations: int) -> None:
        _require_max_combinations(max_combinations)
        self._recommendations = recommendations
        self._max_combinations = max_combinations

    def compose_stacks(self, requirement: ProjectRequirement) -> StackCompositionResult:
        recommendation = self._recommendations.recommend(requirement)
        composition = compose(
            recommendation.evaluation,
            max_combinations=self._max_combinations,
        )
        budget = requirement.monthly_budget_usd_cents
        if budget is not None:
            composition = apply_stack_budget(
                composition,
                monthly_budget_usd_cents=budget,
                pricing_by_plan=collect_plan_pricing(recommendation.evaluation),
            )
        return StackCompositionResult(
            recommendation=recommendation,
            composition=composition,
            requirement=requirement,
        )


def _stacks(composition: CompositionResult) -> tuple[Stack, ...]:
    return (*composition.compatible, *composition.unknown, *composition.incompatible)


def _require_max_combinations(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"invalid max_combinations: {value!r}")
