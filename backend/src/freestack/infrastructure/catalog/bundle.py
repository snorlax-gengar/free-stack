from dataclasses import dataclass

from freestack.domain.limit import Limit
from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.service import Service
from freestack.domain.source import Source
from freestack.domain.validation import require_identifier, require_name


@dataclass(frozen=True, slots=True, kw_only=True)
class UnmodeledFact:
    """A sourced fact the current domain cannot store as a limit.

    This is infrastructure data for a later caveat design. It is not a domain
    entity and is not written to the catalog repository.
    """

    plan_id: str
    statement: str
    source_id: str

    def __post_init__(self) -> None:
        require_identifier(self.plan_id, "plan_id")
        require_identifier(self.source_id, "source_id")
        require_name(self.statement, "statement")


@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogBundle:
    """One provider's catalog seed, kept outside the domain model."""

    provider: Provider
    services: tuple[Service, ...]
    plans: tuple[Plan, ...]
    sources: tuple[Source, ...]
    limits: tuple[Limit, ...]
    unmodeled_facts: tuple[UnmodeledFact, ...]

    def __post_init__(self) -> None:
        for field_name in ("services", "plans", "sources", "limits", "unmodeled_facts"):
            value = getattr(self, field_name)
            if not isinstance(value, tuple):
                raise ValueError(f"invalid {field_name}: {value!r}")
