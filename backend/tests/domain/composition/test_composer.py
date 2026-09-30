import ast
from pathlib import Path

import pytest

from freestack.domain.capability import CapabilityKey
from freestack.domain.composition.composer import compose
from freestack.domain.composition.models import BlockReason, CompositionStatus
from freestack.domain.feature import Feature
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.needs import derive_needs
from freestack.domain.plan import Plan
from freestack.domain.recommendation.evaluation import (
    EvaluationStatus,
    RecommendationEvaluation,
    evaluate,
)
from freestack.domain.requirement import ProjectRequirement


def _plan(plan_id: str, *capabilities: CapabilityKey) -> Plan:
    return Plan(
        id=plan_id,
        service_id="example-service",
        name="Example",
        slug=plan_id,
        description="",
        capabilities=frozenset(capabilities),
    )


def _limit(plan_id: str, metric: LimitMetric, value: int) -> Limit:
    return Limit(
        plan_id=plan_id,
        metric=metric,
        period=LimitPeriod.NONE,
        value=value,
        source_id="example-source",
    )


def _evaluation(
    features: frozenset[Feature],
    plans: list[Plan],
    limits_by_plan: dict[str, tuple[Limit, ...]] | None = None,
    **requirement: object,
) -> RecommendationEvaluation:
    needs = derive_needs(ProjectRequirement(features=features, **requirement))  # type: ignore[arg-type]
    return evaluate(needs, plans, limits_by_plan or {}, {})


def test_max_combinations_accepts_one() -> None:
    evaluation = _evaluation(frozenset({Feature.DATABASE}), [_plan("plan-a", CapabilityKey.DATABASE)])

    result = compose(evaluation, max_combinations=1)

    assert result.status is CompositionStatus.COMPOSED
    assert result.combination_count == 1


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "10"])
def test_max_combinations_rejects_values_below_one(value: object) -> None:
    evaluation = _evaluation(frozenset({Feature.AI_API}), [])

    with pytest.raises(ValueError, match=r"invalid max_combinations:"):
        compose(evaluation, max_combinations=value)  # type: ignore[arg-type]


def test_invalid_max_combinations_is_rejected_before_no_roles() -> None:
    evaluation = _evaluation(frozenset({Feature.AI_API}), [])
    assert evaluation.roles == ()

    with pytest.raises(ValueError, match=r"invalid max_combinations:"):
        compose(evaluation, max_combinations=0)


def test_no_roles_returns_an_empty_result_and_keeps_unevaluated_features() -> None:
    evaluation = _evaluation(frozenset({Feature.AI_API}), [])

    result = compose(evaluation, max_combinations=10)

    assert result.status is CompositionStatus.NO_ROLES
    assert result.combination_count == 0
    assert result.compatible == result.unknown == result.incompatible == ()
    assert result.blocked_roles == ()
    assert result.unevaluated_features == frozenset({Feature.AI_API})


def test_one_role_with_three_candidates_returns_three_stacks() -> None:
    evaluation = _evaluation(
        frozenset({Feature.DATABASE}),
        [
            _plan("plan-c", CapabilityKey.DATABASE),
            _plan("plan-a", CapabilityKey.DATABASE),
            _plan("plan-b", CapabilityKey.DATABASE),
        ],
    )

    result = compose(evaluation, max_combinations=10)

    assert result.status is CompositionStatus.COMPOSED
    assert tuple(stack.sort_key for stack in result.compatible) == (
        ("plan-a",),
        ("plan-b",),
        ("plan-c",),
    )
    assert result.unknown == ()
    assert result.incompatible == ()


def test_cartesian_product_covers_every_complete_assignment() -> None:
    two_by_two = _evaluation(
        frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
        [
            _plan("beta-db", CapabilityKey.DATABASE),
            _plan("alpha-db", CapabilityKey.DATABASE),
            _plan("beta-file", CapabilityKey.FILE_STORAGE),
            _plan("alpha-file", CapabilityKey.FILE_STORAGE),
        ],
    )
    two_by_two_by_one = _evaluation(
        frozenset({Feature.DATABASE, Feature.FILE_UPLOADS, Feature.BACKEND_SERVER}),
        [
            _plan("beta-db", CapabilityKey.DATABASE),
            _plan("alpha-db", CapabilityKey.DATABASE),
            _plan("beta-file", CapabilityKey.FILE_STORAGE),
            _plan("alpha-file", CapabilityKey.FILE_STORAGE),
            _plan("gamma-server", CapabilityKey.SERVER_COMPUTE),
        ],
    )

    pairs = compose(two_by_two, max_combinations=4)
    triples = compose(two_by_two_by_one, max_combinations=4)

    assert tuple(stack.sort_key for stack in pairs.compatible) == (
        ("alpha-db", "alpha-file"),
        ("alpha-db", "beta-file"),
        ("beta-db", "alpha-file"),
        ("beta-db", "beta-file"),
    )
    assert triples.combination_count == 4
    assert triples.compatible[0].features == (
        Feature.BACKEND_SERVER,
        Feature.DATABASE,
        Feature.FILE_UPLOADS,
    )
    assert triples.compatible[0].sort_key == ("gamma-server", "alpha-db", "alpha-file")


def test_compatible_and_unknown_are_candidates_and_incompatible_is_not() -> None:
    ok = _plan("plan-ok", CapabilityKey.DATABASE)
    missing = _plan("plan-a", CapabilityKey.DATABASE)
    exceeded = _plan("plan-bad", CapabilityKey.DATABASE)
    evaluation = _evaluation(
        frozenset({Feature.DATABASE}),
        [exceeded, ok, missing],
        {
            ok.id: (_limit(ok.id, LimitMetric.DATABASE_SIZE_BYTES, 100),),
            exceeded.id: (_limit(exceeded.id, LimitMetric.DATABASE_SIZE_BYTES, 1),),
        },
        database_size_bytes=50,
    )

    result = compose(evaluation, max_combinations=10)
    assigned = {
        assignment.plan_id
        for stack in (*result.compatible, *result.unknown, *result.incompatible)
        for assignment in stack.assignments
    }

    assert result.compatible[0].sort_key == ("plan-ok",)
    assert result.unknown[0].sort_key == ("plan-a",)
    assert "plan-bad" not in assigned
    assert result.incompatible == ()
    assert all(stack.budget_check is None for stack in (*result.compatible, *result.unknown))


def test_empty_role_is_no_candidates_and_incompatible_role_is_all_incompatible() -> None:
    no_candidates = _evaluation(frozenset({Feature.DATABASE}), [_plan("file-plan", CapabilityKey.FILE_STORAGE)])
    all_incompatible = _evaluation(
        frozenset({Feature.DATABASE}),
        [_plan("plan-bad", CapabilityKey.DATABASE)],
        {"plan-bad": (_limit("plan-bad", LimitMetric.DATABASE_SIZE_BYTES, 1),)},
        database_size_bytes=50,
    )

    missing = compose(no_candidates, max_combinations=10)
    rejected = compose(all_incompatible, max_combinations=10)

    assert missing.status is CompositionStatus.BLOCKED
    assert missing.blocked_roles[0].reason is BlockReason.NO_CANDIDATES
    assert rejected.blocked_roles[0].reason is BlockReason.ALL_INCOMPATIBLE
    assert missing.compatible == missing.unknown == missing.incompatible == ()
    assert missing.combination_count == 0


def test_one_blocked_role_stops_composition_and_keeps_every_block_reason() -> None:
    evaluation = _evaluation(
        frozenset({Feature.FILE_UPLOADS, Feature.DATABASE, Feature.BACKEND_SERVER}),
        [
            _plan("server-plan", CapabilityKey.SERVER_COMPUTE),
            _plan("file-plan", CapabilityKey.FILE_STORAGE),
        ],
        {"file-plan": (_limit("file-plan", LimitMetric.FILE_STORAGE_BYTES, 1),)},
        file_storage_bytes=50,
    )

    result = compose(evaluation, max_combinations=10)

    assert result.status is CompositionStatus.BLOCKED
    assert result.compatible == ()
    assert tuple((item.feature, item.reason) for item in result.blocked_roles) == (
        (Feature.DATABASE, BlockReason.NO_CANDIDATES),
        (Feature.FILE_UPLOADS, BlockReason.ALL_INCOMPATIBLE),
    )


def test_combination_limit_returns_every_stack_only_when_the_count_fits() -> None:
    evaluation = _evaluation(
        frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
        [
            _plan("alpha-db", CapabilityKey.DATABASE),
            _plan("beta-db", CapabilityKey.DATABASE),
            _plan("alpha-file", CapabilityKey.FILE_STORAGE),
            _plan("beta-file", CapabilityKey.FILE_STORAGE),
        ],
    )

    below = compose(evaluation, max_combinations=5)
    exact = compose(evaluation, max_combinations=4)
    above = compose(evaluation, max_combinations=3)

    assert below.status is CompositionStatus.COMPOSED
    assert len(below.compatible) == 4
    assert exact.status is CompositionStatus.COMPOSED
    assert exact.combination_count == 4
    assert above.status is CompositionStatus.TOO_MANY_COMBINATIONS
    assert above.combination_count == 4
    assert above.compatible == above.unknown == above.incompatible == ()
    assert above.blocked_roles == ()


def test_same_plan_can_fill_several_roles_and_keep_each_status() -> None:
    shared = _plan("plan-a", CapabilityKey.DATABASE, CapabilityKey.FILE_STORAGE)
    compatible = _evaluation(
        frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
        [shared],
    )
    mixed = _evaluation(
        frozenset({Feature.DATABASE, Feature.FILE_UPLOADS}),
        [shared],
        {shared.id: (_limit(shared.id, LimitMetric.DATABASE_SIZE_BYTES, 100),)},
        database_size_bytes=50,
        file_storage_bytes=50,
    )

    same_status = compose(compatible, max_combinations=10).compatible[0]
    different_status = compose(mixed, max_combinations=10).unknown[0]
    statuses = {assignment.feature: assignment.status for assignment in different_status.assignments}

    assert same_status.plan_ids == ("plan-a",)
    assert len(same_status.assignments) == 2
    assert different_status.plan_ids == ("plan-a",)
    assert statuses[Feature.DATABASE] is EvaluationStatus.COMPATIBLE
    assert statuses[Feature.FILE_UPLOADS] is EvaluationStatus.UNKNOWN
    assert different_status.budget_check is None


def test_role_order_and_repeated_runs_do_not_change_the_result() -> None:
    evaluation = _evaluation(
        frozenset({Feature.STATIC_FRONTEND, Feature.BACKEND_SERVER}),
        [
            _plan("front-plan", CapabilityKey.STATIC_HOSTING),
            _plan("server-plan", CapabilityKey.SERVER_COMPUTE),
        ],
    )
    reversed_roles = RecommendationEvaluation(
        roles=tuple(reversed(evaluation.roles)),
        unevaluated_features=evaluation.unevaluated_features,
    )

    first = compose(evaluation, max_combinations=10)
    second = compose(evaluation, max_combinations=10)
    reordered = compose(reversed_roles, max_combinations=10)

    assert first == second == reordered
    assert first.compatible[0].features == (Feature.BACKEND_SERVER, Feature.STATIC_FRONTEND)
    assert first.compatible[0].sort_key == ("server-plan", "front-plan")


def test_unknown_assignment_puts_the_stack_in_the_unknown_group() -> None:
    evaluation = _evaluation(
        frozenset({Feature.DATABASE}),
        [_plan("plan-a", CapabilityKey.DATABASE)],
        database_size_bytes=50,
    )

    result = compose(evaluation, max_combinations=10)

    assert result.compatible == ()
    assert result.unknown[0].status is EvaluationStatus.UNKNOWN
    assert result.unknown[0].budget_check is None
    assert result.incompatible == ()


def test_unevaluated_features_are_preserved_for_every_composition_status() -> None:
    composed = compose(
        _evaluation(
            frozenset({Feature.AI_API, Feature.DATABASE}),
            [_plan("plan-a", CapabilityKey.DATABASE)],
        ),
        max_combinations=10,
    )
    no_roles = compose(_evaluation(frozenset({Feature.AI_API}), []), max_combinations=10)
    blocked = compose(
        _evaluation(frozenset({Feature.AI_API, Feature.DATABASE}), []),
        max_combinations=10,
    )
    too_many = compose(
        _evaluation(
            frozenset({Feature.AI_API, Feature.DATABASE}),
            [
                _plan("plan-a", CapabilityKey.DATABASE),
                _plan("plan-b", CapabilityKey.DATABASE),
            ],
        ),
        max_combinations=1,
    )
    expected = frozenset({Feature.AI_API})

    assert composed.status is CompositionStatus.COMPOSED
    assert composed.unevaluated_features == expected
    assert no_roles.unevaluated_features == expected
    assert blocked.status is CompositionStatus.BLOCKED
    assert blocked.unevaluated_features == expected
    assert too_many.status is CompositionStatus.TOO_MANY_COMBINATIONS
    assert too_many.unevaluated_features == expected


def test_compose_does_not_change_the_evaluation() -> None:
    plans = [_plan("plan-a", CapabilityKey.DATABASE)]
    before = _evaluation(frozenset({Feature.DATABASE}), plans)
    unchanged = _evaluation(frozenset({Feature.DATABASE}), plans)

    compose(before, max_combinations=10)

    assert before == unchanged


def test_composer_does_not_depend_on_application_infrastructure_or_repositories() -> None:
    composer = Path(__file__).parents[3] / "src" / "freestack" / "domain" / "composition" / "composer.py"
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
    imported = _imported_modules([composer])
    for name in imported:
        assert all(name != item and not name.startswith(f"{item}.") for item in forbidden)

    recommendation = composer.parents[1] / "recommendation"
    assert all(
        "freestack.domain.composition" not in name
        for name in _imported_modules(recommendation.glob("*.py"))
    )


def _imported_modules(paths) -> list[str]:
    imported: list[str] = []
    for path in paths:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.append(node.module)
    return imported
