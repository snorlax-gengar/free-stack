import ast
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

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
from freestack.domain.recommendation.checks import CheckOutcome, ReasonCode
from freestack.domain.recommendation.evaluation import EvaluationStatus


def _assignment(
    feature: Feature = Feature.DATABASE,
    plan_id: str = "supabase-platform-free",
    status: EvaluationStatus = EvaluationStatus.COMPATIBLE,
) -> RoleAssignment:
    return RoleAssignment(feature=feature, plan_id=plan_id, status=status)


def _budget(
    priced: tuple[str, ...] = ("supabase-platform-free",),
    unpriced: tuple[str, ...] = (),
    *,
    budget: int = 0,
    total: int = 0,
    reason: ReasonCode = ReasonCode.WITHIN_BUDGET,
) -> StackBudgetCheck:
    return StackBudgetCheck(
        budget_usd_cents=budget,
        priced_plan_ids=priced,
        unpriced_plan_ids=unpriced,
        known_total_usd_cents=total,
        reason=reason,
    )


def _stack(
    *assignments: RoleAssignment,
    budget_check: StackBudgetCheck | None = None,
) -> Stack:
    return Stack(assignments=assignments or (_assignment(),), budget_check=budget_check)


def _result(**overrides: object) -> CompositionResult:
    values: dict[str, object] = {
        "status": CompositionStatus.COMPOSED,
        "compatible": (),
        "unknown": (),
        "incompatible": (),
        "blocked_roles": (),
        "combination_count": 0,
        "unevaluated_features": frozenset(),
    }
    values.update(overrides)
    return CompositionResult(**values)  # type: ignore[arg-type]


def test_role_assignment_accepts_compatible_and_unknown() -> None:
    compatible = _assignment()
    unknown = _assignment(status=EvaluationStatus.UNKNOWN)

    assert compatible.feature is Feature.DATABASE
    assert compatible.plan_id == "supabase-platform-free"
    assert compatible.status is EvaluationStatus.COMPATIBLE
    assert unknown.status is EvaluationStatus.UNKNOWN


def test_role_assignment_rejects_incompatible_status() -> None:
    with pytest.raises(ValueError, match=r"invalid status:"):
        _assignment(status=EvaluationStatus.INCOMPATIBLE)


def test_role_assignment_rejects_string_feature_and_status() -> None:
    with pytest.raises(ValueError, match=r"invalid feature:"):
        RoleAssignment(feature="database", plan_id="supabase-platform-free", status=EvaluationStatus.COMPATIBLE)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"invalid status:"):
        RoleAssignment(feature=Feature.DATABASE, plan_id="supabase-platform-free", status="compatible")  # type: ignore[arg-type]


@pytest.mark.parametrize("plan_id", ["", "Supabase", "supabase_platform"])
def test_role_assignment_rejects_invalid_plan_id(plan_id: str) -> None:
    with pytest.raises(ValueError, match=r"invalid plan_id:"):
        _assignment(plan_id=plan_id)


def test_role_assignment_is_immutable() -> None:
    assignment = _assignment()

    with pytest.raises(FrozenInstanceError):
        assignment.plan_id = "render-web-service-free"  # type: ignore[misc]


def test_budget_check_accepts_the_three_budget_reasons() -> None:
    within = _budget()
    over = _budget(budget=100, total=101, reason=ReasonCode.OVER_BUDGET)
    missing = _budget(
        priced=(),
        unpriced=("supabase-platform-free",),
        budget=100,
        total=0,
        reason=ReasonCode.PRICING_NOT_FOUND,
    )
    over_with_gap = _budget(
        priced=("render-web-service-free",),
        unpriced=("supabase-platform-free",),
        budget=100,
        total=101,
        reason=ReasonCode.OVER_BUDGET,
    )

    assert within.outcome is CheckOutcome.SATISFIED
    assert over.outcome is CheckOutcome.VIOLATED
    assert missing.outcome is CheckOutcome.UNKNOWN
    assert over_with_gap.reason is ReasonCode.OVER_BUDGET
    assert "outcome" not in StackBudgetCheck.__dataclass_fields__


@pytest.mark.parametrize("amount", [True, False, -1])
def test_budget_check_rejects_bool_and_negative_amounts(amount: object) -> None:
    with pytest.raises(ValueError, match=r"invalid budget_usd_cents:"):
        _budget(budget=amount)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"invalid known_total_usd_cents:"):
        _budget(total=amount)  # type: ignore[arg-type]


def test_budget_check_rejects_a_non_budget_reason() -> None:
    with pytest.raises(ValueError, match=r"invalid reason:"):
        _budget(reason=ReasonCode.WITHIN_LIMIT)


def test_budget_check_rejects_unsorted_or_duplicate_plan_ids() -> None:
    with pytest.raises(ValueError, match=r"invalid priced_plan_ids:"):
        _budget(priced=("supabase-platform-free", "render-web-service-free"))
    with pytest.raises(ValueError, match=r"invalid unpriced_plan_ids:"):
        _budget(
            priced=(),
            unpriced=("supabase-platform-free", "supabase-platform-free"),
            reason=ReasonCode.PRICING_NOT_FOUND,
        )


def test_budget_check_rejects_overlap_and_an_empty_plan_set() -> None:
    with pytest.raises(ValueError, match=r"invalid plan ids:"):
        _budget(
            priced=("supabase-platform-free",),
            unpriced=("supabase-platform-free",),
            reason=ReasonCode.PRICING_NOT_FOUND,
        )
    with pytest.raises(ValueError, match=r"invalid plan ids:"):
        _budget(priced=(), unpriced=())


def test_budget_check_rejects_a_reason_that_disagrees_with_the_amounts() -> None:
    with pytest.raises(ValueError, match=r"invalid reason:"):
        _budget(budget=100, total=101, reason=ReasonCode.WITHIN_BUDGET)
    with pytest.raises(ValueError, match=r"invalid reason:"):
        _budget(
            priced=(),
            unpriced=("supabase-platform-free",),
            budget=100,
            reason=ReasonCode.WITHIN_BUDGET,
        )
    with pytest.raises(ValueError, match=r"invalid reason:"):
        _budget(reason=ReasonCode.PRICING_NOT_FOUND)


def test_stack_keeps_assignments_and_derives_plan_identity() -> None:
    stack = _stack(
        _assignment(Feature.BACKEND_SERVER, "render-web-service-free"),
        _assignment(Feature.DATABASE, "supabase-platform-free"),
        _assignment(Feature.FILE_UPLOADS, "supabase-platform-free"),
    )

    assert stack.features == (
        Feature.BACKEND_SERVER,
        Feature.DATABASE,
        Feature.FILE_UPLOADS,
    )
    assert stack.plan_ids == ("render-web-service-free", "supabase-platform-free")
    assert stack.sort_key == (
        "render-web-service-free",
        "supabase-platform-free",
        "supabase-platform-free",
    )
    assert stack.status is EvaluationStatus.COMPATIBLE


def test_stack_rejects_empty_duplicate_or_unsorted_assignments() -> None:
    with pytest.raises(ValueError, match=r"invalid assignments:"):
        Stack(assignments=(), budget_check=None)
    with pytest.raises(ValueError, match=r"invalid assignments:"):
        _stack(_assignment(), _assignment(plan_id="other-platform-free"))
    with pytest.raises(ValueError, match=r"invalid assignments:"):
        _stack(
            _assignment(Feature.DATABASE, "supabase-platform-free"),
            _assignment(Feature.BACKEND_SERVER, "render-web-service-free"),
        )


def test_stack_status_follows_assignments_and_budget() -> None:
    unknown = _stack(_assignment(status=EvaluationStatus.UNKNOWN))
    over = _stack(budget_check=_budget(budget=100, total=101, reason=ReasonCode.OVER_BUDGET))
    unknown_over = _stack(
        _assignment(status=EvaluationStatus.UNKNOWN),
        budget_check=_budget(budget=100, total=101, reason=ReasonCode.OVER_BUDGET),
    )

    assert unknown.status is EvaluationStatus.UNKNOWN
    assert over.status is EvaluationStatus.INCOMPATIBLE
    assert unknown_over.status is EvaluationStatus.INCOMPATIBLE


def test_stack_rejects_a_budget_check_for_a_different_plan_set() -> None:
    with pytest.raises(ValueError, match=r"invalid budget_check:"):
        _stack(budget_check=_budget(priced=("render-web-service-free",)))


def test_stack_is_immutable() -> None:
    stack = _stack()

    with pytest.raises(FrozenInstanceError):
        stack.budget_check = None  # type: ignore[misc]


def test_blocked_role_accepts_both_reasons() -> None:
    missing = BlockedRole(feature=Feature.DATABASE, reason=BlockReason.NO_CANDIDATES)
    incompatible = BlockedRole(feature=Feature.DATABASE, reason=BlockReason.ALL_INCOMPATIBLE)

    assert missing.reason is BlockReason.NO_CANDIDATES
    assert incompatible.reason is BlockReason.ALL_INCOMPATIBLE


def test_blocked_role_rejects_plain_strings() -> None:
    with pytest.raises(ValueError, match=r"invalid feature:"):
        BlockedRole(feature="database", reason=BlockReason.NO_CANDIDATES)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"invalid reason:"):
        BlockedRole(feature=Feature.DATABASE, reason="no-candidates")  # type: ignore[arg-type]


def test_composition_status_values() -> None:
    assert tuple(status.value for status in CompositionStatus) == (
        "composed",
        "blocked",
        "too-many-combinations",
        "no-roles",
    )


def test_composed_result_groups_stacks_by_their_status() -> None:
    compatible = _stack(_assignment(plan_id="alpha-plan"))
    unknown = _stack(_assignment(plan_id="beta-plan", status=EvaluationStatus.UNKNOWN))
    incompatible = _stack(
        _assignment(plan_id="gamma-plan"),
        budget_check=_budget(
            priced=("gamma-plan",),
            budget=100,
            total=101,
            reason=ReasonCode.OVER_BUDGET,
        ),
    )

    result = _result(
        compatible=(compatible,),
        unknown=(unknown,),
        incompatible=(incompatible,),
        combination_count=3,
        unevaluated_features=frozenset({Feature.AI_API}),
    )

    assert result.compatible[0].status is EvaluationStatus.COMPATIBLE
    assert result.unknown[0].status is EvaluationStatus.UNKNOWN
    assert result.incompatible[0].status is EvaluationStatus.INCOMPATIBLE
    assert result.unevaluated_features == frozenset({Feature.AI_API})


def test_non_composed_result_rejects_stacks() -> None:
    with pytest.raises(ValueError, match=r"invalid status:"):
        _result(
            status=CompositionStatus.BLOCKED,
            compatible=(_stack(),),
            blocked_roles=(BlockedRole(feature=Feature.DATABASE, reason=BlockReason.NO_CANDIDATES),),
            combination_count=0,
        )


def test_blocked_result_requires_blocked_roles() -> None:
    with pytest.raises(ValueError, match=r"invalid blocked_roles:"):
        _result(status=CompositionStatus.BLOCKED)

    result = _result(
        status=CompositionStatus.BLOCKED,
        blocked_roles=(
            BlockedRole(feature=Feature.DATABASE, reason=BlockReason.NO_CANDIDATES),
            BlockedRole(feature=Feature.FILE_UPLOADS, reason=BlockReason.ALL_INCOMPATIBLE),
        ),
    )

    assert result.compatible == ()
    assert result.blocked_roles[0].feature is Feature.DATABASE


def test_no_roles_result_is_empty() -> None:
    result = _result(status=CompositionStatus.NO_ROLES)

    assert result.compatible == result.unknown == result.incompatible == ()
    assert result.blocked_roles == ()
    assert result.combination_count == 0

    with pytest.raises(ValueError, match=r"invalid combination_count:"):
        _result(status=CompositionStatus.NO_ROLES, combination_count=1)


def test_too_many_combinations_keeps_the_count_without_stacks() -> None:
    result = _result(status=CompositionStatus.TOO_MANY_COMBINATIONS, combination_count=12)

    assert result.compatible == ()
    assert result.combination_count == 12

    with pytest.raises(ValueError, match=r"invalid status:"):
        _result(
            status=CompositionStatus.TOO_MANY_COMBINATIONS,
            compatible=(_stack(),),
            combination_count=12,
        )


def test_composed_result_rejects_a_stack_in_the_wrong_group() -> None:
    with pytest.raises(ValueError, match=r"invalid compatible:"):
        _result(
            compatible=(_stack(_assignment(status=EvaluationStatus.UNKNOWN)),),
            combination_count=1,
        )


def test_composed_result_rejects_unsorted_or_duplicate_stacks() -> None:
    first = _stack(_assignment(plan_id="alpha-plan"))
    second = _stack(_assignment(plan_id="beta-plan"))

    with pytest.raises(ValueError, match=r"invalid compatible:"):
        _result(compatible=(second, first), combination_count=2)
    with pytest.raises(ValueError, match=r"invalid compatible:"):
        _result(compatible=(first, first), combination_count=2)


def test_composed_result_rejects_a_count_that_omits_stacks() -> None:
    with pytest.raises(ValueError, match=r"invalid combination_count:"):
        _result(compatible=(_stack(),), combination_count=2)


def test_composition_result_rejects_unsorted_blocked_roles_and_bad_counts() -> None:
    with pytest.raises(ValueError, match=r"invalid blocked_roles:"):
        _result(
            status=CompositionStatus.BLOCKED,
            blocked_roles=(
                BlockedRole(feature=Feature.FILE_UPLOADS, reason=BlockReason.NO_CANDIDATES),
                BlockedRole(feature=Feature.DATABASE, reason=BlockReason.NO_CANDIDATES),
            ),
        )
    with pytest.raises(ValueError, match=r"invalid combination_count:"):
        _result(combination_count=-1)
    with pytest.raises(ValueError, match=r"invalid unevaluated_features:"):
        _result(unevaluated_features=frozenset({"ai-api"}))  # type: ignore[arg-type]


def test_composition_does_not_depend_on_infrastructure_application_or_repositories() -> None:
    package = Path(__file__).parents[3] / "src" / "freestack" / "domain" / "composition"
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
    imported = _imported_modules(package)
    for name in imported:
        assert all(name != item and not name.startswith(f"{item}.") for item in forbidden)

    recommendation = package.parent / "recommendation"
    assert all(
        "freestack.domain.composition" not in name for name in _imported_modules(recommendation)
    )


def _imported_modules(package: Path) -> list[str]:
    imported: list[str] = []
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.append(node.module)
    return imported
