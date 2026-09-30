from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from tests.catalog.conftest import iter_limits, iter_plans


def test_catalog_counts(catalog) -> None:
    services = [
        service
        for provider in catalog.list_providers()
        for service in catalog.list_services(provider.id)
    ]
    plans = list(iter_plans(catalog))
    limits = list(iter_limits(catalog))

    assert len(catalog.list_providers()) == 3
    assert len(services) == 4
    assert len(plans) == 4
    assert len(limits) == 5
    assert len(catalog.list_sources()) == 5


def test_services_reference_existing_providers(catalog) -> None:
    provider_ids = {provider.id for provider in catalog.list_providers()}

    for provider in catalog.list_providers():
        for service in catalog.list_services(provider.id):
            assert service.provider_id in provider_ids


def test_plans_reference_existing_services(catalog) -> None:
    service_ids = {
        service.id
        for provider in catalog.list_providers()
        for service in catalog.list_services(provider.id)
    }

    for plan in iter_plans(catalog):
        assert plan.service_id in service_ids


def test_limits_reference_existing_plans_and_sources(catalog) -> None:
    plan_ids = {plan.id for plan in iter_plans(catalog)}
    source_ids = {source.id for source in catalog.list_sources()}

    for limit in iter_limits(catalog):
        assert limit.plan_id in plan_ids
        assert limit.source_id in source_ids


def test_sources_can_be_shared_and_none_are_orphaned(catalog) -> None:
    limits = list(iter_limits(catalog))
    source_counts: dict[str, int] = {}
    for limit in limits:
        source_counts[limit.source_id] = source_counts.get(limit.source_id, 0) + 1

    assert any(count > 1 for count in source_counts.values())

    referenced = set(source_counts)
    for bundle in ALL_BUNDLES:
        referenced.update(fact.source_id for fact in bundle.unmodeled_facts)

    stored = {source.id for source in catalog.list_sources()}
    assert stored == referenced


def test_unmodeled_facts_reference_existing_plans_and_sources(catalog) -> None:
    plan_ids = {plan.id for plan in iter_plans(catalog)}
    source_ids = {source.id for source in catalog.list_sources()}

    for bundle in ALL_BUNDLES:
        for fact in bundle.unmodeled_facts:
            assert fact.plan_id in plan_ids
            assert fact.source_id in source_ids
