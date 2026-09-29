from dataclasses import dataclass
from datetime import date, datetime

from freestack.domain.validation import require_identifier


@dataclass(frozen=True, slots=True, kw_only=True)
class Source:
    """A document that backs one or more limits."""

    id: str
    url: str
    checked_at: date
    notes: str

    def __post_init__(self) -> None:
        require_identifier(self.id, "id")
        _require_http_url(self.url)
        _require_date(self.checked_at)
        if not isinstance(self.notes, str):
            raise ValueError(f"invalid notes: {self.notes!r}")


def _require_http_url(value: object) -> None:
    if not isinstance(value, str) or value == "" or any(character.isspace() for character in value):
        raise ValueError(f"invalid url: {value!r}")
    scheme, separator, _rest = value.partition("://")
    if separator != "://" or scheme not in {"http", "https"}:
        raise ValueError(f"invalid url: {value!r}")


def _require_date(value: object) -> None:
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError(f"invalid checked_at: {value!r}")
