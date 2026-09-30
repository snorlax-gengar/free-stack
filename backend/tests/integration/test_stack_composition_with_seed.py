from freestack.application.composition import StackCompositionService
from freestack.application.recommendation import RecommendationService
from freestack.domain.composition.models import BlockReason, CompositionStatus
from freestack.domain.feature import Feature
from freestack.domain.recommendation.checks import ReasonCode
from freestack.domain.recommendation.evaluation import EvaluationStatus
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.units import GB, MB
from freestack.infrastructure.catalog.caveats import SeedCaveatCatalog
from freestack.infrastructure.catalog.loader import load_catalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository


def _service(max_combinations: int) -> StackCompositionService:
    repository = InMemoryCatalogRepository()
    load_catalog(repository, ALL_BUNDLES)
    return StackCompositionService(
        recommendations=RecommendationService(catalog=repository, caveats=SeedCaveatCatalog()),
        max_combinations=max_combinations,
    )


def _backend_database_and_files(**overrides: object) -> ProjectRequirement:
    values: dict[str, object] = {
        "features": frozenset(
            {Feature.BACKEND_SERVER, Feature.DATABASE, Feature.FILE_UPLOADS}
        ),
        "file_storage_bytes": 500 * MB,
    }
    values.update(overrides)
    return ProjectRequirement(**values)  # type: ignore[arg-type]


def test_seed_catalog_composes_two_compatible_stacks_without_a_budget() -> None:
    result = _service(10).compose_stacks(_backend_database_and_files())

    assert result.composition.status is CompositionStatus.COMPOSED
    assert result.composition.combination_count == 2
    assert tuple(stack.sort_key for stack in result.composition.compatible) == (
        ("render-web-service-free", "supabase-platform-free", "cloudflare-r2-free"),
        ("render-web-service-free", "supabase-platform-free", "supabase-platform-free"),
    )
    assert result.composition.unknown == ()
    assert result.composition.incompatible == ()
    assert all(stack.budget_check is None for stack in result.composition.compatible)
    for stack in result.composition.compatible:
        details = result.stack_plan_details(stack)
        assert tuple(detail.plan.id for detail in details) == stack.plan_ids


def test_seed_catalog_marks_budgeted_stacks_unknown_without_pricing() -> None:
    result = _service(10).compose_stacks(_backend_database_and_files(monthly_budget_usd_cents=0))

    assert result.composition.status is CompositionStatus.COMPOSED
    assert result.composition.compatible == ()
    assert result.composition.combination_count == 2
    assert len(result.composition.unknown) == 2
    assert all(stack.status is EvaluationStatus.UNKNOWN for stack in result.composition.unknown)
    assert all(
        stack.budget_check is not None
        and stack.budget_check.reason is ReasonCode.PRICING_NOT_FOUND
        and stack.budget_check.budget_usd_cents == 0
        for stack in result.composition.unknown
    )


def test_seed_catalog_stops_when_the_combination_limit_is_one() -> None:
    result = _service(1).compose_stacks(_backend_database_and_files())

    assert result.composition.status is CompositionStatus.TOO_MANY_COMBINATIONS
    assert result.composition.combination_count == 2
    assert result.composition.compatible == result.composition.unknown == result.composition.incompatible == ()


def test_seed_catalog_blocks_authentication_and_realtime_when_bandwidth_exceeds() -> None:
    result = _service(10).compose_stacks(
        ProjectRequirement(
            features=frozenset({Feature.AUTHENTICATION, Feature.REALTIME}),
            monthly_bandwidth_bytes=10 * GB,
        )
    )

    assert result.composition.status is CompositionStatus.BLOCKED
    assert tuple((item.feature, item.reason) for item in result.composition.blocked_roles) == (
        (Feature.AUTHENTICATION, BlockReason.ALL_INCOMPATIBLE),
        (Feature.REALTIME, BlockReason.ALL_INCOMPATIBLE),
    )


def test_seed_catalog_leaves_ai_api_unevaluated() -> None:
    result = _service(10).compose_stacks(ProjectRequirement(features=frozenset({Feature.AI_API})))

    assert result.composition.status is CompositionStatus.NO_ROLES
    assert result.composition.combination_count == 0
    assert result.composition.unevaluated_features == frozenset({Feature.AI_API})
    assert result.recommendation.evaluation.unevaluated_features == frozenset({Feature.AI_API})
