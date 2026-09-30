from freestack.domain.limit import LimitMetric, LimitPeriod
from tests.catalog.conftest import iter_limits


def test_seed_does_not_use_requests_metric(catalog) -> None:
    assert all(limit.metric is not LimitMetric.REQUESTS for limit in iter_limits(catalog))


def test_pages_limits_are_unknown(catalog) -> None:
    assert catalog.list_limits("cloudflare-pages-free") == ()


def test_render_limits_are_unknown(catalog) -> None:
    assert catalog.list_limits("render-web-service-free") == ()


def test_r2_egress_is_explicitly_unlimited(catalog) -> None:
    limits = catalog.list_limits("cloudflare-r2-free")
    egress = next(
        limit
        for limit in limits
        if limit.metric is LimitMetric.BANDWIDTH_BYTES
        and limit.period is LimitPeriod.MONTH
    )

    assert egress.value is None
