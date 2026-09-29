from dataclasses import dataclass

from freestack.domain.capability import CapabilityKey
from freestack.domain.validation import require_identifier, require_name


@dataclass(frozen=True, slots=True, kw_only=True)
class Plan:
    """Terms for using one service."""

    id: str
    service_id: str
    name: str
    slug: str
    description: str
    capabilities: frozenset[CapabilityKey] = frozenset()

    def __post_init__(self) -> None:
        require_identifier(self.id, "id")
        require_identifier(self.service_id, "service_id")
        require_identifier(self.slug, "slug")
        require_name(self.name)
        _require_capabilities(self.capabilities)


def _require_capabilities(capabilities: object) -> None:
    if not isinstance(capabilities, frozenset):
        raise ValueError(f"invalid capabilities: {capabilities!r}")
    if any(not isinstance(item, CapabilityKey) for item in capabilities):
        raise ValueError(f"invalid capabilities: {capabilities!r}")
