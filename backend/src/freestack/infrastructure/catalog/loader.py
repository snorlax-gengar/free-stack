from collections.abc import Iterable

from freestack.domain.repositories import CatalogRepository
from freestack.infrastructure.catalog.bundle import CatalogBundle


def load_catalog(
    repository: CatalogRepository,
    bundles: Iterable[CatalogBundle],
) -> None:
    """Load catalog bundles into a repository.

    Sources are stored first, then providers, services, plans, and limits.
    Unmodeled facts are not stored. A second load of the same data fails with
    the repository's duplicate error.
    """

    loaded = tuple(bundles)
    for bundle in loaded:
        for source in bundle.sources:
            repository.add_source(source)
    for bundle in loaded:
        repository.add_provider(bundle.provider)
    for bundle in loaded:
        for service in bundle.services:
            repository.add_service(service)
    for bundle in loaded:
        for plan in bundle.plans:
            repository.add_plan(plan)
    for bundle in loaded:
        for limit in bundle.limits:
            repository.add_limit(limit)
