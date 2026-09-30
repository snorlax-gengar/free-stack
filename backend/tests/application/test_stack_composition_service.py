import ast
from datetime import date
from pathlib import Path

import pytest

from freestack.application import composition as composition_module
from freestack.application import recommendation as recommendation_module
from freestack.application.composition import StackCompositionResult, StackCompositionService
from freestack.application.recommendation import (
    PlanDetail,
    RecommendationResult,
    RecommendationService,
)
from freestack.domain.capability import CapabilityKey
from freestack.domain.composition.models import (
    BlockReason,
    CompositionResult,
    CompositionStatus,
    RoleAssignment,
    Stack,
    StackBudgetCheck,
)
from freestack.domain.feature import Feature
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.plan import Plan
from freestack.domain.pricing import ExceedBehavior, PlanPricing
from freestack.domain.provider import Provider
from freestack.domain.recommendation.checks import CheckResult, ReasonCode
from freestack.domain.recommendation.evaluation import (
    EvaluationStatus,
    PlanEvaluation,
    RecommendationEvaluation,
    RoleEvaluation,
)
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.service import Service
from freestack.domain.source import Source
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository


class _NoCaveats:
    def list_caveats(self, plan_id: str) -> tuple:
        return ()


def _repository(*, shared: bool = True) -> InMemoryCatalogRepository:
    repository = InMemoryCatalogRepository()
    repository.add_provider(Provider(id="alpha", name="Alpha", slug="alpha", description=""))
    repository.add_service(
        Service(id="alpha-platform", provider_id="alpha", name="Platform", slug="platform", description="")
    )
    repository.add_plan(
        Plan(
            id="database-plan",
            service_id="alpha-platform",
            name="Database",
            slug="database",
            description="",
            capabilities=frozenset({CapabilityKey.DATABASE}),
        )
    )
    repository.add_plan(
        Plan(
            id="storage-plan",
            service_id="alpha-platform",
            name="Storage",
            slug="storage",
            description="",
            capabilities=frozenset({CapabilityKey.FILE_STORAGE}),
        )
    )
    if shared:
        repository.add_plan(
            Plan(
                id="shared-plan",
                service_id="alpha-platform",
                name="Shared",
                slug="shared",
                description="",
                capabilities=frozenset({CapabilityKey.DATABASE, CapabilityKey.FILE_STORAGE}),
            )
        )
    repository.add_source(
        Source(
            id="example-source",
            url="https://example.com/catalog",
            checked_at=date(2026, 9, 30),
            notes="",
        )
    )
    return repository


def _recommendations(repository: InMemoryCatalogRepository) -> RecommendationService:
    return RecommendationService(catalog=repository, caveats=_NoCaveats())


def _service(repository: InMemoryCatalogRepository, max_combinations: int = 10) -> StackCompositionService:
    return StackCompositionService(
        recommendations=_recommendations(repository),
        max_combinations=max_combinations,
    )


def _requirement(**overrides: object) -> ProjectRequirement:
    values: dict[str, object] = {"features": frozenset({Feature.DATABASE, Feature.FILE_UPLOADS})}
    values.update(overrides)
    return ProjectRequirement(**values)  # type: ignore[arg-type]


def test_compose_stacks_returns_recommendation_and_composition() -> None:
    requirement = _requirement()
    result = _service(_repository()).compose_stacks(requirement)

    assert result.requirement is requirement
    assert result.recommendation.plans
    assert result.composition.status is CompositionStatus.COMPOSED
    assert result.composition.combination_count == 4


def test_missing_budget_leaves_stack_budget_checks_empty() -> None:
    result = _service(_repository()).compose_stacks(_requirement())

    assert result.composition.status is CompositionStatus.COMPOSED
    assert result.composition.compatible
    assert all(stack.budget_check is None for stack in result.composition.compatible)


def test_budget_is_applied_to_every_composed_stack() -> None:
    repository = _repository()
    for plan_id, fee in (("database-plan", 100), ("storage-plan", 100), ("shared-plan", 100)):
        repository.add_plan_pricing(
            PlanPricing(
                plan_id=plan_id,
                monthly_base_fee_usd_cents=fee,
                exceed_behaviors=frozenset({ExceedBehavior.CHARGED}),
                source_id="example-source",
            )
        )

    result = _service(repository).compose_stacks(_requirement(monthly_budget_usd_cents=1000))

    stacks = (*result.composition.compatible, *result.composition.unknown, *result.composition.incompatible)
    assert result.composition.status is CompositionStatus.COMPOSED
    assert stacks
    assert all(stack.budget_check is not None for stack in stacks)
    assert all(stack.budget_check.budget_usd_cents == 1000 for stack in stacks)
    assert all(stack.status is EvaluationStatus.COMPATIBLE for stack in stacks)


def test_stack_sum_over_budget_stays_composed_and_incompatible() -> None:
    repository = _repository(shared=False)
    for plan_id in ("database-plan", "storage-plan"):
        repository.add_plan_pricing(
            PlanPricing(
                plan_id=plan_id,
                monthly_base_fee_usd_cents=600,
                exceed_behaviors=frozenset({ExceedBehavior.CHARGED}),
                source_id="example-source",
            )
        )

    result = _service(repository).compose_stacks(
        ProjectRequirement(
            features=frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
            monthly_budget_usd_cents=1000,
        )
    )
    paired = tuple(
        stack
        for stack in result.composition.incompatible
        if set(stack.plan_ids) == {"database-plan", "storage-plan"}
    )

    assert result.composition.status is CompositionStatus.COMPOSED
    assert result.composition.compatible == ()
    assert result.composition.unknown == ()
    assert result.composition.incompatible == paired
    assert all(stack.budget_check is not None and stack.budget_check.known_total_usd_cents == 1200 for stack in paired)
    assert all(stack.budget_check.reason is ReasonCode.OVER_BUDGET for stack in paired)


def test_missing_pricing_makes_budgeted_stacks_unknown() -> None:
    result = _service(_repository()).compose_stacks(_requirement(monthly_budget_usd_cents=0))

    assert result.composition.status is CompositionStatus.COMPOSED
    assert result.composition.compatible == ()
    assert result.composition.unknown
    assert all(
        stack.budget_check is not None and stack.budget_check.reason is ReasonCode.PRICING_NOT_FOUND
        for stack in result.composition.unknown
    )


def test_ai_api_alone_has_no_roles() -> None:
    result = _service(_repository()).compose_stacks(
        ProjectRequirement(features=frozenset({Feature.AI_API}))
    )

    assert result.composition.status is CompositionStatus.NO_ROLES
    assert result.composition.combination_count == 0
    assert result.composition.unevaluated_features == frozenset({Feature.AI_API})


def test_incompatible_candidates_block_composition() -> None:
    repository = _repository()
    for plan_id in ("database-plan", "shared-plan"):
        repository.add_limit(
            Limit(
                plan_id=plan_id,
                metric=LimitMetric.DATABASE_SIZE_BYTES,
                period=LimitPeriod.NONE,
                value=1,
                source_id="example-source",
            )
        )
    result = _service(repository).compose_stacks(
        ProjectRequirement(features=frozenset({Feature.DATABASE}), database_size_bytes=50)
    )

    assert result.composition.status is CompositionStatus.BLOCKED
    assert result.composition.blocked_roles[0].feature is Feature.DATABASE
    assert result.composition.blocked_roles[0].reason is BlockReason.ALL_INCOMPATIBLE
    assert result.composition.compatible == ()


def test_too_many_combinations_returns_the_full_count_without_stacks() -> None:
    result = _service(_repository(), max_combinations=1).compose_stacks(
        ProjectRequirement(features=frozenset({Feature.DATABASE}))
    )

    assert result.composition.status is CompositionStatus.TOO_MANY_COMBINATIONS
    assert result.composition.combination_count == 2
    assert result.composition.compatible == result.composition.unknown == result.composition.incompatible == ()


def test_budget_stage_follows_the_budget_field_not_composition_status(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    collect = composition_module.collect_plan_pricing
    apply = composition_module.apply_stack_budget

    def _collect(evaluation):
        calls.append("collect")
        return collect(evaluation)

    def _apply(result, **kwargs):
        calls.append("apply")
        return apply(result, **kwargs)

    monkeypatch.setattr(composition_module, "collect_plan_pricing", _collect)
    monkeypatch.setattr(composition_module, "apply_stack_budget", _apply)
    service = _service(_repository())

    service.compose_stacks(ProjectRequirement(features=frozenset({Feature.AI_API})))
    assert calls == []
    service.compose_stacks(
        ProjectRequirement(features=frozenset({Feature.AI_API}), monthly_budget_usd_cents=0)
    )
    assert calls == ["collect", "apply"]


def test_plan_details_follow_stack_plan_ids_and_are_shared() -> None:
    result = _service(_repository()).compose_stacks(_requirement())
    shared_stacks = [
        stack for stack in result.composition.compatible if "shared-plan" in stack.plan_ids
    ]
    details = [result.plan_detail("shared-plan") for stack in shared_stacks]
    shared_only = next(stack for stack in shared_stacks if stack.plan_ids == ("shared-plan",))

    assert len(details) > 1
    assert all(detail is details[0] for detail in details)
    assert result.stack_plan_details(shared_only) == (details[0],)
    assert len(shared_only.assignments) == 2
    with pytest.raises(KeyError):
        result.plan_detail("unknown-plan")


@pytest.mark.parametrize("value", [0, -1, True, False, 1.5, "100"])
def test_max_combinations_is_rejected_when_the_service_is_created(value: object) -> None:
    with pytest.raises(ValueError, match=r"invalid max_combinations:"):
        StackCompositionService(
            recommendations=_recommendations(_repository()),
            max_combinations=value,  # type: ignore[arg-type]
        )


def test_result_rejects_a_stack_plan_missing_from_the_recommendation() -> None:
    recommendation = _recommendation("database-plan")
    composition = _composition("missing-plan")

    with pytest.raises(ValueError, match=r"invalid stack plans:"):
        StackCompositionResult(
            recommendation=recommendation,
            composition=composition,
            requirement=ProjectRequirement(features=frozenset({Feature.DATABASE})),
        )


def test_result_rejects_unevaluated_features_that_disagree() -> None:
    recommendation = _recommendation("database-plan", unevaluated=frozenset({Feature.AI_API}))

    with pytest.raises(ValueError, match=r"invalid unevaluated_features:"):
        StackCompositionResult(
            recommendation=recommendation,
            composition=_composition("database-plan"),
            requirement=ProjectRequirement(features=frozenset({Feature.DATABASE, Feature.AI_API})),
        )


def test_result_rejects_a_budget_that_disagrees_with_the_requirement() -> None:
    recommendation = _recommendation("database-plan")
    composition = _composition(
        "database-plan",
        budget_check=StackBudgetCheck(
            budget_usd_cents=2000,
            priced_plan_ids=("database-plan",),
            unpriced_plan_ids=(),
            known_total_usd_cents=0,
            reason=ReasonCode.WITHIN_BUDGET,
        ),
    )

    with pytest.raises(ValueError, match=r"invalid budget_check:"):
        StackCompositionResult(
            recommendation=recommendation,
            composition=composition,
            requirement=ProjectRequirement(
                features=frozenset({Feature.DATABASE}),
                monthly_budget_usd_cents=1000,
            ),
        )


def test_composition_application_does_not_import_infrastructure_or_reverse_into_recommendation() -> None:
    source = Path(composition_module.__file__).read_text(encoding="utf-8")
    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    forbidden = (
        "fastapi",
        "pydantic",
        "sqlite3",
        "psycopg",
        "supabase",
        "httpx",
        "requests",
        "freestack.infrastructure",
    )
    for name in imported:
        assert all(name != item and not name.startswith(f"{item}.") for item in forbidden)

    recommendation_source = Path(recommendation_module.__file__).read_text(encoding="utf-8")
    assert "freestack.application.composition" not in recommendation_source
    domain_root = Path(composition_module.__file__).parents[1] / "domain"
    for path in domain_root.rglob("*.py"):
        assert "freestack.application" not in path.read_text(encoding="utf-8")


def _recommendation(
    plan_id: str,
    unevaluated: frozenset[Feature] = frozenset(),
) -> RecommendationResult:
    plan = Plan(
        id=plan_id,
        service_id="alpha-platform",
        name="Database",
        slug="database",
        description="",
        capabilities=frozenset({CapabilityKey.DATABASE}),
    )
    provider = Provider(id="alpha", name="Alpha", slug="alpha", description="")
    service = Service(id="alpha-platform", provider_id="alpha", name="Platform", slug="platform", description="")
    evaluation = PlanEvaluation(
        plan=plan,
        role=Feature.DATABASE,
        capability_check=CheckResult(reason_code=ReasonCode.CAPABILITY_PROVIDED),
        quantity_checks=(),
        global_quantity_checks=(),
        budget_check=None,
    )
    return RecommendationResult(
        evaluation=RecommendationEvaluation(
            roles=(
                RoleEvaluation(
                    role=Feature.DATABASE,
                    compatible=(evaluation,),
                    unknown=(),
                    incompatible=(),
                ),
            ),
            unevaluated_features=unevaluated,
        ),
        plans=(
            PlanDetail(
                plan=plan,
                service=service,
                provider=provider,
                pricing=None,
                caveats=(),
                sources=(),
            ),
        ),
    )


def _composition(plan_id: str, budget_check: StackBudgetCheck | None = None) -> CompositionResult:
    stack = Stack(
        assignments=(
            RoleAssignment(
                feature=Feature.DATABASE,
                plan_id=plan_id,
                status=EvaluationStatus.COMPATIBLE,
            ),
        ),
        budget_check=budget_check,
    )
    return CompositionResult(
        status=CompositionStatus.COMPOSED,
        compatible=(stack,),
        unknown=(),
        incompatible=(),
        blocked_roles=(),
        combination_count=1,
        unevaluated_features=frozenset(),
    )
