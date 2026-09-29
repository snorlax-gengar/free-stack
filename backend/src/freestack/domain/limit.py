from dataclasses import dataclass
from enum import StrEnum

from freestack.domain.validation import require_identifier


class LimitMetric(StrEnum):
    """What a limit measures. The value name includes the base unit."""

    FILE_STORAGE_BYTES = "file-storage-bytes"
    DATABASE_SIZE_BYTES = "database-size-bytes"
    BANDWIDTH_BYTES = "bandwidth-bytes"
    REQUESTS = "requests"
    BUILD_SECONDS = "build-seconds"


class LimitPeriod(StrEnum):
    """The window a limit applies to."""

    NONE = "none"
    DAY = "day"
    MONTH = "month"


@dataclass(frozen=True, slots=True, kw_only=True)
class Limit:
    """One measured allowance belonging to a plan.

    ``value`` is an integer in the metric's base unit.

    ``None`` means the allowance is explicitly unlimited.
    A missing ``Limit`` row means the allowance is unknown.
    ``0`` means the plan does not offer that usage.
    """

    plan_id: str
    metric: LimitMetric
    period: LimitPeriod
    value: int | None
    source_id: str

    def __post_init__(self) -> None:
        require_identifier(self.plan_id, "plan_id")
        require_identifier(self.source_id, "source_id")
        if not isinstance(self.metric, LimitMetric):
            raise ValueError(f"invalid metric: {self.metric!r}")
        if not isinstance(self.period, LimitPeriod):
            raise ValueError(f"invalid period: {self.period!r}")
        _require_limit_value(self.value)


def _require_limit_value(value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"invalid value: {value!r}")
