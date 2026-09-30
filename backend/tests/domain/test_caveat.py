from dataclasses import FrozenInstanceError

import pytest

from freestack.domain.caveat import Caveat


def _caveat(**overrides: object) -> Caveat:
    values: dict[str, object] = {
        "plan_id": "cloudflare-pages-free",
        "statement": "Builds time out after 20 minutes.",
        "source_id": "cloudflare-pages-limits",
    }
    values.update(overrides)
    return Caveat(**values)  # type: ignore[arg-type]


def test_caveat_stores_plan_statement_and_source() -> None:
    caveat = _caveat()

    assert caveat.plan_id == "cloudflare-pages-free"
    assert caveat.statement == "Builds time out after 20 minutes."
    assert caveat.source_id == "cloudflare-pages-limits"
    assert not hasattr(caveat, "id")


@pytest.mark.parametrize("plan_id", ["", "Cloudflare", "cloud_flare"])
def test_caveat_rejects_invalid_plan_id(plan_id: str) -> None:
    with pytest.raises(ValueError, match=r"invalid plan_id:"):
        _caveat(plan_id=plan_id)


@pytest.mark.parametrize("source_id", ["", "Cloudflare", "cloud flare"])
def test_caveat_rejects_invalid_source_id(source_id: str) -> None:
    with pytest.raises(ValueError, match=r"invalid source_id:"):
        _caveat(source_id=source_id)


@pytest.mark.parametrize("statement", ["", "   "])
def test_caveat_rejects_blank_statement(statement: str) -> None:
    with pytest.raises(ValueError, match=r"invalid statement:"):
        _caveat(statement=statement)


def test_caveat_is_immutable() -> None:
    caveat = _caveat()

    with pytest.raises(FrozenInstanceError):
        caveat.statement = "changed"  # type: ignore[misc]


def test_caveat_uses_slots() -> None:
    assert not hasattr(_caveat(), "__dict__")


def test_caveat_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        Caveat(
            "cloudflare-pages-free",
            "Builds time out after 20 minutes.",
            "cloudflare-pages-limits",
        )  # type: ignore[misc]


def test_caveat_equality_and_hash() -> None:
    left = _caveat()
    right = _caveat()

    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}
