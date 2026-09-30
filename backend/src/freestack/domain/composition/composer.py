import itertools
from collections.abc import Sequence

from freestack.domain.composition.models import (
    BlockedRole,
    BlockReason,
    CompositionResult,
    CompositionStatus,
    RoleAssignment,
    Stack,
)
from freestack.domain.feature import Feature
from freestack.domain.recommendation.evaluation import (
    EvaluationStatus,
    RecommendationEvaluation,
    RoleEvaluation,
)


def compose(
    evaluation: RecommendationEvaluation,
    *,
    max_combinations: int,
) -> CompositionResult:
    """Assign one compatible or unknown plan to every evaluated role.

    This does not rank stacks or calculate a budget.
    """

    _validate_max_combinations(max_combinations)
    unevaluated = evaluation.unevaluated_features
    if not evaluation.roles:
        return _empty(CompositionStatus.NO_ROLES, 0, unevaluated)

    roles = tuple(sorted(evaluation.roles, key=lambda role: role.role.value))
    blocked: list[BlockedRole] = []
    features: list[Feature] = []
    candidates: list[tuple[tuple[str, EvaluationStatus], ...]] = []
    for role in roles:
        role_candidates = _role_candidates(role)
        if not role_candidates:
            blocked.append(BlockedRole(feature=role.role, reason=_block_reason(role)))
            continue
        features.append(role.role)
        candidates.append(role_candidates)
    if blocked:
        return _empty(
            CompositionStatus.BLOCKED,
            0,
            unevaluated,
            blocked_roles=tuple(blocked),
        )

    combination_count = _combination_count(tuple(len(items) for items in candidates))
    if combination_count > max_combinations:
        return _empty(CompositionStatus.TOO_MANY_COMBINATIONS, combination_count, unevaluated)

    stacks = tuple(
        _build_stack(tuple(features), choice)
        for choice in itertools.product(*candidates)
    )
    grouped: dict[EvaluationStatus, list[Stack]] = {
        EvaluationStatus.COMPATIBLE: [],
        EvaluationStatus.UNKNOWN: [],
        EvaluationStatus.INCOMPATIBLE: [],
    }
    for stack in stacks:
        grouped[stack.status].append(stack)
    return CompositionResult(
        status=CompositionStatus.COMPOSED,
        compatible=_sorted_stacks(grouped[EvaluationStatus.COMPATIBLE]),
        unknown=_sorted_stacks(grouped[EvaluationStatus.UNKNOWN]),
        incompatible=_sorted_stacks(grouped[EvaluationStatus.INCOMPATIBLE]),
        blocked_roles=(),
        combination_count=combination_count,
        unevaluated_features=unevaluated,
    )


def _validate_max_combinations(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"invalid max_combinations: {value!r}")


def _role_candidates(role: RoleEvaluation) -> tuple[tuple[str, EvaluationStatus], ...]:
    selected = [
        *((item.plan.id, EvaluationStatus.COMPATIBLE) for item in role.compatible),
        *((item.plan.id, EvaluationStatus.UNKNOWN) for item in role.unknown),
    ]
    selected.sort(key=lambda item: item[0])
    return tuple(selected)


def _block_reason(role: RoleEvaluation) -> BlockReason:
    if role.incompatible:
        return BlockReason.ALL_INCOMPATIBLE
    return BlockReason.NO_CANDIDATES


def _combination_count(counts: Sequence[int]) -> int:
    total = 1
    for count in counts:
        total *= count
    return total


def _build_stack(
    features: tuple[Feature, ...],
    choice: tuple[tuple[str, EvaluationStatus], ...],
) -> Stack:
    assignments = tuple(
        RoleAssignment(feature=feature, plan_id=plan_id, status=status)
        for feature, (plan_id, status) in zip(features, choice, strict=True)
    )
    return Stack(assignments=assignments, budget_check=None)


def _sorted_stacks(stacks: list[Stack]) -> tuple[Stack, ...]:
    return tuple(sorted(stacks, key=lambda stack: stack.sort_key))


def _empty(
    status: CompositionStatus,
    combination_count: int,
    unevaluated_features: frozenset[Feature],
    *,
    blocked_roles: tuple[BlockedRole, ...] = (),
) -> CompositionResult:
    return CompositionResult(
        status=status,
        compatible=(),
        unknown=(),
        incompatible=(),
        blocked_roles=blocked_roles,
        combination_count=combination_count,
        unevaluated_features=unevaluated_features,
    )
