import ast
from collections.abc import Mapping
from pathlib import Path

import pytest

from freestack.domain.capability import CapabilityKey
from freestack.domain.composition.budget import (
    apply_stack_budget,
    collect_plan_pricing,
    evaluate_stack_budget,
)
from freestack.domain.composition.models import (
    BlockedRole,
    BlockReason,
    CompositionResult,
    CompositionStatus,
    RoleAssignment,
    Stack,
)
from freestack.domain.feature import Feature
from freestack.domain.plan import Plan
from freestack.domain.pricing import ExceedBehavior, PlanPricing
from freestack.domain.recommendation.checks import (
    BudgetCheck,
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


def _plan(plan_id: str) -> Plan:
    return Plan(
        id=plan_id,
        service_id="example-service",
        name="Example",
        slug=plan_id,
        description="",
        capabilities=frozenset({CapabilityKey.DATABASE}),
    )


def _pricing(plan_id: str, fee: int, behavior: ExceedBehavior = ExceedBehavior.CHARGED) -> PlanPricing:
    return PlanPricing(
        plan_id=plan_id,
        monthly_base_fee_usd_cents=fee,
        exceed_behaviors=frozenset({behavior}),
        source_id="example-source",
    )


def _budget_check(reason: ReasonCode, pricing: PlanPricing | None) -> BudgetCheck:
    return BudgetCheck(reason_code=reason, pricing=pricing)


def _evaluation_for(
    plan: Plan,
    role: Feature,
    budget_check: CheckResult | None,
    *,
    unknown_limit: bool = False,
) -> PlanEvaluation:
    quantity = ()
    if unknown_limit:
        quantity = (LimitCheck(reason_code=ReasonCode.LIMIT_NOT_FOUND, limit=None, other_period_limits=()),)
    item = PlanEvaluation(
        plan=plan,
        role=role,
        capability_check=CheckResult(reason_code=ReasonCode.CAPABILITY_PROVIDED),
        quantity_checks=quantity,
        global_quantity_checks=(),
        budget_check=budget_check,
    )
    return item


def _role(feature: Feature, *items: PlanEvaluation) -> RoleEvaluation:
    return RoleEvaluation(
        role=feature,
        compatible=tuple(item for item in items if item.status is EvaluationStatus.COMPATIBLE),
        unknown=tuple(item for item in items if item.status is EvaluationStatus.UNKNOWN),
        incompatible=tuple(item for item in items if item.status is EvaluationStatus.INCOMPATIBLE),
    )


def _recommendation(*roles: RoleEvaluation) -> RecommendationEvaluation:
    return RecommendationEvaluation(roles=roles, unevaluated_features=frozenset())


def _assignment(
    feature: Feature,
    plan_id: str,
    status: EvaluationStatus = EvaluationStatus.COMPATIBLE,
) -> RoleAssignment:
    return RoleAssignment(feature=feature, plan_id=plan_id, status=status)


def _stack(*assignments: RoleAssignment) -> Stack:
    return Stack(assignments=assignments, budget_check=None)


def _composed(*stacks: Stack, unevaluated: frozenset[Feature] = frozenset()) -> CompositionResult:
    return CompositionResult(
        status=CompositionStatus.COMPOSED,
        compatible=tuple(stack for stack in stacks if stack.status is EvaluationStatus.COMPATIBLE),
        unknown=tuple(stack for stack in stacks if stack.status is EvaluationStatus.UNKNOWN),
        incompatible=tuple(stack for stack in stacks if stack.status is EvaluationStatus.INCOMPATIBLE),
        blocked_roles=(),
        combination_count=len(stacks),
        unevaluated_features=unevaluated,
    )


class _UnreadPricing(Mapping[str, PlanPricing]):
    def __getitem__(self, key: str) -> PlanPricing:
        raise AssertionError("pricing read")

    def __iter__(self):
        raise AssertionError("pricing read")

    def __len__(self) -> int:
        raise AssertionError("pricing read")


def test_collect_plan_pricing_reads_every_role_group_and_skips_missing_prices() -> None:
    priced = _pricing("plan-a", 500)
    unknown_priced = _pricing("plan-b", 100)
    rejected = _pricing("plan-c", 2000)
    evaluation = _recommendation(
        _role(
            Feature.DATABASE,
            _evaluation_for(_plan("plan-a"), Feature.DATABASE, _budget_check(ReasonCode.WITHIN_BUDGET, priced)),
            _evaluation_for(
                _plan("plan-b"),
                Feature.DATABASE,
                _budget_check(ReasonCode.WITHIN_BUDGET, unknown_priced),
                unknown_limit=True,
            ),
            _evaluation_for(
                _plan("plan-none"),
                Feature.DATABASE,
                _budget_check(ReasonCode.PRICING_NOT_FOUND, None),
            ),
            _evaluation_for(_plan("plan-c"), Feature.DATABASE, _budget_check(ReasonCode.OVER_BUDGET, rejected)),
        )
    )

    found = collect_plan_pricing(evaluation)

    assert found == {"plan-a": priced, "plan-b": unknown_priced, "plan-c": rejected}
    assert tuple(found) == ("plan-a", "plan-b", "plan-c")
    assert evaluation.roles[0].compatible[0].plan.id == "plan-a"
    assert evaluation.roles[0].unknown[0].plan.id == "plan-b"
    assert evaluation.roles[0].incompatible[0].plan.id == "plan-c"


def test_collect_plan_pricing_accepts_the_same_price_and_rejects_a_conflict() -> None:
    plan = _plan("plan-a")
    pricing = _pricing("plan-a", 500)
    other = _pricing("plan-a", 900)
    same = _recommendation(
        _role(Feature.DATABASE, _evaluation_for(plan, Feature.DATABASE, _budget_check(ReasonCode.WITHIN_BUDGET, pricing))),
        _role(Feature.FILE_UPLOADS, _evaluation_for(plan, Feature.FILE_UPLOADS, _budget_check(ReasonCode.WITHIN_BUDGET, pricing))),
    )
    both_missing = _recommendation(
        _role(Feature.DATABASE, _evaluation_for(plan, Feature.DATABASE, None)),
        _role(Feature.FILE_UPLOADS, _evaluation_for(plan, Feature.FILE_UPLOADS, None)),
    )

    assert collect_plan_pricing(same) == {"plan-a": pricing}
    assert collect_plan_pricing(both_missing) == {}
    with pytest.raises(ValueError, match=r"inconsistent pricing: plan-a"):
        collect_plan_pricing(
            _recommendation(
                _role(
                    Feature.DATABASE,
                    _evaluation_for(plan, Feature.DATABASE, _budget_check(ReasonCode.WITHIN_BUDGET, pricing)),
                ),
                _role(
                    Feature.FILE_UPLOADS,
                    _evaluation_for(plan, Feature.FILE_UPLOADS, _budget_check(ReasonCode.WITHIN_BUDGET, other)),
                ),
            )
        )
    with pytest.raises(ValueError, match=r"inconsistent pricing: plan-a"):
        collect_plan_pricing(
            _recommendation(
                _role(
                    Feature.DATABASE,
                    _evaluation_for(plan, Feature.DATABASE, _budget_check(ReasonCode.WITHIN_BUDGET, pricing)),
                ),
                _role(Feature.FILE_UPLOADS, _evaluation_for(plan, Feature.FILE_UPLOADS, None)),
            )
        )


def test_evaluate_stack_budget_uses_unique_plan_fees_and_budget_priority() -> None:
    pricing = {
        "plan-a": _pricing("plan-a", 500),
        "plan-b": _pricing("plan-b", 1000),
        "plan-c": _pricing("plan-c", 0),
        "plan-extra": _pricing("plan-extra", 9999),
    }

    within = evaluate_stack_budget(("plan-b", "plan-a"), monthly_budget_usd_cents=2000, pricing_by_plan=pricing)
    exact = evaluate_stack_budget(("plan-a", "plan-b"), monthly_budget_usd_cents=1500, pricing_by_plan=pricing)
    over = evaluate_stack_budget(("plan-a", "plan-b"), monthly_budget_usd_cents=1000, pricing_by_plan=pricing)
    missing = evaluate_stack_budget(("plan-a", "plan-d"), monthly_budget_usd_cents=2000, pricing_by_plan=pricing)
    missing_over = evaluate_stack_budget(("plan-a", "plan-b", "plan-d"), monthly_budget_usd_cents=1000, pricing_by_plan=pricing)
    all_missing = evaluate_stack_budget(("plan-d", "plan-e"), monthly_budget_usd_cents=0, pricing_by_plan={})
    free = evaluate_stack_budget(("plan-c",), monthly_budget_usd_cents=0, pricing_by_plan=pricing)
    duplicated = evaluate_stack_budget(("plan-a", "plan-a"), monthly_budget_usd_cents=500, pricing_by_plan=pricing)

    assert within.reason is ReasonCode.WITHIN_BUDGET
    assert within.priced_plan_ids == ("plan-a", "plan-b")
    assert within.unpriced_plan_ids == ()
    assert within.known_total_usd_cents == 1500
    assert exact.reason is ReasonCode.WITHIN_BUDGET
    assert over.reason is ReasonCode.OVER_BUDGET
    assert missing.reason is ReasonCode.PRICING_NOT_FOUND
    assert missing.priced_plan_ids == ("plan-a",)
    assert missing.unpriced_plan_ids == ("plan-d",)
    assert missing.known_total_usd_cents == 500
    assert missing_over.reason is ReasonCode.OVER_BUDGET
    assert missing_over.unpriced_plan_ids == ("plan-d",)
    assert all_missing.reason is ReasonCode.PRICING_NOT_FOUND
    assert all_missing.known_total_usd_cents == 0
    assert all_missing.unpriced_plan_ids == ("plan-d", "plan-e")
    assert free.reason is ReasonCode.WITHIN_BUDGET
    assert free.known_total_usd_cents == 0
    assert duplicated.known_total_usd_cents == 500
    assert duplicated.priced_plan_ids == ("plan-a",)
    assert "plan-extra" not in within.priced_plan_ids


@pytest.mark.parametrize("value", [True, False, -1, 1.5, "100"])
def test_evaluate_stack_budget_rejects_an_invalid_budget(value: object) -> None:
    with pytest.raises(ValueError, match=r"invalid monthly_budget_usd_cents:"):
        evaluate_stack_budget(("plan-a",), monthly_budget_usd_cents=value, pricing_by_plan={})  # type: ignore[arg-type]


def test_evaluate_stack_budget_rejects_a_mismatched_pricing_key() -> None:
    with pytest.raises(ValueError, match=r"invalid pricing:"):
        evaluate_stack_budget(
            ("plan-a",),
            monthly_budget_usd_cents=1000,
            pricing_by_plan={"plan-a": _pricing("plan-b", 500)},
        )


def test_exceed_behavior_does_not_change_the_stack_budget() -> None:
    charged = {"plan-a": _pricing("plan-a", 500, ExceedBehavior.CHARGED)}
    suspended = {"plan-a": _pricing("plan-a", 500, ExceedBehavior.SUSPENDED)}

    assert evaluate_stack_budget(("plan-a",), monthly_budget_usd_cents=500, pricing_by_plan=charged) == (
        evaluate_stack_budget(("plan-a",), monthly_budget_usd_cents=500, pricing_by_plan=suspended)
    )


def test_apply_stack_budget_regroups_stacks_without_changing_the_count() -> None:
    pricing = {
        "plan-a": _pricing("plan-a", 300),
        "plan-b": _pricing("plan-b", 500),
        "plan-d": _pricing("plan-d", 800),
        "plan-e": _pricing("plan-e", 700),
    }
    kept = _stack(_assignment(Feature.DATABASE, "plan-a"), _assignment(Feature.FILE_UPLOADS, "plan-b"))
    missing = _stack(_assignment(Feature.DATABASE, "plan-a"), _assignment(Feature.FILE_UPLOADS, "plan-c"))
    unknown_over = _stack(
        _assignment(Feature.DATABASE, "plan-d", EvaluationStatus.UNKNOWN),
        _assignment(Feature.FILE_UPLOADS, "plan-e"),
    )
    shared = _stack(_assignment(Feature.DATABASE, "plan-a"), _assignment(Feature.FILE_UPLOADS, "plan-a"))
    original = _composed(kept, missing, unknown_over, unevaluated=frozenset({Feature.AI_API}))

    result = apply_stack_budget(original, monthly_budget_usd_cents=1000, pricing_by_plan=pricing)
    shared_result = apply_stack_budget(_composed(shared), monthly_budget_usd_cents=300, pricing_by_plan=pricing)

    assert tuple(stack.sort_key for stack in result.compatible) == (("plan-a", "plan-b"),)
    assert result.compatible[0].budget_check is not None
    assert result.compatible[0].budget_check.reason is ReasonCode.WITHIN_BUDGET
    assert tuple(stack.sort_key for stack in result.unknown) == (("plan-a", "plan-c"),)
    assert result.unknown[0].budget_check is not None
    assert result.unknown[0].budget_check.reason is ReasonCode.PRICING_NOT_FOUND
    assert tuple(stack.sort_key for stack in result.incompatible) == (("plan-d", "plan-e"),)
    assert result.incompatible[0].budget_check is not None
    assert result.incompatible[0].budget_check.reason is ReasonCode.OVER_BUDGET
    assert result.combination_count == 3
    assert result.blocked_roles == ()
    assert result.unevaluated_features == frozenset({Feature.AI_API})
    assert original.compatible[0].budget_check is None
    assert shared_result.compatible[0].budget_check is not None
    assert shared_result.compatible[0].budget_check.known_total_usd_cents == 300
    assert shared_result.compatible[0].plan_ids == ("plan-a",)


def test_apply_stack_budget_sorts_a_regrouped_bucket() -> None:
    later = _stack(_assignment(Feature.DATABASE, "plan-b"))
    earlier = _stack(_assignment(Feature.DATABASE, "plan-a", EvaluationStatus.UNKNOWN))
    original = _composed(later, earlier)

    result = apply_stack_budget(original, monthly_budget_usd_cents=0, pricing_by_plan={})

    assert result.compatible == ()
    assert tuple(stack.sort_key for stack in result.unknown) == (("plan-a",), ("plan-b",))


def test_apply_stack_budget_keeps_unknown_when_the_budget_is_within() -> None:
    original = _composed(_stack(_assignment(Feature.DATABASE, "plan-a", EvaluationStatus.UNKNOWN)))

    result = apply_stack_budget(
        original,
        monthly_budget_usd_cents=500,
        pricing_by_plan={"plan-a": _pricing("plan-a", 100)},
    )

    assert result.compatible == ()
    assert result.unknown[0].status is EvaluationStatus.UNKNOWN
    assert result.unknown[0].budget_check is not None
    assert result.unknown[0].budget_check.reason is ReasonCode.WITHIN_BUDGET


def test_apply_stack_budget_rejects_a_stack_that_already_has_a_budget() -> None:
    priced = evaluate_stack_budget(("plan-a",), monthly_budget_usd_cents=100, pricing_by_plan={"plan-a": _pricing("plan-a", 0)})
    stack = Stack(assignments=(_assignment(Feature.DATABASE, "plan-a"),), budget_check=priced)
    original = CompositionResult(
        status=CompositionStatus.COMPOSED,
        compatible=(stack,),
        unknown=(),
        incompatible=(),
        blocked_roles=(),
        combination_count=1,
        unevaluated_features=frozenset(),
    )

    with pytest.raises(ValueError, match=r"budget already applied"):
        apply_stack_budget(original, monthly_budget_usd_cents=100, pricing_by_plan={})


@pytest.mark.parametrize(
    "status, blocked_roles, combination_count",
    [
        (CompositionStatus.NO_ROLES, (), 0),
        (CompositionStatus.BLOCKED, (BlockedRole(feature=Feature.DATABASE, reason=BlockReason.NO_CANDIDATES),), 0),
        (CompositionStatus.TOO_MANY_COMBINATIONS, (), 4),
    ],
)
def test_apply_stack_budget_returns_non_composed_results_unchanged(
    status: CompositionStatus,
    blocked_roles: tuple[BlockedRole, ...],
    combination_count: int,
) -> None:
    original = CompositionResult(
        status=status,
        compatible=(),
        unknown=(),
        incompatible=(),
        blocked_roles=blocked_roles,
        combination_count=combination_count,
        unevaluated_features=frozenset({Feature.AI_API}),
    )

    assert apply_stack_budget(original, monthly_budget_usd_cents=0, pricing_by_plan=_UnreadPricing()) is original
    with pytest.raises(ValueError, match=r"invalid monthly_budget_usd_cents:"):
        apply_stack_budget(original, monthly_budget_usd_cents=True, pricing_by_plan=_UnreadPricing())  # type: ignore[arg-type]


def test_budget_module_does_not_depend_on_application_infrastructure_or_repositories() -> None:
    budget = Path(__file__).parents[3] / "src" / "freestack" / "domain" / "composition" / "budget.py"
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
    imported: list[str] = []
    for node in ast.walk(ast.parse(budget.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    for name in imported:
        assert all(name != item and not name.startswith(f"{item}.") for item in forbidden)
