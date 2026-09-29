from typing import Protocol

from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.service import Service


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
