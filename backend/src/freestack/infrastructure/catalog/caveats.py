from freestack.domain.caveat import Caveat
from freestack.domain.repositories import CaveatCatalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES


class SeedCaveatCatalog(CaveatCatalog):
    """Read caveats converted from catalog seed facts.

    Unmodeled facts stay in infrastructure. Callers depend on CaveatCatalog.
    Caveats are not written to the catalog repository.
    """

    def __init__(self) -> None:
        grouped: dict[str, list[Caveat]] = {}
        for bundle in ALL_BUNDLES:
            for fact in bundle.unmodeled_facts:
                grouped.setdefault(fact.plan_id, []).append(
                    Caveat(
                        plan_id=fact.plan_id,
                        statement=fact.statement,
                        source_id=fact.source_id,
                    )
                )
        self._caveats = {
            plan_id: tuple(caveats) for plan_id, caveats in grouped.items()
        }

    def list_caveats(self, plan_id: str) -> tuple[Caveat, ...]:
        return self._caveats.get(plan_id, ())
