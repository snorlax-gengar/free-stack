from dataclasses import dataclass
from enum import StrEnum

from freestack.domain.validation import require_identifier


class ExceedBehavior(StrEnum):
    """What can happen when included usage is exceeded.

    This is a plan-level set, not a per-metric model.
    """

    CHARGED = "charged"
    SUSPENDED = "suspended"
    RESTRICTED = "restricted"


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanPricing:
    """Monthly base fee and exceed behavior for one plan.

    ``monthly_base_fee_usd_cents`` of ``0`` means the base fee is free.
    A positive value means a monthly base fee exists.
    A missing pricing row means the price is unknown.
    This is not a usage limit and not an overage rate.
    """

    plan_id: str
    monthly_base_fee_usd_cents: int
    exceed_behaviors: frozenset[ExceedBehavior]
    source_id: str

    def __post_init__(self) -> None:
        require_identifier(self.plan_id, "plan_id")
        require_identifier(self.source_id, "source_id")
        _require_fee(self.monthly_base_fee_usd_cents)
        _require_exceed_behaviors(self.exceed_behaviors)


def _require_fee(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"invalid monthly_base_fee_usd_cents: {value!r}")


def _require_exceed_behaviors(behaviors: object) -> None:
    if not isinstance(behaviors, frozenset) or len(behaviors) == 0:
        raise ValueError(f"invalid exceed_behaviors: {behaviors!r}")
    if any(not isinstance(item, ExceedBehavior) for item in behaviors):
        raise ValueError(f"invalid exceed_behaviors: {behaviors!r}")
