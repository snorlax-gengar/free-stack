from dataclasses import dataclass

from freestack.domain.capability import CapabilityKey
from freestack.domain.feature import Feature
from freestack.domain.limit import LimitMetric, LimitPeriod
from freestack.domain.requirement import ProjectRequirement

_FEATURE_ORDER = {feature: index for index, feature in enumerate(Feature)}

_CAPABILITY_BY_FEATURE: dict[Feature, CapabilityKey] = {
    Feature.STATIC_FRONTEND: CapabilityKey.STATIC_HOSTING,
    Feature.BACKEND_SERVER: CapabilityKey.SERVER_COMPUTE,
    Feature.BACKEND_FUNCTIONS: CapabilityKey.SERVERLESS_FUNCTIONS,
    Feature.DATABASE: CapabilityKey.DATABASE,
    Feature.FILE_UPLOADS: CapabilityKey.FILE_STORAGE,
    Feature.AUTHENTICATION: CapabilityKey.AUTHENTICATION,
    Feature.REALTIME: CapabilityKey.REALTIME,
    Feature.SCHEDULED_JOBS: CapabilityKey.SCHEDULED_JOBS,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilityNeed:
    """A catalog capability required by one project feature."""

    feature: Feature
    capability: CapabilityKey

    def __post_init__(self) -> None:
        if not isinstance(self.feature, Feature):
            raise ValueError(f"invalid feature: {self.feature!r}")
        if not isinstance(self.capability, CapabilityKey):
            raise ValueError(f"invalid capability: {self.capability!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class QuantityNeed:
    """A required usage amount. This is not a stored limit."""

    metric: LimitMetric
    period: LimitPeriod
    required: int
    applies_to: Feature | None

    def __post_init__(self) -> None:
        if not isinstance(self.metric, LimitMetric):
            raise ValueError(f"invalid metric: {self.metric!r}")
        if not isinstance(self.period, LimitPeriod):
            raise ValueError(f"invalid period: {self.period!r}")
        if isinstance(self.required, bool) or not isinstance(self.required, int) or self.required <= 0:
            raise ValueError(f"invalid required: {self.required!r}")
        if self.applies_to is not None and not isinstance(self.applies_to, Feature):
            raise ValueError(f"invalid applies_to: {self.applies_to!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class BudgetNeed:
    """Maximum monthly base budget in USD cents. Zero means free only."""

    max_monthly_usd_cents: int

    def __post_init__(self) -> None:
        value = self.max_monthly_usd_cents
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"invalid max_monthly_usd_cents: {value!r}")


@dataclass(frozen=True, slots=True, kw_only=True)
class DerivedNeeds:
    """Needs produced from one project requirement. These are not entities."""

    capabilities: tuple[CapabilityNeed, ...]
    quantities: tuple[QuantityNeed, ...]
    budget: BudgetNeed | None
    unevaluated_features: frozenset[Feature]

    def __post_init__(self) -> None:
        _require_need_tuple(self.capabilities, CapabilityNeed, "capabilities")
        _require_need_tuple(self.quantities, QuantityNeed, "quantities")
        if self.budget is not None and not isinstance(self.budget, BudgetNeed):
            raise ValueError(f"invalid budget: {self.budget!r}")
        if not isinstance(self.unevaluated_features, frozenset):
            raise ValueError(f"invalid unevaluated_features: {self.unevaluated_features!r}")
        if any(not isinstance(item, Feature) for item in self.unevaluated_features):
            raise ValueError(f"invalid unevaluated_features: {self.unevaluated_features!r}")


def derive_needs(requirement: ProjectRequirement) -> DerivedNeeds:
    """Turn a project requirement into needs. This does not evaluate plans."""

    capabilities: list[CapabilityNeed] = []
    unevaluated: list[Feature] = []
    for feature in sorted(requirement.features, key=_FEATURE_ORDER.__getitem__):
        capability = _CAPABILITY_BY_FEATURE.get(feature)
        if capability is None:
            unevaluated.append(feature)
            continue
        capabilities.append(CapabilityNeed(feature=feature, capability=capability))

    quantities: list[QuantityNeed] = []
    if requirement.file_storage_bytes is not None:
        quantities.append(
            QuantityNeed(
                metric=LimitMetric.FILE_STORAGE_BYTES,
                period=LimitPeriod.NONE,
                required=requirement.file_storage_bytes,
                applies_to=Feature.FILE_UPLOADS,
            )
        )
    if requirement.database_size_bytes is not None:
        quantities.append(
            QuantityNeed(
                metric=LimitMetric.DATABASE_SIZE_BYTES,
                period=LimitPeriod.NONE,
                required=requirement.database_size_bytes,
                applies_to=Feature.DATABASE,
            )
        )
    if requirement.monthly_bandwidth_bytes is not None:
        quantities.append(
            QuantityNeed(
                metric=LimitMetric.BANDWIDTH_BYTES,
                period=LimitPeriod.MONTH,
                required=requirement.monthly_bandwidth_bytes,
                applies_to=None,
            )
        )

    budget = None
    if requirement.monthly_budget_usd_cents is not None:
        budget = BudgetNeed(max_monthly_usd_cents=requirement.monthly_budget_usd_cents)

    return DerivedNeeds(
        capabilities=tuple(capabilities),
        quantities=tuple(quantities),
        budget=budget,
        unevaluated_features=frozenset(unevaluated),
    )


def _require_need_tuple(values: object, item_type: type[object], field_name: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(item, item_type) for item in values):
        raise ValueError(f"invalid {field_name}: {values!r}")
