import pytest

from freestack.domain.errors import DuplicateEntityError
from freestack.infrastructure.catalog.loader import load_catalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository


def test_empty_bundles_load() -> None:
    repository = InMemoryCatalogRepository()

    load_catalog(repository, ())

    assert repository.list_providers() == ()
    assert repository.list_sources() == ()


def test_full_catalog_loads(catalog) -> None:
    assert len(catalog.list_providers()) == 3
    assert len(catalog.list_sources()) == 5


def test_second_load_raises_duplicate_entity_error(catalog) -> None:
    with pytest.raises(DuplicateEntityError):
        load_catalog(catalog, ALL_BUNDLES)
