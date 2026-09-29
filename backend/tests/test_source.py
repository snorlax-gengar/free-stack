from dataclasses import FrozenInstanceError
from datetime import date, datetime

import pytest

from freestack.domain.source import Source


def _source(**overrides: object) -> Source:
    values: dict[str, object] = {
        "id": "cloudflare-pages-pricing",
        "url": "https://example.com/pages-pricing",
        "checked_at": date(2026, 9, 29),
        "notes": "fictional test source",
    }
    values.update(overrides)
    return Source(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "url",
    ["https://example.com/pages", "http://example.com/pages"],
)
def test_source_accepts_http_urls(url: str) -> None:
    source = _source(url=url)

    assert source.url == url


def test_source_accepts_date_and_empty_notes() -> None:
    source = _source(checked_at=date(2099, 1, 1), notes="")

    assert source.checked_at == date(2099, 1, 1)
    assert source.notes == ""


@pytest.mark.parametrize(
    "url",
    ["ftp://example.com", "www.example.com", "", "https://example.com/a b"],
)
def test_source_rejects_invalid_url(url: str) -> None:
    with pytest.raises(ValueError, match=r"invalid url:"):
        _source(url=url)


def test_source_rejects_datetime() -> None:
    with pytest.raises(ValueError, match=r"invalid checked_at:"):
        _source(checked_at=datetime(2026, 9, 29, 12, 0, 0))


def test_source_rejects_string_date() -> None:
    with pytest.raises(ValueError, match=r"invalid checked_at:"):
        _source(checked_at="2026-09-29")


@pytest.mark.parametrize("notes", [None, 1])
def test_source_rejects_non_string_notes(notes: object) -> None:
    with pytest.raises(ValueError, match=r"invalid notes:"):
        _source(notes=notes)


def test_source_is_immutable() -> None:
    source = _source()

    with pytest.raises(FrozenInstanceError):
        source.notes = ""  # type: ignore[misc]


def test_source_uses_slots() -> None:
    assert not hasattr(_source(), "__dict__")


def test_source_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        Source(
            "cloudflare-pages-pricing",
            "https://example.com/pages-pricing",
            date(2026, 9, 29),
            "",
        )  # type: ignore[misc]


def test_source_equality_and_hash() -> None:
    left = _source()
    right = _source()

    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}
    assert {left: "catalog"}[right] == "catalog"
