from freestack.domain.repositories import CatalogRepository
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository
from tests.persistence.catalog_repository_contract import CatalogRepositoryContract


class TestInMemoryCatalogRepository(CatalogRepositoryContract):
    def make_repository(self) -> CatalogRepository:
        return InMemoryCatalogRepository()
