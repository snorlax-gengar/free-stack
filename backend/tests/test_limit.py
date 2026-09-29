from dataclasses import FrozenInstanceError

import pytest

from freestack.domain.limit import Limit, LimitMetric, LimitPeriod


def _limit(**overrides: object) -> Limit:
    values: dict[str, object] = {
        "plan_id": "cloudflare-pages-free",
        "metric": LimitMetric.REQUESTS,
        "period": LimitPeriod.DAY,
        "value": 100,
        "source_id": "cloudflare-pages-pricing",
    }
    values.update(overrides)
    return Limit(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [None, 0, 1, 10_000])
def test_limit_accepts_documented_values(value: int | None) -> None:
    limit = _limit(value=value)

    assert limit.value == value


@pytest.mark.parametrize("value", [-1, True, False, 1.5, "10"])
def test_limit_rejects_invalid_value(value: object) -> None:
    with pytest.raises(ValueError, match=r"invalid value:"):
        _limit(value=value)


def test_limit_rejects_string_metric() -> None:
    with pytest.raises(ValueError, match=r"invalid metric:"):
        _limit(metric="requests")


def test_limit_rejects_string_period() -> None:
    with pytest.raises(ValueError, match=r"invalid period:"):
        _limit(period="day")


@pytest.mark.parametrize("plan_id", ["", "Cloudflare", "cloud_flare"])
def test_limit_rejects_invalid_plan_id(plan_id: str) -> None:
    with pytest.raises(ValueError, match=r"invalid plan_id:"):
        _limit(plan_id=plan_id)


@pytest.mark.parametrize("source_id", ["", "Cloudflare", "cloud flare"])
def test_limit_rejects_invalid_source_id(source_id: str) -> None:
    with pytest.raises(ValueError, match=r"invalid source_id:"):
        _limit(source_id=source_id)


def test_limit_is_immutable() -> None:
    limit = _limit()

    with pytest.raises(FrozenInstanceError):
        limit.value = 0  # type: ignore[misc]


def test_limit_uses_slots() -> None:
    assert not hasattr(_limit(), "__dict__")


def test_limit_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        Limit(
            "cloudflare-pages-free",
            LimitMetric.REQUESTS,
            LimitPeriod.DAY,
            100,
            "cloudflare-pages-pricing",
        )  # type: ignore[misc]


def test_limit_equality_and_hash() -> None:
    left = _limit()
    right = _limit()

    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}
    assert {left: "catalog"}[right] == "catalog"
