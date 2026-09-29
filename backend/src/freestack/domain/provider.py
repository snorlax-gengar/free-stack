from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Provider:
    """An infrastructure provider or platform."""

    id: str
    name: str
    slug: str
    description: str
