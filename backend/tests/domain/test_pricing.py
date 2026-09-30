from dataclasses import FrozenInstanceError
from enum import StrEnum

import pytest

from freestack.domain.pricing import ExceedBehavior, PlanPricing


class _OtherBehavior(StrEnum):
    CHARGED = "charged"


def _pricing(**overrides: object) -> PlanPricing:
    values: dict[str, object] = {
        "plan_id": "cloudflare-pages-free",
        "monthly_base_fee_usd_cents": 0,
        "exceed_behaviors": frozenset({ExceedBehavior.CHARGED}),
        "source_id": "cloudflare-pages-pricing",
    }
    values.update(overrides)
    return PlanPricing(**values)  # type: ignore[arg-type]


def test_plan_pricing_accepts_zero_base_fee() -> None:
    pricing = _pricing(monthly_base_fee_usd_cents=0)

    assert pricing.monthly_base_fee_usd_cents == 0


def test_plan_pricing_accepts_positive_base_fee() -> None:
    pricing = _pricing(monthly_base_fee_usd_cents=2500)

    assert pricing.monthly_base_fee_usd_cents == 2500


@pytest.mark.parametrize(
    "behavior",
    [ExceedBehavior.CHARGED, ExceedBehavior.SUSPENDED, ExceedBehavior.RESTRICTED],
)
def test_plan_pricing_accepts_each_exceed_behavior(behavior: ExceedBehavior) -> None:
    pricing = _pricing(exceed_behaviors=frozenset({behavior}))

    assert pricing.exceed_behaviors == frozenset({behavior})


def test_plan_pricing_accepts_combined_exceed_behaviors() -> None:
    behaviors = frozenset(
        {
            ExceedBehavior.CHARGED,
            ExceedBehavior.SUSPENDED,
            ExceedBehavior.RESTRICTED,
        }
    )

    pricing = _pricing(exceed_behaviors=behaviors)

    assert pricing.exceed_behaviors == behaviors


@pytest.mark.parametrize("fee", [True, False, -1, 1.5, "0"])
def test_plan_pricing_rejects_invalid_fee(fee: object) -> None:
    with pytest.raises(ValueError, match=r"invalid monthly_base_fee_usd_cents:"):
        _pricing(monthly_base_fee_usd_cents=fee)


@pytest.mark.parametrize(
    "behaviors",
    [
        frozenset(),
        {ExceedBehavior.CHARGED},
        [ExceedBehavior.CHARGED],
        "charged",
        frozenset({_OtherBehavior.CHARGED}),
        frozenset({"charged"}),
    ],
)
def test_plan_pricing_rejects_invalid_exceed_behaviors(behaviors: object) -> None:
    with pytest.raises(ValueError, match=r"invalid exceed_behaviors:"):
        _pricing(exceed_behaviors=behaviors)


@pytest.mark.parametrize("plan_id", ["", "Cloudflare", "cloud_flare"])
def test_plan_pricing_rejects_invalid_plan_id(plan_id: str) -> None:
    with pytest.raises(ValueError, match=r"invalid plan_id:"):
        _pricing(plan_id=plan_id)


@pytest.mark.parametrize("source_id", ["", "Cloudflare", "cloud flare"])
def test_plan_pricing_rejects_invalid_source_id(source_id: str) -> None:
    with pytest.raises(ValueError, match=r"invalid source_id:"):
        _pricing(source_id=source_id)


def test_plan_pricing_is_immutable() -> None:
    pricing = _pricing()

    with pytest.raises(FrozenInstanceError):
        pricing.monthly_base_fee_usd_cents = 1  # type: ignore[misc]


def test_plan_pricing_uses_slots() -> None:
    assert not hasattr(_pricing(), "__dict__")


def test_plan_pricing_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        PlanPricing(
            "cloudflare-pages-free",
            0,
            frozenset({ExceedBehavior.CHARGED}),
            "cloudflare-pages-pricing",
        )  # type: ignore[misc]


def test_plan_pricing_equality_and_hash() -> None:
    left = _pricing()
    right = _pricing()

    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}
