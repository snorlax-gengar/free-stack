import ast
from pathlib import Path

from freestack.domain.capability import CapabilityKey
from freestack.domain.feature import Feature
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.needs import BudgetNeed, CapabilityNeed, DerivedNeeds, QuantityNeed
from freestack.domain.plan import Plan
from freestack.domain.pricing import ExceedBehavior, PlanPricing
from freestack.domain.recommendation import evaluation
from freestack.domain.recommendation.checks import ReasonCode
from freestack.domain.recommendation.evaluation import (
    EvaluationStatus,
    PlanEvaluation,
    evaluate,
    evaluate_plan,
)
from freestack.domain.units import GB, MB


def _plan(plan_id: str, *capabilities: CapabilityKey) -> Plan:
    return Plan(
        id=plan_id,
        service_id="example-service",
        name="Example",
        slug=plan_id,
        description="",
        capabilities=frozenset(capabilities),
    )


def _limit(
    plan_id: str,
    metric: LimitMetric,
    period: LimitPeriod,
    value: int | None,
) -> Limit:
    return Limit(
        plan_id=plan_id,
        metric=metric,
        period=period,
        value=value,
        source_id="example-source",
    )


def _pricing(plan_id: str, fee: int) -> PlanPricing:
    return PlanPricing(
        plan_id=plan_id,
        monthly_base_fee_usd_cents=fee,
        exceed_behaviors=frozenset({ExceedBehavior.CHARGED}),
        source_id="example-source",
    )


def _database_and_uploads(*, budget: BudgetNeed | None) -> DerivedNeeds:
    return DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.FILE_UPLOADS, capability=CapabilityKey.FILE_STORAGE),
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
        ),
        quantities=(
            QuantityNeed(
                metric=LimitMetric.DATABASE_SIZE_BYTES,
                period=LimitPeriod.NONE,
                required=500 * MB,
                applies_to=Feature.DATABASE,
            ),
            QuantityNeed(
                metric=LimitMetric.FILE_STORAGE_BYTES,
                period=LimitPeriod.NONE,
                required=1 * GB,
                applies_to=Feature.FILE_UPLOADS,
            ),
            QuantityNeed(
                metric=LimitMetric.BANDWIDTH_BYTES,
                period=LimitPeriod.MONTH,
                required=5 * GB,
                applies_to=None,
            ),
        ),
        budget=budget,
        unevaluated_features=frozenset(),
    )


def test_plan_without_the_role_capability_is_not_evaluated() -> None:
    needs = _database_and_uploads(budget=None)
    file_plan = _plan("file-plan", CapabilityKey.FILE_STORAGE)

    assert evaluate_plan(file_plan, Feature.DATABASE, needs, (), None) is None


def test_plan_with_the_role_capability_is_evaluated() -> None:
    needs = _database_and_uploads(budget=BudgetNeed(max_monthly_usd_cents=0))
    plan = _plan("database-plan", CapabilityKey.DATABASE)
    limits = (
        _limit("database-plan", LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 500 * MB),
        _limit("database-plan", LimitMetric.FILE_STORAGE_BYTES, LimitPeriod.NONE, 1),
        _limit("database-plan", LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, 5 * GB),
    )

    result = evaluate_plan(plan, Feature.DATABASE, needs, limits, _pricing("database-plan", 0))

    assert result is not None
    assert result.plan is plan
    assert result.role is Feature.DATABASE
    assert result.capability_check.reason_code is ReasonCode.CAPABILITY_PROVIDED
    assert len(result.quantity_checks) == 1
    assert result.quantity_checks[0].reason_code is ReasonCode.WITHIN_LIMIT
    assert len(result.global_quantity_checks) == 1
    assert result.global_quantity_checks[0].reason_code is ReasonCode.WITHIN_LIMIT
    assert result.budget_check is not None
    assert result.budget_check.reason_code is ReasonCode.WITHIN_BUDGET
    assert result.status is EvaluationStatus.COMPATIBLE


def test_database_role_ignores_another_roles_quantity() -> None:
    needs = _database_and_uploads(budget=None)
    plan = _plan("database-plan", CapabilityKey.DATABASE)
    limits = (
        _limit("database-plan", LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 500 * MB),
        _limit("database-plan", LimitMetric.FILE_STORAGE_BYTES, LimitPeriod.NONE, 1),
        _limit("database-plan", LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, 10 * GB),
    )

    result = evaluate_plan(plan, Feature.DATABASE, needs, limits, None)

    assert result is not None
    assert result.quantity_checks[0].reason_code is ReasonCode.WITHIN_LIMIT
    assert result.status is EvaluationStatus.COMPATIBLE


def test_missing_budget_has_no_budget_check() -> None:
    needs = DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
        ),
        quantities=(),
        budget=None,
        unevaluated_features=frozenset(),
    )

    result = evaluate_plan(_plan("database-plan", CapabilityKey.DATABASE), Feature.DATABASE, needs, (), None)

    assert result is not None
    assert result.budget_check is None
    assert result.status is EvaluationStatus.COMPATIBLE


def test_missing_pricing_is_unknown_when_a_budget_exists() -> None:
    needs = DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
        ),
        quantities=(),
        budget=BudgetNeed(max_monthly_usd_cents=0),
        unevaluated_features=frozenset(),
    )

    result = evaluate_plan(_plan("database-plan", CapabilityKey.DATABASE), Feature.DATABASE, needs, (), None)

    assert result is not None
    assert result.budget_check is not None
    assert result.budget_check.reason_code is ReasonCode.PRICING_NOT_FOUND
    assert result.status is EvaluationStatus.UNKNOWN


def test_status_is_compatible_when_every_check_is_satisfied() -> None:
    result = _database_status(database_value=500 * MB, bandwidth_period=LimitPeriod.MONTH)

    assert result is not None
    assert result.status is EvaluationStatus.COMPATIBLE


def test_status_is_unknown_when_any_check_is_unknown() -> None:
    needs = _database_and_uploads(budget=BudgetNeed(max_monthly_usd_cents=0))
    plan = _plan("database-plan", CapabilityKey.DATABASE)
    limits = (
        _limit("database-plan", LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, 5 * GB),
    )

    result = evaluate_plan(plan, Feature.DATABASE, needs, limits, _pricing("database-plan", 0))

    assert result is not None
    assert result.quantity_checks[0].reason_code is ReasonCode.LIMIT_NOT_FOUND
    assert result.status is EvaluationStatus.UNKNOWN


def test_status_is_incompatible_when_any_check_is_violated() -> None:
    result = _database_status(database_value=1, bandwidth_period=LimitPeriod.DAY)

    assert result is not None
    assert result.quantity_checks[0].reason_code is ReasonCode.EXCEEDS_LIMIT
    assert result.global_quantity_checks[0].reason_code is ReasonCode.LIMIT_PERIOD_MISMATCH
    assert result.budget_check is not None
    assert result.budget_check.reason_code is ReasonCode.WITHIN_BUDGET
    assert result.status is EvaluationStatus.INCOMPATIBLE


def test_violated_outranks_unknown() -> None:
    needs = _database_and_uploads(budget=None)
    plan = _plan("database-plan", CapabilityKey.DATABASE)
    limits = (
        _limit("database-plan", LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 1),
        _limit("database-plan", LimitMetric.BANDWIDTH_BYTES, LimitPeriod.DAY, 5 * GB),
    )

    result = evaluate_plan(plan, Feature.DATABASE, needs, limits, None)

    assert result is not None
    assert result.status is EvaluationStatus.INCOMPATIBLE


def test_role_groups_plans_by_status_and_plan_id() -> None:
    needs = DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
        ),
        quantities=(
            QuantityNeed(
                metric=LimitMetric.DATABASE_SIZE_BYTES,
                period=LimitPeriod.NONE,
                required=100,
                applies_to=Feature.DATABASE,
            ),
        ),
        budget=None,
        unevaluated_features=frozenset(),
    )
    plans = (
        _plan("plan-d", CapabilityKey.DATABASE),
        _plan("plan-a", CapabilityKey.DATABASE),
        _plan("plan-c", CapabilityKey.DATABASE),
        _plan("plan-b", CapabilityKey.DATABASE),
    )
    limits_by_plan = {
        "plan-a": (_limit("plan-a", LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 100),),
        "plan-c": (_limit("plan-c", LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 200),),
        "plan-d": (_limit("plan-d", LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 1),),
    }

    role = evaluate(
        needs,
        plans,
        limits_by_plan,
        {},
    ).roles[0]
    again = evaluate(needs, tuple(reversed(plans)), limits_by_plan, {}).roles[0]

    assert role == again
    assert tuple(item.plan.id for item in role.compatible) == ("plan-a", "plan-c")
    assert tuple(item.plan.id for item in role.unknown) == ("plan-b",)
    assert tuple(item.plan.id for item in role.incompatible) == ("plan-d",)


def test_plans_stay_in_the_role_whose_capability_they_provide() -> None:
    needs = DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.FILE_UPLOADS, capability=CapabilityKey.FILE_STORAGE),
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
        ),
        quantities=(),
        budget=None,
        unevaluated_features=frozenset(),
    )
    database_plan = _plan("database-plan", CapabilityKey.DATABASE)
    file_plan = _plan("file-plan", CapabilityKey.FILE_STORAGE)

    result = evaluate(needs, (file_plan, database_plan), {}, {})

    assert tuple(role.role for role in result.roles) == (
        Feature.DATABASE,
        Feature.FILE_UPLOADS,
    )
    database_role, file_role = result.roles
    assert tuple(item.plan.id for item in database_role.compatible) == ("database-plan",)
    assert database_role.unknown == ()
    assert database_role.incompatible == ()
    assert tuple(item.plan.id for item in file_role.compatible) == ("file-plan",)
    assert file_role.unknown == ()
    assert file_role.incompatible == ()


def test_ai_api_stays_unevaluated_and_does_not_create_a_role() -> None:
    needs = DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
        ),
        quantities=(),
        budget=None,
        unevaluated_features=frozenset({Feature.AI_API}),
    )
    plan = _plan("database-plan", CapabilityKey.DATABASE)

    result = evaluate(needs, (plan,), {}, {})

    assert tuple(role.role for role in result.roles) == (Feature.DATABASE,)
    assert result.unevaluated_features == frozenset({Feature.AI_API})
    assert evaluate_plan(plan, Feature.AI_API, needs, (), None) is None


def test_role_with_no_candidate_plans_is_empty() -> None:
    needs = DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
        ),
        quantities=(),
        budget=None,
        unevaluated_features=frozenset(),
    )

    result = evaluate(needs, (), {}, {})

    assert len(result.roles) == 1
    assert result.roles[0].compatible == ()
    assert result.roles[0].unknown == ()
    assert result.roles[0].incompatible == ()


def test_requirement_with_only_unevaluated_features_has_no_roles() -> None:
    needs = DerivedNeeds(
        capabilities=(),
        quantities=(),
        budget=None,
        unevaluated_features=frozenset({Feature.AI_API}),
    )

    result = evaluate(needs, (_plan("database-plan", CapabilityKey.DATABASE),), {}, {})

    assert result.roles == ()
    assert result.unevaluated_features == frozenset({Feature.AI_API})


def test_role_order_follows_feature_definition_order() -> None:
    needs = DerivedNeeds(
        capabilities=(
            CapabilityNeed(feature=Feature.FILE_UPLOADS, capability=CapabilityKey.FILE_STORAGE),
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
            CapabilityNeed(
                feature=Feature.STATIC_FRONTEND,
                capability=CapabilityKey.STATIC_HOSTING,
            ),
        ),
        quantities=(),
        budget=None,
        unevaluated_features=frozenset(),
    )

    first = evaluate(needs, (), {}, {})
    second = evaluate(needs, (), {}, {})

    assert first == second
    assert tuple(role.role for role in first.roles) == (
        Feature.STATIC_FRONTEND,
        Feature.DATABASE,
        Feature.FILE_UPLOADS,
    )


def test_evaluation_does_not_import_infrastructure_or_frameworks() -> None:
    source = Path(evaluation.__file__).read_text(encoding="utf-8")
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
        "freestack.application",
        "freestack.domain.repositories",
    )
    for name in imported:
        assert all(
            name != forbidden_name and not name.startswith(f"{forbidden_name}.")
            for forbidden_name in forbidden
        )


def _database_status(
    *,
    database_value: int,
    bandwidth_period: LimitPeriod,
) -> PlanEvaluation | None:
    needs = _database_and_uploads(budget=BudgetNeed(max_monthly_usd_cents=0))
    plan = _plan("database-plan", CapabilityKey.DATABASE)
    limits = (
        _limit("database-plan", LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, database_value),
        _limit("database-plan", LimitMetric.BANDWIDTH_BYTES, bandwidth_period, 5 * GB),
    )
    return evaluate_plan(plan, Feature.DATABASE, needs, limits, _pricing("database-plan", 0))
