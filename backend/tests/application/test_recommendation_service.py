import ast
from datetime import date
from pathlib import Path

import pytest

from freestack.application import recommendation as recommendation_module
from freestack.application.recommendation import RecommendationService
from freestack.domain.capability import CapabilityKey
from freestack.domain.caveat import Caveat
from freestack.domain.errors import DuplicateEntityError, RelatedEntityNotFoundError
from freestack.domain.feature import Feature
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.needs import derive_needs
from freestack.domain.plan import Plan
from freestack.domain.pricing import ExceedBehavior, PlanPricing
from freestack.domain.provider import Provider
from freestack.domain.recommendation.checks import CheckResult, ReasonCode
from freestack.domain.recommendation.evaluation import (
    PlanEvaluation,
    RecommendationEvaluation,
    RoleEvaluation,
    evaluate,
)
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.service import Service
from freestack.domain.source import Source
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository


def _catalog() -> InMemoryCatalogRepository:
    repository = InMemoryCatalogRepository()
    repository.add_provider(Provider(id="alpha", name="Alpha", slug="alpha", description=""))
    repository.add_provider(Provider(id="beta", name="Beta", slug="beta", description=""))
    repository.add_provider(Provider(id="gamma", name="Gamma", slug="gamma", description=""))
    repository.add_service(
        Service(
            id="alpha-database",
            provider_id="alpha",
            name="Database",
            slug="database",
            description="",
        )
    )
    repository.add_service(
        Service(
            id="alpha-platform",
            provider_id="alpha",
            name="Platform",
            slug="platform",
            description="",
        )
    )
    repository.add_service(
        Service(
            id="beta-storage",
            provider_id="beta",
            name="Storage",
            slug="storage",
            description="",
        )
    )
    repository.add_service(
        Service(
            id="gamma-pages",
            provider_id="gamma",
            name="Pages",
            slug="pages",
            description="",
        )
    )
    repository.add_plan(
        Plan(
            id="alpha-database-free",
            service_id="alpha-database",
            name="Free",
            slug="free",
            description="",
            capabilities=frozenset({CapabilityKey.DATABASE}),
        )
    )
    repository.add_plan(
        Plan(
            id="alpha-platform-free",
            service_id="alpha-platform",
            name="Free",
            slug="free",
            description="",
            capabilities=frozenset({CapabilityKey.DATABASE, CapabilityKey.FILE_STORAGE}),
        )
    )
    repository.add_plan(
        Plan(
            id="beta-storage-free",
            service_id="beta-storage",
            name="Free",
            slug="free",
            description="",
            capabilities=frozenset({CapabilityKey.FILE_STORAGE}),
        )
    )
    repository.add_plan(
        Plan(
            id="gamma-pages-free",
            service_id="gamma-pages",
            name="Free",
            slug="free",
            description="",
            capabilities=frozenset({CapabilityKey.STATIC_HOSTING}),
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
    repository.add_limit(
        Limit(
            plan_id="alpha-database-free",
            metric=LimitMetric.DATABASE_SIZE_BYTES,
            period=LimitPeriod.NONE,
            value=100,
            source_id="example-source",
        )
    )
    repository.add_limit(
        Limit(
            plan_id="alpha-platform-free",
            metric=LimitMetric.DATABASE_SIZE_BYTES,
            period=LimitPeriod.NONE,
            value=10,
            source_id="example-source",
        )
    )
    repository.add_limit(
        Limit(
            plan_id="alpha-platform-free",
            metric=LimitMetric.FILE_STORAGE_BYTES,
            period=LimitPeriod.NONE,
            value=1000,
            source_id="example-source",
        )
    )
    repository.add_limit(
        Limit(
            plan_id="beta-storage-free",
            metric=LimitMetric.FILE_STORAGE_BYTES,
            period=LimitPeriod.NONE,
            value=100,
            source_id="example-source",
        )
    )
    repository.add_plan_pricing(
        PlanPricing(
            plan_id="beta-storage-free",
            monthly_base_fee_usd_cents=0,
            exceed_behaviors=frozenset({ExceedBehavior.CHARGED}),
            source_id="example-source",
        )
    )
    return repository


def _requirement(**overrides: object) -> ProjectRequirement:
    values: dict[str, object] = {
        "features": frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
        "database_size_bytes": 50,
        "file_storage_bytes": 50,
    }
    values.update(overrides)
    return ProjectRequirement(**values)  # type: ignore[arg-type]


def _direct(repository: InMemoryCatalogRepository, requirement: ProjectRequirement):
    plans = repository.list_all_plans()
    limits_by_plan = {plan.id: repository.list_limits(plan.id) for plan in plans}
    pricing_by_plan = {}
    for plan in plans:
        pricing = repository.get_plan_pricing(plan.id)
        if pricing is not None:
            pricing_by_plan[plan.id] = pricing
    return evaluate(derive_needs(requirement), plans, limits_by_plan, pricing_by_plan)


class _NoCaveats:
    def list_caveats(self, plan_id: str) -> tuple[Caveat, ...]:
        return ()


def _service(catalog, caveats=None) -> RecommendationService:
    return RecommendationService(
        catalog=catalog,
        caveats=_NoCaveats() if caveats is None else caveats,
    )


class _RecordingRepository:
    def __init__(self, inner: InMemoryCatalogRepository) -> None:
        self.inner = inner
        self.service_ids: list[str] = []
        self.provider_ids: list[str] = []
        self.source_ids: list[str] = []

    def __getattr__(self, name: str):
        return getattr(self.inner, name)

    def get_service(self, service_id: str):
        self.service_ids.append(service_id)
        return self.inner.get_service(service_id)

    def get_provider(self, provider_id: str):
        self.provider_ids.append(provider_id)
        return self.inner.get_provider(provider_id)

    def get_source(self, source_id: str):
        self.source_ids.append(source_id)
        return self.inner.get_source(source_id)


def test_recommend_returns_engine_evaluation_unchanged() -> None:
    repository = _catalog()
    requirement = _requirement()

    result = _service(repository).recommend(requirement)

    assert result.evaluation == _direct(repository, requirement)
    database_role = result.evaluation.roles[0]
    assert tuple(item.plan.id for item in database_role.incompatible) == (
        "alpha-platform-free",
    )
    assert "alpha-platform-free" in {detail.plan.id for detail in result.plans}
    platform = next(detail for detail in result.plans if detail.plan.id == "alpha-platform-free")
    assert tuple(source.id for source in platform.sources) == ("example-source",)


def test_unknown_status_is_preserved_when_pricing_is_missing() -> None:
    repository = _catalog()
    requirement = _requirement(monthly_budget_usd_cents=0)

    result = _service(repository).recommend(requirement)

    assert result.evaluation == _direct(repository, requirement)
    database_role = next(role for role in result.evaluation.roles if role.role is Feature.DATABASE)
    assert tuple(item.plan.id for item in database_role.unknown) == ("alpha-database-free",)
    assert "alpha-database-free" not in {item.plan.id for item in database_role.compatible}


def test_shared_plan_is_detailed_once_and_distinct_plans_stay_separate() -> None:
    repository = _catalog()

    result = _service(repository).recommend(_requirement())

    assert tuple(detail.plan.id for detail in result.plans) == (
        "alpha-database-free",
        "alpha-platform-free",
        "beta-storage-free",
    )
    database_role, file_role = result.evaluation.roles
    assert "alpha-platform-free" in {item.plan.id for item in database_role.incompatible}
    assert "alpha-platform-free" in {item.plan.id for item in file_role.compatible}
    assert "beta-storage-free" in {item.plan.id for item in file_role.compatible}
    assert "alpha-database-free" not in {item.plan.id for item in (*file_role.compatible, *file_role.unknown, *file_role.incompatible)}


def test_plan_details_follow_service_and_provider_links() -> None:
    repository = _catalog()

    details = {
        detail.plan.id: detail
        for detail in _service(repository).recommend(_requirement()).plans
    }

    database = details["alpha-database-free"]
    assert database.service.id == "alpha-database"
    assert database.provider.id == "alpha"
    assert database.pricing is None

    storage = details["beta-storage-free"]
    assert storage.service.id == "beta-storage"
    assert storage.provider.id == "beta"
    assert storage.pricing == repository.get_plan_pricing("beta-storage-free")


def test_unused_plans_are_not_loaded_and_shared_providers_are_loaded_once() -> None:
    repository = _RecordingRepository(_catalog())

    _service(repository).recommend(_requirement())

    assert repository.service_ids == [
        "alpha-database",
        "alpha-platform",
        "beta-storage",
    ]
    assert repository.provider_ids == ["alpha", "beta"]


def test_empty_catalog_returns_an_empty_plan_list() -> None:
    repository = InMemoryCatalogRepository()
    requirement = ProjectRequirement(features=frozenset({Feature.DATABASE}))

    result = _service(repository).recommend(requirement)

    assert result.evaluation == _direct(repository, requirement)
    assert result.plans == ()


def test_ai_api_stays_unevaluated() -> None:
    repository = _RecordingRepository(_catalog())
    requirement = ProjectRequirement(features=frozenset({Feature.AI_API}))

    result = _service(repository).recommend(requirement)

    assert result.evaluation == _direct(repository.inner, requirement)
    assert result.evaluation.roles == ()
    assert result.evaluation.unevaluated_features == frozenset({Feature.AI_API})
    assert result.plans == ()
    assert repository.service_ids == []


def test_missing_service_raises() -> None:
    class _MissingService(_RecordingRepository):
        def get_service(self, service_id: str):
            self.service_ids.append(service_id)
            return None

    repository = _MissingService(_catalog())

    with pytest.raises(RelatedEntityNotFoundError, match="service not found"):
        _service(repository).recommend(_requirement())


def test_missing_provider_raises() -> None:
    class _MissingProvider(_RecordingRepository):
        def get_provider(self, provider_id: str):
            self.provider_ids.append(provider_id)
            return None

    repository = _MissingProvider(_catalog())

    with pytest.raises(RelatedEntityNotFoundError, match="provider not found"):
        _service(repository).recommend(_requirement())


def test_evaluation_plan_missing_from_catalog_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    ghost = Plan(
        id="ghost-plan",
        service_id="ghost-service",
        name="Ghost",
        slug="ghost-plan",
        description="",
        capabilities=frozenset({CapabilityKey.DATABASE}),
    )
    plan_evaluation = PlanEvaluation(
        plan=ghost,
        role=Feature.DATABASE,
        capability_check=CheckResult(reason_code=ReasonCode.CAPABILITY_PROVIDED),
        quantity_checks=(),
        global_quantity_checks=(),
        budget_check=None,
    )
    replacement = RecommendationEvaluation(
        roles=(
            RoleEvaluation(
                role=Feature.DATABASE,
                compatible=(plan_evaluation,),
                unknown=(),
                incompatible=(),
            ),
        ),
        unevaluated_features=frozenset(),
    )

    def _replace(*_args, **_kwargs):
        return replacement

    monkeypatch.setattr(recommendation_module, "evaluate", _replace)

    with pytest.raises(RelatedEntityNotFoundError, match="plan not found"):
        _service(_catalog()).recommend(
            ProjectRequirement(features=frozenset({Feature.DATABASE}))
        )


def test_repository_exception_propagates() -> None:
    class _FailingRepository:
        def list_all_plans(self) -> tuple[Plan, ...]:
            raise DuplicateEntityError("catalog failed")

    with pytest.raises(DuplicateEntityError, match="catalog failed"):
        _service(_FailingRepository()).recommend(  # type: ignore[arg-type]
            ProjectRequirement(features=frozenset({Feature.DATABASE}))
        )


def test_engine_exception_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    def _explode(*_args, **_kwargs):
        raise RuntimeError("engine failed")

    monkeypatch.setattr(recommendation_module, "evaluate", _explode)

    with pytest.raises(RuntimeError, match="engine failed"):
        _service(_catalog()).recommend(
            ProjectRequirement(features=frozenset({Feature.DATABASE}))
        )


class _ListedCaveats:
    def __init__(self, caveats_by_plan: dict[str, tuple[Caveat, ...]]) -> None:
        self.caveats_by_plan = caveats_by_plan
        self.plan_ids: list[str] = []

    def list_caveats(self, plan_id: str) -> tuple[Caveat, ...]:
        self.plan_ids.append(plan_id)
        return self.caveats_by_plan.get(plan_id, ())


def _caveat(plan_id: str, statement: str, source_id: str) -> Caveat:
    return Caveat(plan_id=plan_id, statement=statement, source_id=source_id)


def test_caveats_keep_catalog_order_and_are_loaded_once_for_a_shared_plan() -> None:
    repository = _catalog()
    caveats = _ListedCaveats(
        {
            "alpha-platform-free": (
                _caveat("alpha-platform-free", "First note.", "example-source"),
                _caveat("alpha-platform-free", "Second note.", "example-source"),
            ),
            "alpha-database-free": (),
        }
    )

    result = _service(repository, caveats).recommend(_requirement())

    detail = next(item for item in result.plans if item.plan.id == "alpha-platform-free")
    assert detail.caveats == caveats.caveats_by_plan["alpha-platform-free"]
    assert caveats.plan_ids.count("alpha-platform-free") == 1
    assert "alpha-platform-free" in {
        item.plan.id
        for role in result.evaluation.roles
        for item in role.incompatible
    }
    assert "gamma-pages-free" not in caveats.plan_ids
    assert next(item for item in result.plans if item.plan.id == "alpha-database-free").caveats == ()


def test_caveat_for_another_plan_is_rejected() -> None:
    caveats = _ListedCaveats(
        {
            "alpha-database-free": (
                _caveat("other-plan", "Wrong plan.", "example-source"),
            )
        }
    )

    with pytest.raises(RelatedEntityNotFoundError, match="caveat plan_id mismatch"):
        _service(_catalog(), caveats).recommend(
            ProjectRequirement(features=frozenset({Feature.DATABASE}))
        )


def test_different_caveats_do_not_change_evaluation() -> None:
    repository = _catalog()
    requirement = _requirement()
    first = _ListedCaveats(
        {"alpha-database-free": (_caveat("alpha-database-free", "Alpha note.", "example-source"),)}
    )
    second = _ListedCaveats(
        {"beta-storage-free": (_caveat("beta-storage-free", "Beta note.", "example-source"),)}
    )

    result_a = _service(repository, first).recommend(requirement)
    result_b = _service(repository, second).recommend(requirement)

    assert result_a.evaluation == result_b.evaluation == _direct(repository, requirement)
    assert result_a.plans[0].caveats != result_b.plans[0].caveats or result_a.plans[1].caveats != result_b.plans[1].caveats


def test_used_limit_sources_are_kept_and_unused_metrics_are_not() -> None:
    repository = _source_catalog()
    caveats = _NoCaveats()
    requirement = ProjectRequirement(
        features=frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
        database_size_bytes=50,
        file_storage_bytes=50,
        monthly_bandwidth_bytes=5,
    )

    result = _service(repository, caveats).recommend(requirement)
    details = {detail.plan.id: detail for detail in result.plans}

    assert tuple(source.id for source in details["database-plan"].sources) == ("database-source",)
    assert details["database-plan"].caveats == ()
    assert tuple(source.id for source in details["storage-plan"].sources) == (
        "pricing-source",
        "storage-source",
    )
    assert tuple(source.id for source in details["mismatch-plan"].sources) == ("day-source",)
    assert "unused-source" not in {
        source.id for detail in result.plans for source in detail.sources
    }
    database_role = next(role for role in result.evaluation.roles if role.role is Feature.DATABASE)
    assert "database-plan" in {item.plan.id for item in database_role.unknown}
    assert "mismatch-plan" in {item.plan.id for item in database_role.unknown}


def test_pricing_source_is_included_with_or_without_a_budget() -> None:
    repository = _source_catalog()
    priced = ProjectRequirement(features=frozenset({Feature.FILE_UPLOADS}))
    budgeted = ProjectRequirement(
        features=frozenset({Feature.FILE_UPLOADS}),
        monthly_budget_usd_cents=0,
    )

    without_budget = _service(repository).recommend(priced)
    with_budget = _service(repository).recommend(budgeted)
    storage = next(detail for detail in without_budget.plans if detail.plan.id == "storage-plan")
    budget_storage = next(detail for detail in with_budget.plans if detail.plan.id == "storage-plan")

    assert storage.pricing is not None
    assert tuple(source.id for source in storage.sources) == ("pricing-source",)
    assert tuple(source.id for source in budget_storage.sources) == ("pricing-source",)
    assert with_budget.evaluation == _direct(repository, budgeted)


def test_duplicate_sources_are_sorted_and_loaded_once() -> None:
    repository = _RecordingRepository(_source_catalog())
    caveats = _ListedCaveats(
        {
            "database-plan": (
                _caveat("database-plan", "Database note.", "z-source"),
                _caveat("database-plan", "Shared note.", "database-source"),
            ),
            "storage-plan": (_caveat("storage-plan", "Storage note.", "database-source"),),
        }
    )
    requirement = ProjectRequirement(
        features=frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
        database_size_bytes=50,
        file_storage_bytes=50,
    )

    result = _service(repository, caveats).recommend(requirement)
    database = next(detail for detail in result.plans if detail.plan.id == "database-plan")

    assert tuple(source.id for source in database.sources) == ("database-source", "z-source")
    assert repository.source_ids.count("database-source") == 1
    assert result.evaluation == _direct(repository.inner, requirement)


def test_missing_sources_fail_in_source_id_order() -> None:
    class _HiddenSources(_RecordingRepository):
        def get_source(self, source_id: str):
            self.source_ids.append(source_id)
            return None

    repository = _HiddenSources(_source_catalog())
    caveats = _ListedCaveats(
        {"database-plan": (_caveat("database-plan", "Database note.", "z-source"),)}
    )

    with pytest.raises(RelatedEntityNotFoundError, match="source not found: database-source"):
        _service(repository, caveats).recommend(
            ProjectRequirement(
                features=frozenset({Feature.DATABASE}),
                database_size_bytes=50,
            )
        )


def _source_catalog() -> InMemoryCatalogRepository:
    repository = InMemoryCatalogRepository()
    repository.add_provider(Provider(id="catalog", name="Catalog", slug="catalog", description=""))
    repository.add_service(
        Service(
            id="catalog-platform",
            provider_id="catalog",
            name="Platform",
            slug="platform",
            description="",
        )
    )
    repository.add_plan(
        Plan(
            id="database-plan",
            service_id="catalog-platform",
            name="Database",
            slug="database",
            description="",
            capabilities=frozenset({CapabilityKey.DATABASE}),
        )
    )
    repository.add_plan(
        Plan(
            id="storage-plan",
            service_id="catalog-platform",
            name="Storage",
            slug="storage",
            description="",
            capabilities=frozenset({CapabilityKey.FILE_STORAGE}),
        )
    )
    repository.add_plan(
        Plan(
            id="mismatch-plan",
            service_id="catalog-platform",
            name="Mismatch",
            slug="mismatch",
            description="",
            capabilities=frozenset({CapabilityKey.DATABASE, CapabilityKey.FILE_STORAGE}),
        )
    )
    for source_id in ("database-source", "storage-source", "unused-source", "day-source", "pricing-source", "z-source"):
        repository.add_source(
            Source(
                id=source_id,
                url=f"https://example.com/{source_id}",
                checked_at=date(2026, 9, 30),
                notes="",
            )
        )
    repository.add_limit(
        Limit(
            plan_id="database-plan",
            metric=LimitMetric.DATABASE_SIZE_BYTES,
            period=LimitPeriod.NONE,
            value=100,
            source_id="database-source",
        )
    )
    repository.add_limit(
        Limit(
            plan_id="database-plan",
            metric=LimitMetric.FILE_STORAGE_BYTES,
            period=LimitPeriod.NONE,
            value=1,
            source_id="unused-source",
        )
    )
    repository.add_limit(
        Limit(
            plan_id="storage-plan",
            metric=LimitMetric.FILE_STORAGE_BYTES,
            period=LimitPeriod.NONE,
            value=100,
            source_id="storage-source",
        )
    )
    repository.add_limit(
        Limit(
            plan_id="mismatch-plan",
            metric=LimitMetric.BANDWIDTH_BYTES,
            period=LimitPeriod.DAY,
            value=1,
            source_id="day-source",
        )
    )
    repository.add_plan_pricing(
        PlanPricing(
            plan_id="storage-plan",
            monthly_base_fee_usd_cents=0,
            exceed_behaviors=frozenset({ExceedBehavior.CHARGED}),
            source_id="pricing-source",
        )
    )
    return repository


def test_application_does_not_import_infrastructure_or_frameworks() -> None:
    source = Path(recommendation_module.__file__).read_text(encoding="utf-8")
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
        assert all(
            name != forbidden_name and not name.startswith(f"{forbidden_name}.")
            for forbidden_name in forbidden
        )

    domain_root = Path(recommendation_module.__file__).parents[1] / "domain"
    for path in domain_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "freestack.application" not in text
