from freestack.domain.capability import CapabilityKey
from freestack.domain.limit import LimitMetric, LimitPeriod
from freestack.domain.units import GB, MB
from tests.catalog.conftest import iter_limits, iter_plans

EXPECTED_CAPABILITIES = {
    "cloudflare-pages-free": frozenset({CapabilityKey.STATIC_HOSTING}),
    "cloudflare-r2-free": frozenset({CapabilityKey.FILE_STORAGE}),
    "render-web-service-free": frozenset({CapabilityKey.SERVER_COMPUTE}),
    "supabase-platform-free": frozenset(
        {
            CapabilityKey.DATABASE,
            CapabilityKey.AUTHENTICATION,
            CapabilityKey.FILE_STORAGE,
            CapabilityKey.REALTIME,
            CapabilityKey.SERVERLESS_FUNCTIONS,
        }
    ),
}

EXPECTED_LIMITS = {
    (
        "cloudflare-r2-free",
        LimitMetric.FILE_STORAGE_BYTES,
        LimitPeriod.NONE,
        10 * GB,
    ),
    (
        "cloudflare-r2-free",
        LimitMetric.BANDWIDTH_BYTES,
        LimitPeriod.MONTH,
        None,
    ),
    (
        "supabase-platform-free",
        LimitMetric.DATABASE_SIZE_BYTES,
        LimitPeriod.NONE,
        500 * MB,
    ),
    (
        "supabase-platform-free",
        LimitMetric.FILE_STORAGE_BYTES,
        LimitPeriod.NONE,
        1 * GB,
    ),
    (
        "supabase-platform-free",
        LimitMetric.BANDWIDTH_BYTES,
        LimitPeriod.MONTH,
        5 * GB,
    ),
}


def test_plan_capabilities_match_the_seed_contract(catalog) -> None:
    actual = {plan.id: plan.capabilities for plan in iter_plans(catalog)}

    assert actual == EXPECTED_CAPABILITIES


def test_limits_match_the_seed_contract(catalog) -> None:
    actual = {
        (limit.plan_id, limit.metric, limit.period, limit.value)
        for limit in iter_limits(catalog)
    }

    assert actual == EXPECTED_LIMITS
    assert len(actual) == 5
