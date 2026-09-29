class RepositoryError(Exception):
    """Storage-agnostic catalog repository failure."""


class DuplicateEntityError(RepositoryError):
    """An entity with the same id is already stored."""


class DuplicateSlugError(RepositoryError):
    """A slug is already used within its uniqueness scope."""


class RelatedEntityNotFoundError(RepositoryError):
    """A referenced parent entity is not stored."""
