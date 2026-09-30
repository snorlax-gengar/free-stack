from collections.abc import Iterator

import pytest

from freestack.domain.limit import Limit
from freestack.domain.plan import Plan
from freestack.domain.repositories import CatalogRepository
from freestack.infrastructure.catalog.loader import load_catalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository


@pytest.fixture
def catalog() -> CatalogRepository:
    repository = InMemoryCatalogRepository()
    load_catalog(repository, ALL_BUNDLES)
    return repository


def iter_plans(repository: CatalogRepository) -> Iterator[Plan]:
    for provider in repository.list_providers():
        for service in repository.list_services(provider.id):
            yield from repository.list_plans(service.id)


def iter_limits(repository: CatalogRepository) -> Iterator[Limit]:
    for plan in iter_plans(repository):
        yield from repository.list_limits(plan.id)
