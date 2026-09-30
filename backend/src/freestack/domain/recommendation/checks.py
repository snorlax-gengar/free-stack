from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from freestack.domain.limit import Limit
from freestack.domain.needs import BudgetNeed, CapabilityNeed, QuantityNeed
from freestack.domain.plan import Plan
from freestack.domain.pricing import PlanPricing


class ReasonCode(StrEnum):
    """Why a single need check ended the way it did."""

    CAPABILITY_PROVIDED = "capability-provided"
    CAPABILITY_NOT_PROVIDED = "capability-not-provided"
    WITHIN_LIMIT = "within-limit"
    UNLIMITED = "unlimited"
    EXCEEDS_LIMIT = "exceeds-limit"
    LIMIT_NOT_FOUND = "limit-not-found"
    LIMIT_PERIOD_MISMATCH = "limit-period-mismatch"
    WITHIN_BUDGET = "within-budget"
    OVER_BUDGET = "over-budget"
    PRICING_NOT_FOUND = "pricing-not-found"


class CheckOutcome(StrEnum):
    """Whether one need is met, unmet, or not decidable."""

    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNKNOWN = "unknown"


_OUTCOME_BY_REASON: dict[ReasonCode, CheckOutcome] = {
    ReasonCode.CAPABILITY_PROVIDED: CheckOutcome.SATISFIED,
    ReasonCode.CAPABILITY_NOT_PROVIDED: CheckOutcome.VIOLATED,
    ReasonCode.WITHIN_LIMIT: CheckOutcome.SATISFIED,
    ReasonCode.UNLIMITED: CheckOutcome.SATISFIED,
    ReasonCode.EXCEEDS_LIMIT: CheckOutcome.VIOLATED,
    ReasonCode.LIMIT_NOT_FOUND: CheckOutcome.UNKNOWN,
    ReasonCode.LIMIT_PERIOD_MISMATCH: CheckOutcome.UNKNOWN,
    ReasonCode.WITHIN_BUDGET: CheckOutcome.SATISFIED,
    ReasonCode.OVER_BUDGET: CheckOutcome.VIOLATED,
    ReasonCode.PRICING_NOT_FOUND: CheckOutcome.UNKNOWN,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class CheckResult:
    """One check result. The outcome is derived from the reason code."""

    reason_code: ReasonCode

    def __post_init__(self) -> None:
        if not isinstance(self.reason_code, ReasonCode):
            raise ValueError(f"invalid reason_code: {self.reason_code!r}")
        if self.reason_code not in _OUTCOME_BY_REASON:
            raise ValueError(f"invalid reason_code: {self.reason_code!r}")

    @property
    def outcome(self) -> CheckOutcome:
        return _OUTCOME_BY_REASON[self.reason_code]


@dataclass(frozen=True, slots=True, kw_only=True)
class LimitCheck(CheckResult):
    """A quantity check plus the limits that produced it."""

    limit: Limit | None
    other_period_limits: tuple[Limit, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.limit is not None and not isinstance(self.limit, Limit):
            raise ValueError(f"invalid limit: {self.limit!r}")
        if not isinstance(self.other_period_limits, tuple) or any(
            not isinstance(item, Limit) for item in self.other_period_limits
        ):
            raise ValueError(f"invalid other_period_limits: {self.other_period_limits!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class BudgetCheck(CheckResult):
    """A budget check plus the pricing that produced it."""

    pricing: PlanPricing | None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.pricing is not None and not isinstance(self.pricing, PlanPricing):
            raise ValueError(f"invalid pricing: {self.pricing!r}")


def check_capability(plan: Plan, need: CapabilityNeed) -> CheckResult:
    """Report whether the plan provides the needed capability."""

    if need.capability in plan.capabilities:
        return CheckResult(reason_code=ReasonCode.CAPABILITY_PROVIDED)
    return CheckResult(reason_code=ReasonCode.CAPABILITY_NOT_PROVIDED)


def check_limit(limits: Sequence[Limit], need: QuantityNeed) -> LimitCheck:
    """Compare a quantity need with limits already loaded for one plan."""

    exact = next(
        (
            limit
            for limit in limits
            if limit.metric is need.metric and limit.period is need.period
        ),
        None,
    )
    if exact is not None:
        if exact.value is None:
            reason = ReasonCode.UNLIMITED
        elif need.required <= exact.value:
            reason = ReasonCode.WITHIN_LIMIT
        else:
            reason = ReasonCode.EXCEEDS_LIMIT
        return LimitCheck(
            reason_code=reason,
            limit=exact,
            other_period_limits=(),
        )
    other_period_limits = tuple(limit for limit in limits if limit.metric is need.metric)
    if other_period_limits:
        return LimitCheck(
            reason_code=ReasonCode.LIMIT_PERIOD_MISMATCH,
            limit=None,
            other_period_limits=other_period_limits,
        )
    return LimitCheck(
        reason_code=ReasonCode.LIMIT_NOT_FOUND,
        limit=None,
        other_period_limits=(),
    )


def check_budget(pricing: PlanPricing | None, need: BudgetNeed) -> BudgetCheck:
    """Compare a budget with the plan base fee. Exceed behavior is ignored."""

    if pricing is None:
        return BudgetCheck(reason_code=ReasonCode.PRICING_NOT_FOUND, pricing=None)
    if pricing.monthly_base_fee_usd_cents <= need.max_monthly_usd_cents:
        return BudgetCheck(reason_code=ReasonCode.WITHIN_BUDGET, pricing=pricing)
    return BudgetCheck(reason_code=ReasonCode.OVER_BUDGET, pricing=pricing)
