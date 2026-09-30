from freestack.application.composition import StackCompositionService
from freestack.application.recommendation import RecommendationService
from freestack.infrastructure.catalog.caveats import SeedCaveatCatalog
from freestack.infrastructure.catalog.loader import load_catalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository

DEFAULT_MAX_COMBINATIONS = 10


def get_stack_composition_service() -> StackCompositionService:
    """Build the composition service from the seed catalog.

    ``max_combinations`` is an API policy, not a request field.
    """

    repository = InMemoryCatalogRepository()
    load_catalog(repository, ALL_BUNDLES)
    return StackCompositionService(
        recommendations=RecommendationService(catalog=repository, caveats=SeedCaveatCatalog()),
        max_combinations=DEFAULT_MAX_COMBINATIONS,
    )
