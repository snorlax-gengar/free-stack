from dataclasses import dataclass

from freestack.domain.validation import require_identifier, require_name


@dataclass(frozen=True, slots=True, kw_only=True)
class Caveat:
    """A sourced note about a plan that is not a stored catalog entity.

    A caveat has no id, is not persisted, and is not a recommendation decision.
    """

    plan_id: str
    statement: str
    source_id: str

    def __post_init__(self) -> None:
        require_identifier(self.plan_id, "plan_id")
        require_identifier(self.source_id, "source_id")
        require_name(self.statement, "statement")
