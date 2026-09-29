from typing import TypeVar

from freestack.domain.errors import (
    DuplicateEntityError,
    DuplicateSlugError,
    RelatedEntityNotFoundError,
)
from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.repositories import CatalogRepository
from freestack.domain.service import Service


class InMemoryCatalogRepository(CatalogRepository):
    """Catalog repository that stores entities in process memory."""

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}
        self._services: dict[str, Service] = {}
        self._plans: dict[str, Plan] = {}

    def add_provider(self, provider: Provider) -> None:
        if provider.id in self._providers:
            raise DuplicateEntityError(f"provider id already exists: {provider.id}")
        if any(stored.slug == provider.slug for stored in self._providers.values()):
            raise DuplicateSlugError(f"provider slug already exists: {provider.slug}")
        self._providers[provider.id] = provider

    def get_provider(self, provider_id: str) -> Provider | None:
        return self._providers.get(provider_id)

    def list_providers(self) -> tuple[Provider, ...]:
        return _sorted_by_id(self._providers)

    def add_service(self, service: Service) -> None:
        if service.id in self._services:
            raise DuplicateEntityError(f"service id already exists: {service.id}")
        if service.provider_id not in self._providers:
            raise RelatedEntityNotFoundError(
                f"provider not found: {service.provider_id}"
            )
        if any(
            stored.provider_id == service.provider_id and stored.slug == service.slug
            for stored in self._services.values()
        ):
            raise DuplicateSlugError(
                f"service slug already exists for provider {service.provider_id}: {service.slug}"
            )
        self._services[service.id] = service

    def get_service(self, service_id: str) -> Service | None:
        return self._services.get(service_id)

    def list_services(self, provider_id: str) -> tuple[Service, ...]:
        matched = {
            service.id: service
            for service in self._services.values()
            if service.provider_id == provider_id
        }
        return _sorted_by_id(matched)

    def add_plan(self, plan: Plan) -> None:
        if plan.id in self._plans:
            raise DuplicateEntityError(f"plan id already exists: {plan.id}")
        if plan.service_id not in self._services:
            raise RelatedEntityNotFoundError(f"service not found: {plan.service_id}")
        if any(
            stored.service_id == plan.service_id and stored.slug == plan.slug
            for stored in self._plans.values()
        ):
            raise DuplicateSlugError(
                f"plan slug already exists for service {plan.service_id}: {plan.slug}"
            )
        self._plans[plan.id] = plan

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    def list_plans(self, service_id: str) -> tuple[Plan, ...]:
        matched = {
            plan.id: plan
            for plan in self._plans.values()
            if plan.service_id == service_id
        }
        return _sorted_by_id(matched)


EntityT = TypeVar("EntityT", Provider, Service, Plan)


def _sorted_by_id(entities: dict[str, EntityT]) -> tuple[EntityT, ...]:
    return tuple(entities[entity_id] for entity_id in sorted(entities))
