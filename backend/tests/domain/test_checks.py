import ast
from pathlib import Path

import pytest

from freestack.domain.capability import CapabilityKey
from freestack.domain.feature import Feature
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.needs import BudgetNeed, CapabilityNeed, QuantityNeed
from freestack.domain.plan import Plan
from freestack.domain.pricing import ExceedBehavior, PlanPricing
from freestack.domain.recommendation import checks
from freestack.domain.recommendation.checks import (
    CheckOutcome,
    CheckResult,
    ReasonCode,
    check_budget,
    check_capability,
    check_limit,
)
from freestack.domain.units import GB

REASON_OUTCOMES = (
    (ReasonCode.CAPABILITY_PROVIDED, CheckOutcome.SATISFIED),
    (ReasonCode.CAPABILITY_NOT_PROVIDED, CheckOutcome.VIOLATED),
    (ReasonCode.WITHIN_LIMIT, CheckOutcome.SATISFIED),
    (ReasonCode.UNLIMITED, CheckOutcome.SATISFIED),
    (ReasonCode.EXCEEDS_LIMIT, CheckOutcome.VIOLATED),
    (ReasonCode.LIMIT_NOT_FOUND, CheckOutcome.UNKNOWN),
    (ReasonCode.LIMIT_PERIOD_MISMATCH, CheckOutcome.UNKNOWN),
    (ReasonCode.WITHIN_BUDGET, CheckOutcome.SATISFIED),
    (ReasonCode.OVER_BUDGET, CheckOutcome.VIOLATED),
    (ReasonCode.PRICING_NOT_FOUND, CheckOutcome.UNKNOWN),
)


def _plan(*capabilities: CapabilityKey) -> Plan:
    return Plan(
        id="example-plan",
        service_id="example-service",
        name="Example",
        slug="example",
        description="",
        capabilities=frozenset(capabilities),
    )


def _need(capability: CapabilityKey) -> CapabilityNeed:
    feature = {
        CapabilityKey.DATABASE: Feature.DATABASE,
        CapabilityKey.FILE_STORAGE: Feature.FILE_UPLOADS,
        CapabilityKey.AUTHENTICATION: Feature.AUTHENTICATION,
        CapabilityKey.REALTIME: Feature.REALTIME,
    }[capability]
    return CapabilityNeed(feature=feature, capability=capability)


def _limit(metric: LimitMetric, period: LimitPeriod, value: int | None) -> Limit:
    return Limit(
        plan_id="example-plan",
        metric=metric,
        period=period,
        value=value,
        source_id="example-source",
    )


def _quantity(metric: LimitMetric, period: LimitPeriod, required: int) -> QuantityNeed:
    return QuantityNeed(
        metric=metric,
        period=period,
        required=required,
        applies_to=None,
    )


def _pricing(fee: int, *behaviors: ExceedBehavior) -> PlanPricing:
    if not behaviors:
        behaviors = (ExceedBehavior.CHARGED,)
    return PlanPricing(
        plan_id="example-plan",
        monthly_base_fee_usd_cents=fee,
        exceed_behaviors=frozenset(behaviors),
        source_id="example-source",
    )


@pytest.mark.parametrize(("reason", "outcome"), REASON_OUTCOMES)
def test_reason_code_determines_outcome(reason: ReasonCode, outcome: CheckOutcome) -> None:
    result = CheckResult(reason_code=reason)

    assert result.reason_code is reason
    assert result.outcome is outcome


def test_every_reason_code_has_one_outcome() -> None:
    assert {reason for reason, _outcome in REASON_OUTCOMES} == set(ReasonCode)


def test_capability_provided() -> None:
    result = check_capability(_plan(CapabilityKey.DATABASE), _need(CapabilityKey.DATABASE))

    assert result.reason_code is ReasonCode.CAPABILITY_PROVIDED
    assert result.outcome is CheckOutcome.SATISFIED


def test_capability_not_provided() -> None:
    result = check_capability(_plan(CapabilityKey.DATABASE), _need(CapabilityKey.FILE_STORAGE))

    assert result.reason_code is ReasonCode.CAPABILITY_NOT_PROVIDED
    assert result.outcome is CheckOutcome.VIOLATED


def test_other_capabilities_do_not_satisfy_a_missing_one() -> None:
    plan = _plan(
        CapabilityKey.DATABASE,
        CapabilityKey.AUTHENTICATION,
        CapabilityKey.REALTIME,
    )

    result = check_capability(plan, _need(CapabilityKey.FILE_STORAGE))

    assert result.reason_code is ReasonCode.CAPABILITY_NOT_PROVIDED
    assert result.outcome is CheckOutcome.VIOLATED


@pytest.mark.parametrize(
    ("required", "limit_value", "reason", "outcome"),
    [
        (5 * GB, 10 * GB, ReasonCode.WITHIN_LIMIT, CheckOutcome.SATISFIED),
        (10 * GB, 10 * GB, ReasonCode.WITHIN_LIMIT, CheckOutcome.SATISFIED),
        (11 * GB, 10 * GB, ReasonCode.EXCEEDS_LIMIT, CheckOutcome.VIOLATED),
    ],
)
def test_limit_compares_required_amount_with_the_exact_limit(
    required: int,
    limit_value: int,
    reason: ReasonCode,
    outcome: CheckOutcome,
) -> None:
    result = check_limit(
        (
            _limit(LimitMetric.FILE_STORAGE_BYTES, LimitPeriod.NONE, limit_value),
        ),
        _quantity(LimitMetric.FILE_STORAGE_BYTES, LimitPeriod.NONE, required),
    )

    assert result.reason_code is reason
    assert result.outcome is outcome


def test_unlimited_limit_satisfies_any_required_amount() -> None:
    result = check_limit(
        (_limit(LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, None),),
        _quantity(LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, 11 * GB),
    )

    assert result.reason_code is ReasonCode.UNLIMITED
    assert result.outcome is CheckOutcome.SATISFIED


def test_missing_metric_is_unknown() -> None:
    result = check_limit(
        (_limit(LimitMetric.FILE_STORAGE_BYTES, LimitPeriod.NONE, 10 * GB),),
        _quantity(LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 1 * GB),
    )

    assert result.reason_code is ReasonCode.LIMIT_NOT_FOUND
    assert result.outcome is CheckOutcome.UNKNOWN


def test_same_metric_with_another_period_is_unknown() -> None:
    result = check_limit(
        (_limit(LimitMetric.BANDWIDTH_BYTES, LimitPeriod.DAY, 10 * GB),),
        _quantity(LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, 5 * GB),
    )

    assert result.reason_code is ReasonCode.LIMIT_PERIOD_MISMATCH
    assert result.outcome is CheckOutcome.UNKNOWN


@pytest.mark.parametrize("reverse", [False, True])
def test_exact_period_is_used_when_another_period_is_also_present(reverse: bool) -> None:
    day = _limit(LimitMetric.BANDWIDTH_BYTES, LimitPeriod.DAY, 1)
    month = _limit(LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, 10 * GB)
    limits = (month, day) if reverse else (day, month)

    result = check_limit(
        limits,
        _quantity(LimitMetric.BANDWIDTH_BYTES, LimitPeriod.MONTH, 5 * GB),
    )

    assert result.reason_code is ReasonCode.WITHIN_LIMIT
    assert result.outcome is CheckOutcome.SATISFIED


@pytest.mark.parametrize("limits", [(), []])
def test_empty_limits_are_unknown(limits: list[Limit] | tuple[Limit, ...]) -> None:
    result = check_limit(
        limits,
        _quantity(LimitMetric.DATABASE_SIZE_BYTES, LimitPeriod.NONE, 1 * GB),
    )

    assert result.reason_code is ReasonCode.LIMIT_NOT_FOUND
    assert result.outcome is CheckOutcome.UNKNOWN


@pytest.mark.parametrize(
    ("fee", "budget", "reason", "outcome"),
    [
        (500, 1000, ReasonCode.WITHIN_BUDGET, CheckOutcome.SATISFIED),
        (1000, 1000, ReasonCode.WITHIN_BUDGET, CheckOutcome.SATISFIED),
        (1001, 1000, ReasonCode.OVER_BUDGET, CheckOutcome.VIOLATED),
        (0, 0, ReasonCode.WITHIN_BUDGET, CheckOutcome.SATISFIED),
    ],
)
def test_budget_compares_base_fee_with_the_maximum(
    fee: int,
    budget: int,
    reason: ReasonCode,
    outcome: CheckOutcome,
) -> None:
    result = check_budget(_pricing(fee), BudgetNeed(max_monthly_usd_cents=budget))

    assert result.reason_code is reason
    assert result.outcome is outcome


def test_missing_pricing_is_unknown() -> None:
    result = check_budget(None, BudgetNeed(max_monthly_usd_cents=0))

    assert result.reason_code is ReasonCode.PRICING_NOT_FOUND
    assert result.outcome is CheckOutcome.UNKNOWN


@pytest.mark.parametrize(
    "behavior",
    [ExceedBehavior.CHARGED, ExceedBehavior.SUSPENDED, ExceedBehavior.RESTRICTED],
)
def test_exceed_behavior_does_not_change_the_budget_result(behavior: ExceedBehavior) -> None:
    need = BudgetNeed(max_monthly_usd_cents=1000)
    within = check_budget(_pricing(500, behavior), need)
    over = check_budget(_pricing(1001, behavior), need)

    assert within.reason_code is ReasonCode.WITHIN_BUDGET
    assert within.outcome is CheckOutcome.SATISFIED
    assert over.reason_code is ReasonCode.OVER_BUDGET
    assert over.outcome is CheckOutcome.VIOLATED


def test_checks_do_not_import_infrastructure_or_frameworks() -> None:
    source = Path(checks.__file__).read_text(encoding="utf-8")
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
    )
    for name in imported:
        assert all(
            name != forbidden_name and not name.startswith(f"{forbidden_name}.")
            for forbidden_name in forbidden
        )
