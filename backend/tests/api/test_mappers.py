import ast
from datetime import date
from pathlib import Path

import pytest

from freestack.api import mappers, schemas
from freestack.api.mappers import to_response
from freestack.application.composition import StackCompositionResult, StackCompositionService
from freestack.application.recommendation import PlanDetail, RecommendationResult, RecommendationService
from freestack.domain.capability import CapabilityKey
from freestack.domain.caveat import Caveat
from freestack.domain.composition.models import (
    BlockedRole,
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
from freestack.domain.recommendation.checks import (
    BudgetCheck,
    CheckOutcome,
    CheckResult,
    LimitCheck,
    ReasonCode,
)
from freestack.domain.recommendation.evaluation import (
    EvaluationStatus,
    PlanEvaluation,
    RecommendationEvaluation,
    RoleEvaluation,
)
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.service import Service
from freestack.domain.source import Source
from freestack.infrastructure.catalog.caveats import SeedCaveatCatalog
from freestack.infrastructure.catalog.loader import load_catalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository


def test_response_echoes_the_requirement_in_feature_declaration_order() -> None:
    response = to_response(_result())

    assert response.requirement.features == [Feature.DATABASE, Feature.FILE_UPLOADS, Feature.AI_API]
    assert response.requirement.file_storage_bytes == 100
    assert response.requirement.database_size_bytes is None
    assert response.requirement.monthly_bandwidth_bytes is None
    assert response.requirement.monthly_budget_usd_cents == 500
    assert response.unevaluated_features == [Feature.AI_API]


def test_plans_are_keyed_by_plan_id_without_duplicating_a_shared_plan() -> None:
    response = to_response(_result())
    storage = response.plans["a-storage"]

    assert list(response.plans) == ["a-storage", "z-database"]
    assert storage.plan.id == "a-storage"
    assert storage.plan.service_id == "alpha-storage"
    assert storage.plan.capabilities == [
        CapabilityKey.SERVERLESS_FUNCTIONS,
        CapabilityKey.FILE_STORAGE,
    ]
    assert storage.service.provider_id == "alpha"
    assert storage.provider.slug == "alpha"
    assert storage.pricing is not None
    assert storage.pricing.monthly_base_fee_usd_cents == 0
    assert storage.pricing.exceed_behaviors == [
        ExceedBehavior.CHARGED,
        ExceedBehavior.SUSPENDED,
        ExceedBehavior.RESTRICTED,
    ]
    assert [caveat.statement for caveat in storage.caveats] == ["Keep backups.", "No SLA."]
    assert [caveat.plan_id for caveat in storage.caveats] == ["a-storage", "a-storage"]
    assert "caveat_id" not in storage.caveats[0].model_dump()
    assert [source.id for source in storage.sources] == ["source-a", "source-b"]
    assert response.sources["source-a"].checked_at == date(2026, 9, 30)
    assert list(response.sources) == ["source-a", "source-b"]
    assert response.plans["z-database"].pricing is None
    assert [source.id for source in response.plans["z-database"].sources] == ["source-a"]
    assert response.sources["source-a"] == storage.sources[0]


def test_evaluation_keeps_role_order_and_check_fields() -> None:
    response = to_response(_result())

    assert [role.role for role in response.roles] == [Feature.FILE_UPLOADS, Feature.DATABASE]
    uploads = response.roles[0].unknown[0]
    assert uploads.plan_id == "a-storage"
    assert uploads.status is EvaluationStatus.UNKNOWN
    assert uploads.capability_check.reason_code is ReasonCode.CAPABILITY_PROVIDED
    assert uploads.capability_check.outcome is CheckOutcome.SATISFIED
    assert uploads.budget_check is not None
    assert uploads.budget_check.reason_code is ReasonCode.WITHIN_BUDGET
    assert uploads.budget_check.pricing is not None
    assert uploads.budget_check.pricing.plan_id == "a-storage"
    dumped = uploads.model_dump()
    assert "kind" not in dumped
    assert "required" not in dumped["quantity_checks"][0]
    database = response.roles[1].unknown[0]
    assert database.plan_id == "z-database"
    assert database.budget_check is not None
    assert database.budget_check.pricing is None
    assert database.budget_check.reason_code is ReasonCode.PRICING_NOT_FOUND


def test_quantity_checks_keep_the_three_limit_states() -> None:
    checks = to_response(_result()).roles[0].unknown[0]
    missing, unlimited = checks.quantity_checks
    zero = checks.global_quantity_checks[0]

    assert missing.reason_code is ReasonCode.LIMIT_NOT_FOUND
    assert missing.limit is None
    assert unlimited.reason_code is ReasonCode.UNLIMITED
    assert unlimited.limit is not None
    assert unlimited.limit.value is None
    assert zero.reason_code is ReasonCode.WITHIN_LIMIT
    assert zero.limit is not None
    assert zero.limit.value == 0
    assert zero.other_period_limits[0].value == 10


def test_stack_key_is_stable_and_assignments_stay_independent_of_plan_ids() -> None:
    first = to_response(_result())
    second = to_response(_result())
    stack = first.composition.unknown[0]
    again = second.composition.unknown[0]

    assert stack.key == again.key
    assert stack.key != to_response(_result(storage_plan_id="b-storage")).composition.unknown[0].key
    assert [item.feature for item in stack.assignments] == [Feature.DATABASE, Feature.FILE_UPLOADS]
    assert [item.plan_id for item in stack.assignments] == ["z-database", "a-storage"]
    assert stack.plan_ids == ["a-storage", "z-database"]
    assert stack.status is EvaluationStatus.UNKNOWN
    assert stack.budget_check is not None
    assert stack.budget_check.budget_usd_cents == 500
    assert stack.budget_check.priced_plan_ids == ["z-database"]
    assert stack.budget_check.unpriced_plan_ids == ["a-storage"]
    assert stack.budget_check.known_total_usd_cents == 0
    assert stack.budget_check.reason is ReasonCode.PRICING_NOT_FOUND
    assert stack.budget_check.outcome is CheckOutcome.UNKNOWN


def test_missing_stack_budget_stays_null() -> None:
    detail = _catalog_plan(
        "z-database",
        service_id="alpha-database",
        slug="database",
        capabilities=frozenset({CapabilityKey.DATABASE}),
    )
    evaluation = PlanEvaluation(
        plan=detail.plan,
        role=Feature.DATABASE,
        capability_check=CheckResult(reason_code=ReasonCode.CAPABILITY_PROVIDED),
        quantity_checks=(),
        global_quantity_checks=(),
        budget_check=None,
    )
    stack = Stack(
        assignments=(
            RoleAssignment(
                feature=Feature.DATABASE,
                plan_id="z-database",
                status=EvaluationStatus.COMPATIBLE,
            ),
        ),
        budget_check=None,
    )
    response = to_response(
        StackCompositionResult(
            recommendation=RecommendationResult(
                evaluation=RecommendationEvaluation(
                    roles=(
                        RoleEvaluation(
                            role=Feature.DATABASE,
                            compatible=(evaluation,),
                            unknown=(),
                            incompatible=(),
                        ),
                    ),
                    unevaluated_features=frozenset(),
                ),
                plans=(detail,),
            ),
            composition=CompositionResult(
                status=CompositionStatus.COMPOSED,
                compatible=(stack,),
                unknown=(),
                incompatible=(),
                blocked_roles=(),
                combination_count=1,
                unevaluated_features=frozenset(),
            ),
            requirement=ProjectRequirement(features=frozenset({Feature.DATABASE})),
        )
    )

    assert response.composition.compatible[0].budget_check is None
    assert response.composition.compatible[0].status is EvaluationStatus.COMPATIBLE
    assert response.roles[0].compatible[0].budget_check is None


def test_composition_statuses_and_block_reasons_are_copied() -> None:
    blocked = to_response(_stopped(_blocked()))
    no_roles = to_response(_stopped(_empty(CompositionStatus.NO_ROLES)))
    too_many = to_response(_stopped(_empty(CompositionStatus.TOO_MANY_COMBINATIONS, count=4)))

    assert blocked.composition.status is CompositionStatus.BLOCKED
    assert [(role.feature, role.reason) for role in blocked.composition.blocked_roles] == [
        (Feature.DATABASE, BlockReason.NO_CANDIDATES),
        (Feature.FILE_UPLOADS, BlockReason.ALL_INCOMPATIBLE),
    ]
    assert blocked.composition.compatible == []
    assert no_roles.composition.status is CompositionStatus.NO_ROLES
    assert no_roles.composition.combination_count == 0
    assert too_many.composition.status is CompositionStatus.TOO_MANY_COMBINATIONS
    assert too_many.composition.combination_count == 4
    assert too_many.composition.blocked_roles == []


def test_seed_catalog_composition_maps_through_the_application_result() -> None:
    service = _seed_service(10)
    requirement = ProjectRequirement(
        features=frozenset({Feature.BACKEND_SERVER, Feature.DATABASE, Feature.FILE_UPLOADS}),
        file_storage_bytes=500_000_000,
    )
    result = service.compose_stacks(requirement)
    response = to_response(result)
    stack = result.composition.compatible[0]
    mapped = response.composition.compatible[0]

    assert response.requirement.monthly_budget_usd_cents is None
    assert response.composition.status is CompositionStatus.COMPOSED
    assert mapped.budget_check is None
    assert [item.plan_id for item in mapped.assignments] == [item.plan_id for item in stack.assignments]
    assert mapped.plan_ids == list(stack.plan_ids)
    assert mapped.plan_ids != [item.plan_id for item in mapped.assignments]
    assert list(response.plans) == [detail.plan.id for detail in result.recommendation.plans]
    assert len(response.plans) == len(set(response.plans))
    render = response.plans["render-web-service-free"]
    assert render.pricing is None
    assert render.caveats
    assert render.sources
    assert render.sources[0].id in response.sources

    budgeted = service.compose_stacks(
        ProjectRequirement(
            features=requirement.features,
            file_storage_bytes=500_000_000,
            monthly_budget_usd_cents=0,
        )
    )
    budget_response = to_response(budgeted)
    recorded = budgeted.composition.unknown[0].budget_check
    copied = budget_response.composition.unknown[0].budget_check
    assert recorded is not None
    assert copied is not None
    assert copied.reason is recorded.reason
    assert copied.known_total_usd_cents == recorded.known_total_usd_cents
    assert copied.unpriced_plan_ids == list(recorded.unpriced_plan_ids)
    assert copied.reason is ReasonCode.PRICING_NOT_FOUND


def test_seed_catalog_maps_stopped_composition_statuses() -> None:
    service = _seed_service(1)
    too_many = to_response(
        service.compose_stacks(
            ProjectRequirement(
                features=frozenset(
                    {Feature.BACKEND_SERVER, Feature.DATABASE, Feature.FILE_UPLOADS}
                ),
                file_storage_bytes=500_000_000,
            )
        )
    )
    blocked = to_response(
        _seed_service(10).compose_stacks(
            ProjectRequirement(
                features=frozenset({Feature.AUTHENTICATION, Feature.REALTIME}),
                monthly_bandwidth_bytes=10_000_000_000,
            )
        )
    )
    no_roles = to_response(
        _seed_service(10).compose_stacks(ProjectRequirement(features=frozenset({Feature.AI_API})))
    )

    assert too_many.composition.status is CompositionStatus.TOO_MANY_COMBINATIONS
    assert too_many.composition.combination_count == 2
    assert blocked.composition.status is CompositionStatus.BLOCKED
    assert [role.reason for role in blocked.composition.blocked_roles] == [
        BlockReason.ALL_INCOMPATIBLE,
        BlockReason.ALL_INCOMPATIBLE,
    ]
    assert no_roles.composition.status is CompositionStatus.NO_ROLES
    assert no_roles.unevaluated_features == [Feature.AI_API]


def test_schema_and_mapper_modules_do_not_call_infrastructure_or_rerun_composition() -> None:
    api_root = Path(mappers.__file__).parent
    forbidden = (
        "fastapi",
        "freestack.infrastructure",
        "freestack.domain.repositories",
        "freestack.domain.composition.composer",
        "freestack.domain.composition.budget",
    )
    calls = {"compose", "recommend", "evaluate", "apply_stack_budget", "collect_plan_pricing"}
    for path in (api_root / "schemas.py", api_root / "mappers.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.append(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in calls
        for name in imported:
            assert all(name != item and not name.startswith(f"{item}.") for item in forbidden)
    assert schemas.RecommendationRequest.model_config["extra"] == "forbid"


def _result(*, storage_plan_id: str = "a-storage") -> StackCompositionResult:
    storage = _catalog_plan(
        storage_plan_id,
        service_id="alpha-storage",
        slug="storage",
        capabilities=frozenset({CapabilityKey.FILE_STORAGE, CapabilityKey.SERVERLESS_FUNCTIONS}),
    )
    database = _catalog_plan(
        "z-database",
        service_id="alpha-database",
        slug="database",
        capabilities=frozenset({CapabilityKey.DATABASE}),
    )
    pricing = PlanPricing(
        plan_id=storage_plan_id,
        monthly_base_fee_usd_cents=0,
        exceed_behaviors=frozenset(
            {ExceedBehavior.RESTRICTED, ExceedBehavior.CHARGED, ExceedBehavior.SUSPENDED}
        ),
        source_id="source-a",
    )
    storage_evaluation = PlanEvaluation(
        plan=storage.plan,
        role=Feature.FILE_UPLOADS,
        capability_check=CheckResult(reason_code=ReasonCode.CAPABILITY_PROVIDED),
        quantity_checks=(
            LimitCheck(
                reason_code=ReasonCode.LIMIT_NOT_FOUND,
                limit=None,
                other_period_limits=(),
            ),
            LimitCheck(
                reason_code=ReasonCode.UNLIMITED,
                limit=_limit(storage_plan_id, None),
                other_period_limits=(),
            ),
        ),
        global_quantity_checks=(
            LimitCheck(
                reason_code=ReasonCode.WITHIN_LIMIT,
                limit=_limit(storage_plan_id, 0),
                other_period_limits=(_limit(storage_plan_id, 10, period=LimitPeriod.DAY),),
            ),
        ),
        budget_check=BudgetCheck(reason_code=ReasonCode.WITHIN_BUDGET, pricing=pricing),
    )
    database_evaluation = PlanEvaluation(
        plan=database.plan,
        role=Feature.DATABASE,
        capability_check=CheckResult(reason_code=ReasonCode.CAPABILITY_PROVIDED),
        quantity_checks=(),
        global_quantity_checks=(),
        budget_check=BudgetCheck(reason_code=ReasonCode.PRICING_NOT_FOUND, pricing=None),
    )
    if storage_evaluation.status is not EvaluationStatus.UNKNOWN:
        raise AssertionError(storage_evaluation.status)
    stack_budget = StackBudgetCheck(
        budget_usd_cents=500,
        priced_plan_ids=("z-database",),
        unpriced_plan_ids=(storage_plan_id,),
        known_total_usd_cents=0,
        reason=ReasonCode.PRICING_NOT_FOUND,
    )
    stack = Stack(
        assignments=(
            RoleAssignment(
                feature=Feature.DATABASE,
                plan_id="z-database",
                status=EvaluationStatus.UNKNOWN,
            ),
            RoleAssignment(
                feature=Feature.FILE_UPLOADS,
                plan_id=storage_plan_id,
                status=EvaluationStatus.UNKNOWN,
            ),
        ),
        budget_check=stack_budget,
    )
    group: dict[str, tuple[Stack, ...]] = {"compatible": (), "unknown": (), "incompatible": ()}
    group["unknown" if stack.status is EvaluationStatus.UNKNOWN else "compatible"] = (stack,)
    return StackCompositionResult(
        recommendation=RecommendationResult(
            evaluation=RecommendationEvaluation(
                roles=(
                    RoleEvaluation(
                        role=Feature.FILE_UPLOADS,
                        compatible=(),
                        unknown=(storage_evaluation,),
                        incompatible=(),
                    ),
                    RoleEvaluation(
                        role=Feature.DATABASE,
                        compatible=(),
                        unknown=(database_evaluation,),
                        incompatible=(),
                    ),
                ),
                unevaluated_features=frozenset({Feature.AI_API}),
            ),
            plans=(storage, database),
        ),
        composition=CompositionResult(
            status=CompositionStatus.COMPOSED,
            compatible=group["compatible"],
            unknown=group["unknown"],
            incompatible=group["incompatible"],
            blocked_roles=(),
            combination_count=1,
            unevaluated_features=frozenset({Feature.AI_API}),
        ),
        requirement=ProjectRequirement(
            features=frozenset({Feature.AI_API, Feature.FILE_UPLOADS, Feature.DATABASE}),
            file_storage_bytes=100,
            monthly_budget_usd_cents=500,
        ),
    )


def _catalog_plan(
    plan_id: str,
    *,
    service_id: str,
    slug: str,
    capabilities: frozenset[CapabilityKey],
) -> PlanDetail:
    provider = Provider(id="alpha", name="Alpha", slug="alpha", description="")
    service = Service(
        id=service_id,
        provider_id="alpha",
        name="Platform",
        slug=slug,
        description="",
    )
    plan = Plan(
        id=plan_id,
        service_id=service_id,
        name="Plan",
        slug=slug,
        description="",
        capabilities=capabilities,
    )
    sources = (
        (
            Source(id="source-a", url="https://example.test/a", checked_at=date(2026, 9, 30), notes=""),
            Source(id="source-b", url="https://example.test/b", checked_at=date(2026, 9, 30), notes="b"),
        )
        if plan_id != "z-database"
        else (
            Source(id="source-a", url="https://example.test/a", checked_at=date(2026, 9, 30), notes=""),
        )
    )
    caveats = (
        (
            Caveat(plan_id=plan_id, statement="Keep backups.", source_id="source-b"),
            Caveat(plan_id=plan_id, statement="No SLA.", source_id="source-a"),
        )
        if plan_id != "z-database"
        else ()
    )
    pricing = None
    if plan_id != "z-database":
        pricing = PlanPricing(
            plan_id=plan_id,
            monthly_base_fee_usd_cents=0,
            exceed_behaviors=frozenset(
                {ExceedBehavior.RESTRICTED, ExceedBehavior.CHARGED, ExceedBehavior.SUSPENDED}
            ),
            source_id="source-a",
        )
    return PlanDetail(
        plan=plan,
        service=service,
        provider=provider,
        pricing=pricing,
        caveats=caveats,
        sources=sources,
    )


def _limit(
    plan_id: str,
    value: int | None,
    *,
    period: LimitPeriod = LimitPeriod.MONTH,
) -> Limit:
    return Limit(
        plan_id=plan_id,
        metric=LimitMetric.FILE_STORAGE_BYTES,
        period=period,
        value=value,
        source_id="source-a",
    )


def _stopped(composition: CompositionResult) -> StackCompositionResult:
    return StackCompositionResult(
        recommendation=RecommendationResult(
            evaluation=RecommendationEvaluation(roles=(), unevaluated_features=frozenset({Feature.AI_API})),
            plans=(),
        ),
        composition=composition,
        requirement=ProjectRequirement(features=frozenset({Feature.AI_API})),
    )


def _blocked() -> CompositionResult:
    return CompositionResult(
        status=CompositionStatus.BLOCKED,
        compatible=(),
        unknown=(),
        incompatible=(),
        blocked_roles=(
            BlockedRole(feature=Feature.DATABASE, reason=BlockReason.NO_CANDIDATES),
            BlockedRole(feature=Feature.FILE_UPLOADS, reason=BlockReason.ALL_INCOMPATIBLE),
        ),
        combination_count=0,
        unevaluated_features=frozenset({Feature.AI_API}),
    )


def _empty(status: CompositionStatus, count: int = 0) -> CompositionResult:
    return CompositionResult(
        status=status,
        compatible=(),
        unknown=(),
        incompatible=(),
        blocked_roles=(),
        combination_count=count,
        unevaluated_features=frozenset({Feature.AI_API}),
    )


def _seed_service(max_combinations: int) -> StackCompositionService:
    repository = InMemoryCatalogRepository()
    load_catalog(repository, ALL_BUNDLES)
    return StackCompositionService(
        recommendations=RecommendationService(catalog=repository, caveats=SeedCaveatCatalog()),
        max_combinations=max_combinations,
    )


def test_response_models_do_not_invent_removed_contract_fields() -> None:
    response = to_response(_result())
    payload = response.model_dump()

    assert "budget" not in payload["composition"]["unknown"][0]
    assert "kind" not in payload["roles"][0]["unknown"][0]["capability_check"]
    with pytest.raises(AttributeError):
        _ = response.plans["a-storage"].caveats[0].caveat_id  # type: ignore[attr-defined]
