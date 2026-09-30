from dataclasses import dataclass

from freestack.domain.feature import Feature


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectRequirement:
    """What a project needs. This object does not evaluate plans."""

    features: frozenset[Feature]
    file_storage_bytes: int | None = None
    database_size_bytes: int | None = None
    monthly_bandwidth_bytes: int | None = None
    monthly_budget_usd_cents: int | None = None

    def __post_init__(self) -> None:
        _require_features(self.features)
        _require_positive_quantity(self.file_storage_bytes, "file_storage_bytes")
        _require_positive_quantity(self.database_size_bytes, "database_size_bytes")
        _require_positive_quantity(self.monthly_bandwidth_bytes, "monthly_bandwidth_bytes")
        _require_budget(self.monthly_budget_usd_cents)
        if self.file_storage_bytes is not None and Feature.FILE_UPLOADS not in self.features:
            raise ValueError(
                f"invalid file_storage_bytes: {self.file_storage_bytes!r} requires file-uploads"
            )
        if self.database_size_bytes is not None and Feature.DATABASE not in self.features:
            raise ValueError(
                f"invalid database_size_bytes: {self.database_size_bytes!r} requires database"
            )


def _require_features(features: object) -> None:
    if not isinstance(features, frozenset) or len(features) == 0:
        raise ValueError(f"invalid features: {features!r}")
    if any(not isinstance(item, Feature) for item in features):
        raise ValueError(f"invalid features: {features!r}")


def _require_positive_quantity(value: object, field_name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"invalid {field_name}: {value!r}")


def _require_budget(value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"invalid monthly_budget_usd_cents: {value!r}")
