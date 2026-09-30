import pytest

from freestack.domain.capability import CapabilityKey
from freestack.domain.feature import Feature
from freestack.domain.limit import LimitMetric, LimitPeriod
from freestack.domain.needs import (
    BudgetNeed,
    CapabilityNeed,
    DerivedNeeds,
    QuantityNeed,
    derive_needs,
)
from freestack.domain.requirement import ProjectRequirement


@pytest.mark.parametrize(
    ("feature", "capability"),
    [
        (Feature.STATIC_FRONTEND, CapabilityKey.STATIC_HOSTING),
        (Feature.BACKEND_SERVER, CapabilityKey.SERVER_COMPUTE),
        (Feature.BACKEND_FUNCTIONS, CapabilityKey.SERVERLESS_FUNCTIONS),
        (Feature.DATABASE, CapabilityKey.DATABASE),
        (Feature.FILE_UPLOADS, CapabilityKey.FILE_STORAGE),
        (Feature.AUTHENTICATION, CapabilityKey.AUTHENTICATION),
        (Feature.REALTIME, CapabilityKey.REALTIME),
        (Feature.SCHEDULED_JOBS, CapabilityKey.SCHEDULED_JOBS),
    ],
)
def test_feature_maps_to_capability(feature: Feature, capability: CapabilityKey) -> None:
    needs = derive_needs(ProjectRequirement(features=frozenset({feature})))

    assert needs.capabilities == (CapabilityNeed(feature=feature, capability=capability),)
    assert needs.unevaluated_features == frozenset()


def test_ai_api_stays_unevaluated() -> None:
    needs = derive_needs(
        ProjectRequirement(features=frozenset({Feature.DATABASE, Feature.AI_API}))
    )

    assert needs.capabilities == (
        CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
    )
    assert needs.unevaluated_features == frozenset({Feature.AI_API})


def test_file_storage_quantity_uses_the_catalog_limit_shape() -> None:
    needs = derive_needs(
        ProjectRequirement(
            features=frozenset({Feature.FILE_UPLOADS}),
            file_storage_bytes=1_000_000,
        )
    )

    assert needs.quantities == (
        QuantityNeed(
            metric=LimitMetric.FILE_STORAGE_BYTES,
            period=LimitPeriod.NONE,
            required=1_000_000,
            applies_to=Feature.FILE_UPLOADS,
        ),
    )


def test_database_quantity_uses_the_catalog_limit_shape() -> None:
    needs = derive_needs(
        ProjectRequirement(
            features=frozenset({Feature.DATABASE}),
            database_size_bytes=500_000_000,
        )
    )

    assert needs.quantities == (
        QuantityNeed(
            metric=LimitMetric.DATABASE_SIZE_BYTES,
            period=LimitPeriod.NONE,
            required=500_000_000,
            applies_to=Feature.DATABASE,
        ),
    )


def test_bandwidth_quantity_is_monthly_and_not_tied_to_a_feature() -> None:
    needs = derive_needs(
        ProjectRequirement(
            features=frozenset({Feature.STATIC_FRONTEND}),
            monthly_bandwidth_bytes=10_000_000_000,
        )
    )

    assert needs.quantities == (
        QuantityNeed(
            metric=LimitMetric.BANDWIDTH_BYTES,
            period=LimitPeriod.MONTH,
            required=10_000_000_000,
            applies_to=None,
        ),
    )


def test_missing_quantities_are_omitted() -> None:
    needs = derive_needs(ProjectRequirement(features=frozenset({Feature.DATABASE})))

    assert needs.quantities == ()


def test_missing_budget_stays_none() -> None:
    needs = derive_needs(ProjectRequirement(features=frozenset({Feature.DATABASE})))

    assert needs.budget is None


def test_zero_budget_is_a_free_only_need() -> None:
    needs = derive_needs(
        ProjectRequirement(
            features=frozenset({Feature.DATABASE}),
            monthly_budget_usd_cents=0,
        )
    )

    assert needs.budget == BudgetNeed(max_monthly_usd_cents=0)


def test_positive_budget_keeps_the_amount() -> None:
    needs = derive_needs(
        ProjectRequirement(
            features=frozenset({Feature.DATABASE}),
            monthly_budget_usd_cents=2500,
        )
    )

    assert needs.budget == BudgetNeed(max_monthly_usd_cents=2500)


def test_combined_requirement_derives_every_need() -> None:
    needs = derive_needs(
        ProjectRequirement(
            features=frozenset(
                {
                    Feature.STATIC_FRONTEND,
                    Feature.DATABASE,
                    Feature.FILE_UPLOADS,
                    Feature.AI_API,
                }
            ),
            file_storage_bytes=1_000_000_000,
            database_size_bytes=500_000_000,
            monthly_bandwidth_bytes=10_000_000_000,
            monthly_budget_usd_cents=0,
        )
    )

    assert needs == DerivedNeeds(
        capabilities=(
            CapabilityNeed(
                feature=Feature.STATIC_FRONTEND,
                capability=CapabilityKey.STATIC_HOSTING,
            ),
            CapabilityNeed(feature=Feature.DATABASE, capability=CapabilityKey.DATABASE),
            CapabilityNeed(
                feature=Feature.FILE_UPLOADS,
                capability=CapabilityKey.FILE_STORAGE,
            ),
        ),
        quantities=(
            QuantityNeed(
                metric=LimitMetric.FILE_STORAGE_BYTES,
                period=LimitPeriod.NONE,
                required=1_000_000_000,
                applies_to=Feature.FILE_UPLOADS,
            ),
            QuantityNeed(
                metric=LimitMetric.DATABASE_SIZE_BYTES,
                period=LimitPeriod.NONE,
                required=500_000_000,
                applies_to=Feature.DATABASE,
            ),
            QuantityNeed(
                metric=LimitMetric.BANDWIDTH_BYTES,
                period=LimitPeriod.MONTH,
                required=10_000_000_000,
                applies_to=None,
            ),
        ),
        budget=BudgetNeed(max_monthly_usd_cents=0),
        unevaluated_features=frozenset({Feature.AI_API}),
    )


def test_derive_needs_order_does_not_depend_on_feature_insertion() -> None:
    features = [Feature.SCHEDULED_JOBS, Feature.STATIC_FRONTEND, Feature.AI_API, Feature.DATABASE]
    forward = derive_needs(ProjectRequirement(features=frozenset(features)))
    reverse = derive_needs(ProjectRequirement(features=frozenset(reversed(features))))

    assert forward == reverse
    assert forward == derive_needs(ProjectRequirement(features=frozenset(features)))
    assert tuple(need.feature for need in forward.capabilities) == (
        Feature.STATIC_FRONTEND,
        Feature.DATABASE,
        Feature.SCHEDULED_JOBS,
    )
    assert forward.unevaluated_features == frozenset({Feature.AI_API})
