from dataclasses import FrozenInstanceError
from enum import StrEnum

import pytest

from freestack.domain.capability import CapabilityKey
from freestack.domain.feature import Feature
from freestack.domain.requirement import ProjectRequirement


class _OtherFeature(StrEnum):
    DATABASE = "database"


def _requirement(**overrides: object) -> ProjectRequirement:
    values: dict[str, object] = {
        "features": frozenset({Feature.DATABASE}),
    }
    values.update(overrides)
    return ProjectRequirement(**values)  # type: ignore[arg-type]


def test_requirement_accepts_one_feature() -> None:
    requirement = _requirement()

    assert requirement.features == frozenset({Feature.DATABASE})
    assert requirement.file_storage_bytes is None
    assert requirement.database_size_bytes is None
    assert requirement.monthly_bandwidth_bytes is None
    assert requirement.monthly_budget_usd_cents is None


def test_requirement_accepts_several_features() -> None:
    features = frozenset({Feature.STATIC_FRONTEND, Feature.DATABASE, Feature.AUTHENTICATION})

    requirement = _requirement(features=features)

    assert requirement.features == features


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("file_storage_bytes", 1_000_000),
        ("database_size_bytes", 500_000_000),
        ("monthly_bandwidth_bytes", 10_000_000_000),
    ],
)
def test_requirement_accepts_positive_quantities(field_name: str, value: int) -> None:
    features = frozenset({Feature.FILE_UPLOADS, Feature.DATABASE, Feature.STATIC_FRONTEND})

    requirement = _requirement(features=features, **{field_name: value})

    assert getattr(requirement, field_name) == value


@pytest.mark.parametrize("budget", [0, 100])
def test_requirement_accepts_zero_and_positive_budget(budget: int) -> None:
    requirement = _requirement(monthly_budget_usd_cents=budget)

    assert requirement.monthly_budget_usd_cents == budget


def test_requirement_allows_bandwidth_without_a_dedicated_feature() -> None:
    requirement = ProjectRequirement(
        features=frozenset({Feature.STATIC_FRONTEND}),
        monthly_bandwidth_bytes=10_000_000_000,
    )

    assert requirement.monthly_bandwidth_bytes == 10_000_000_000


def test_requirement_rejects_empty_features() -> None:
    with pytest.raises(ValueError, match=r"invalid features:"):
        _requirement(features=frozenset())


@pytest.mark.parametrize(
    "features",
    [
        {Feature.DATABASE},
        [Feature.DATABASE],
        "database",
        frozenset({"database"}),
        frozenset({CapabilityKey.DATABASE}),
        frozenset({_OtherFeature.DATABASE}),
    ],
)
def test_requirement_rejects_invalid_features(features: object) -> None:
    with pytest.raises(ValueError, match=r"invalid features:"):
        _requirement(features=features)


@pytest.mark.parametrize("field_name", ["file_storage_bytes", "database_size_bytes", "monthly_bandwidth_bytes"])
@pytest.mark.parametrize("value", [0, -1, 1.5, True, False])
def test_requirement_rejects_invalid_quantity(field_name: str, value: object) -> None:
    features = frozenset({Feature.FILE_UPLOADS, Feature.DATABASE})

    with pytest.raises(ValueError, match=f"invalid {field_name}:"):
        _requirement(features=features, **{field_name: value})


@pytest.mark.parametrize("budget", [-1, 1.5, True, False])
def test_requirement_rejects_invalid_budget(budget: object) -> None:
    with pytest.raises(ValueError, match=r"invalid monthly_budget_usd_cents:"):
        _requirement(monthly_budget_usd_cents=budget)


def test_requirement_rejects_file_storage_without_file_uploads() -> None:
    with pytest.raises(ValueError, match="requires file-uploads"):
        ProjectRequirement(
            features=frozenset({Feature.DATABASE}),
            file_storage_bytes=1_000_000,
        )


def test_requirement_rejects_database_size_without_database() -> None:
    with pytest.raises(ValueError, match="requires database"):
        ProjectRequirement(
            features=frozenset({Feature.FILE_UPLOADS}),
            database_size_bytes=500_000_000,
        )


def test_requirement_accepts_storage_and_database_with_their_features() -> None:
    requirement = ProjectRequirement(
        features=frozenset({Feature.FILE_UPLOADS, Feature.DATABASE}),
        file_storage_bytes=1_000_000,
        database_size_bytes=500_000_000,
    )

    assert requirement.file_storage_bytes == 1_000_000
    assert requirement.database_size_bytes == 500_000_000


def test_requirement_is_immutable() -> None:
    requirement = _requirement()

    with pytest.raises(FrozenInstanceError):
        requirement.monthly_budget_usd_cents = 0  # type: ignore[misc]


def test_requirement_uses_slots() -> None:
    assert not hasattr(_requirement(), "__dict__")


def test_requirement_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ProjectRequirement(frozenset({Feature.DATABASE}))  # type: ignore[misc]
