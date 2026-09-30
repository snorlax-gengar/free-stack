from typing import Protocol

from freestack.domain.caveat import Caveat
from freestack.domain.limit import Limit
from freestack.domain.plan import Plan
from freestack.domain.pricing import PlanPricing
from freestack.domain.provider import Provider
from freestack.domain.service import Service
from freestack.domain.source import Source


class CatalogRepository(Protocol):
    """Persistence port for the provider, service, and plan catalog."""

    def add_provider(self, provider: Provider) -> None:
        """Store a provider."""
        ...

    def get_provider(self, provider_id: str) -> Provider | None:
        """Return a provider, or None when it is not stored."""
        ...

    def list_providers(self) -> tuple[Provider, ...]:
        """Return stored providers sorted by id."""
        ...

    def add_service(self, service: Service) -> None:
        """Store a service."""
        ...

    def get_service(self, service_id: str) -> Service | None:
        """Return a service, or None when it is not stored."""
        ...

    def list_services(self, provider_id: str) -> tuple[Service, ...]:
        """Return a provider's services sorted by id."""
        ...

    def add_plan(self, plan: Plan) -> None:
        """Store a plan."""
        ...

    def get_plan(self, plan_id: str) -> Plan | None:
        """Return a plan, or None when it is not stored."""
        ...

    def list_plans(self, service_id: str) -> tuple[Plan, ...]:
        """Return a service's plans sorted by id."""
        ...

    def list_all_plans(self) -> tuple[Plan, ...]:
        """Return every stored plan sorted by id."""
        ...

    def add_source(self, source: Source) -> None:
        """Store a source."""
        ...

    def get_source(self, source_id: str) -> Source | None:
        """Return a source, or None when it is not stored."""
        ...

    def list_sources(self) -> tuple[Source, ...]:
        """Return stored sources sorted by id."""
        ...

    def add_limit(self, limit: Limit) -> None:
        """Store a limit."""
        ...

    def list_limits(self, plan_id: str) -> tuple[Limit, ...]:
        """Return a plan's limits sorted by metric, then period."""
        ...

    def add_plan_pricing(self, pricing: PlanPricing) -> None:
        """Store pricing for a plan. Each plan has at most one pricing row."""
        ...

    def get_plan_pricing(self, plan_id: str) -> PlanPricing | None:
        """Return a plan's pricing, or None when it is not stored."""
        ...


class CaveatCatalog(Protocol):
    """Read-only caveat notes. This port does not persist caveats."""

    def list_caveats(self, plan_id: str) -> tuple[Caveat, ...]:
        """Return caveats for a plan, or an empty tuple when there are none."""
        ...
