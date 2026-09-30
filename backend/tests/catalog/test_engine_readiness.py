from freestack.domain.capability import CapabilityKey
from freestack.domain.limit import LimitMetric
from tests.catalog.conftest import iter_plans


def _plans_with(catalog, capability: CapabilityKey) -> set[str]:
    return {
        plan.id
        for plan in iter_plans(catalog)
        if capability in plan.capabilities
    }


def test_file_storage_plans_are_readable(catalog) -> None:
    assert _plans_with(catalog, CapabilityKey.FILE_STORAGE) == {
        "cloudflare-r2-free",
        "supabase-platform-free",
    }


def test_database_plan_has_a_size_limit(catalog) -> None:
    assert _plans_with(catalog, CapabilityKey.DATABASE) == {"supabase-platform-free"}
    metrics = {
        limit.metric for limit in catalog.list_limits("supabase-platform-free")
    }
    assert LimitMetric.DATABASE_SIZE_BYTES in metrics


def test_server_compute_plan_has_unknown_limits(catalog) -> None:
    assert _plans_with(catalog, CapabilityKey.SERVER_COMPUTE) == {
        "render-web-service-free"
    }
    assert catalog.list_limits("render-web-service-free") == ()
