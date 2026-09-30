from dataclasses import dataclass
from enum import StrEnum

from freestack.domain.feature import Feature
from freestack.domain.recommendation.checks import CheckOutcome, CheckResult, ReasonCode
from freestack.domain.recommendation.evaluation import EvaluationStatus
from freestack.domain.validation import require_identifier

_STACK_BUDGET_REASONS = frozenset(
    {
        ReasonCode.WITHIN_BUDGET,
        ReasonCode.OVER_BUDGET,
        ReasonCode.PRICING_NOT_FOUND,
    }
)


class BlockReason(StrEnum):
    """Why one role cannot be assigned a plan.

    ``no-candidates`` means the role has no evaluated plans.
    ``all-incompatible`` means every evaluated plan for the role is incompatible.
    A plan that lacks the role capability is not an evaluated candidate.
    """

    NO_CANDIDATES = "no-candidates"
    ALL_INCOMPATIBLE = "all-incompatible"


class CompositionStatus(StrEnum):
    """Whether composition produced stacks. This does not rank them."""

    COMPOSED = "composed"
    BLOCKED = "blocked"
    TOO_MANY_COMBINATIONS = "too-many-combinations"
    NO_ROLES = "no-roles"


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleAssignment:
    """One role filled by one plan. The status is copied from evaluation."""

    feature: Feature
    plan_id: str
    status: EvaluationStatus

    def __post_init__(self) -> None:
        if not isinstance(self.feature, Feature):
            raise ValueError(f"invalid feature: {self.feature!r}")
        if not isinstance(self.plan_id, str):
            raise ValueError(f"invalid plan_id: {self.plan_id!r}")
        require_identifier(self.plan_id, "plan_id")
        if self.status is not EvaluationStatus.COMPATIBLE and self.status is not EvaluationStatus.UNKNOWN:
            raise ValueError(f"invalid status: {self.status!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class StackBudgetCheck:
    """A recorded budget comparison. This object does not price a stack."""

    budget_usd_cents: int
    priced_plan_ids: tuple[str, ...]
    unpriced_plan_ids: tuple[str, ...]
    known_total_usd_cents: int
    reason: ReasonCode

    def __post_init__(self) -> None:
        _require_cents(self.budget_usd_cents, "budget_usd_cents")
        _require_cents(self.known_total_usd_cents, "known_total_usd_cents")
        _require_plan_id_tuple(self.priced_plan_ids, "priced_plan_ids")
        _require_plan_id_tuple(self.unpriced_plan_ids, "unpriced_plan_ids")
        overlap = set(self.priced_plan_ids) & set(self.unpriced_plan_ids)
        if overlap:
            raise ValueError(f"invalid plan ids: {tuple(sorted(overlap))!r}")
        if not self.priced_plan_ids and not self.unpriced_plan_ids:
            raise ValueError("invalid plan ids: ()")
        if not isinstance(self.reason, ReasonCode) or self.reason not in _STACK_BUDGET_REASONS:
            raise ValueError(f"invalid reason: {self.reason!r}")
        expected = _budget_reason(
            self.budget_usd_cents,
            self.known_total_usd_cents,
            self.unpriced_plan_ids,
        )
        if self.reason is not expected:
            raise ValueError(f"invalid reason: {self.reason!r}")

    @property
    def outcome(self) -> CheckOutcome:
        return CheckResult(reason_code=self.reason).outcome


@dataclass(frozen=True, slots=True, kw_only=True)
class Stack:
    """One complete assignment of evaluated roles. This is not a ranking."""

    assignments: tuple[RoleAssignment, ...]
    budget_check: StackBudgetCheck | None

    def __post_init__(self) -> None:
        if not isinstance(self.assignments, tuple) or len(self.assignments) == 0:
            raise ValueError(f"invalid assignments: {self.assignments!r}")
        if any(not isinstance(item, RoleAssignment) for item in self.assignments):
            raise ValueError(f"invalid assignments: {self.assignments!r}")
        features = tuple(item.feature for item in self.assignments)
        ordered = tuple(sorted(features, key=lambda feature: feature.value))
        if features != ordered or len(features) != len(set(features)):
            raise ValueError(f"invalid assignments: {features!r}")
        if self.budget_check is not None and not isinstance(self.budget_check, StackBudgetCheck):
            raise ValueError(f"invalid budget_check: {self.budget_check!r}")
        if self.budget_check is not None:
            covered = set(self.budget_check.priced_plan_ids) | set(self.budget_check.unpriced_plan_ids)
            if covered != set(self.plan_ids):
                raise ValueError(
                    f"invalid budget_check: {tuple(sorted(covered))!r} "
                    f"does not match plans {self.plan_ids!r}"
                )

    @property
    def plan_ids(self) -> tuple[str, ...]:
        return tuple(sorted({item.plan_id for item in self.assignments}))

    @property
    def features(self) -> tuple[Feature, ...]:
        return tuple(item.feature for item in self.assignments)

    @property
    def status(self) -> EvaluationStatus:
        outcomes = [
            CheckOutcome.SATISFIED
            if item.status is EvaluationStatus.COMPATIBLE
            else CheckOutcome.UNKNOWN
            for item in self.assignments
        ]
        if self.budget_check is not None:
            outcomes.append(self.budget_check.outcome)
        if any(outcome is CheckOutcome.VIOLATED for outcome in outcomes):
            return EvaluationStatus.INCOMPATIBLE
        if any(outcome is CheckOutcome.UNKNOWN for outcome in outcomes):
            return EvaluationStatus.UNKNOWN
        return EvaluationStatus.COMPATIBLE

    @property
    def sort_key(self) -> tuple[str, ...]:
        return tuple(item.plan_id for item in self.assignments)


@dataclass(frozen=True, slots=True, kw_only=True)
class BlockedRole:
    """A role that cannot receive a compatible or unknown plan."""

    feature: Feature
    reason: BlockReason

    def __post_init__(self) -> None:
        if not isinstance(self.feature, Feature):
            raise ValueError(f"invalid feature: {self.feature!r}")
        if not isinstance(self.reason, BlockReason):
            raise ValueError(f"invalid reason: {self.reason!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class CompositionResult:
    """Stacks grouped by status, or a reason composition stopped."""

    status: CompositionStatus
    compatible: tuple[Stack, ...]
    unknown: tuple[Stack, ...]
    incompatible: tuple[Stack, ...]
    blocked_roles: tuple[BlockedRole, ...]
    combination_count: int
    unevaluated_features: frozenset[Feature]

    def __post_init__(self) -> None:
        if not isinstance(self.status, CompositionStatus):
            raise ValueError(f"invalid status: {self.status!r}")
        _require_stack_group(self.compatible, EvaluationStatus.COMPATIBLE, "compatible")
        _require_stack_group(self.unknown, EvaluationStatus.UNKNOWN, "unknown")
        _require_stack_group(self.incompatible, EvaluationStatus.INCOMPATIBLE, "incompatible")
        _require_blocked_roles(self.blocked_roles)
        if isinstance(self.combination_count, bool) or not isinstance(self.combination_count, int):
            raise ValueError(f"invalid combination_count: {self.combination_count!r}")
        if self.combination_count < 0:
            raise ValueError(f"invalid combination_count: {self.combination_count!r}")
        if not isinstance(self.unevaluated_features, frozenset) or any(
            not isinstance(feature, Feature) for feature in self.unevaluated_features
        ):
            raise ValueError(f"invalid unevaluated_features: {self.unevaluated_features!r}")
        if self.status is not CompositionStatus.COMPOSED and (
            self.compatible or self.unknown or self.incompatible
        ):
            raise ValueError(f"invalid status: {self.status!r}")
        blocked = len(self.blocked_roles) > 0
        if (self.status is CompositionStatus.BLOCKED) != blocked:
            raise ValueError(f"invalid blocked_roles: {self.blocked_roles!r}")
        if self.status is CompositionStatus.NO_ROLES and self.combination_count != 0:
            raise ValueError(f"invalid combination_count: {self.combination_count!r}")
        if self.status is CompositionStatus.COMPOSED:
            counted = len(self.compatible) + len(self.unknown) + len(self.incompatible)
            if counted != self.combination_count:
                raise ValueError(f"invalid combination_count: {self.combination_count!r}")


def _budget_reason(
    budget_usd_cents: int,
    known_total_usd_cents: int,
    unpriced_plan_ids: tuple[str, ...],
) -> ReasonCode:
    if known_total_usd_cents > budget_usd_cents:
        return ReasonCode.OVER_BUDGET
    if unpriced_plan_ids:
        return ReasonCode.PRICING_NOT_FOUND
    return ReasonCode.WITHIN_BUDGET


def _require_cents(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"invalid {field_name}: {value!r}")


def _require_plan_id_tuple(values: object, field_name: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(item, str) for item in values):
        raise ValueError(f"invalid {field_name}: {values!r}")
    for item in values:
        require_identifier(item, field_name)
    if values != tuple(sorted(set(values))):
        raise ValueError(f"invalid {field_name}: {values!r}")


def _require_stack_group(
    values: object,
    status: EvaluationStatus,
    field_name: str,
) -> None:
    if not isinstance(values, tuple) or any(not isinstance(item, Stack) for item in values):
        raise ValueError(f"invalid {field_name}: {values!r}")
    if any(item.status is not status for item in values):
        raise ValueError(f"invalid {field_name}: {values!r}")
    keys = tuple(item.sort_key for item in values)
    if keys != tuple(sorted(keys)):
        raise ValueError(f"invalid {field_name}: {keys!r}")
    if len(values) != len(set(values)):
        raise ValueError(f"invalid {field_name}: {values!r}")


def _require_blocked_roles(values: object) -> None:
    if not isinstance(values, tuple) or any(not isinstance(item, BlockedRole) for item in values):
        raise ValueError(f"invalid blocked_roles: {values!r}")
    features = tuple(item.feature for item in values)
    ordered = tuple(sorted(set(features), key=lambda feature: feature.value))
    if features != ordered:
        raise ValueError(f"invalid blocked_roles: {features!r}")
