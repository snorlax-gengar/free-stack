import pytest
from datetime import date

from freestack.domain.capability import CapabilityKey
from freestack.domain.errors import (
    DuplicateEntityError,
    DuplicateSlugError,
    RelatedEntityNotFoundError,
)
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.plan import Plan
from freestack.domain.pricing import ExceedBehavior, PlanPricing
from freestack.domain.provider import Provider
from freestack.domain.repositories import CatalogRepository
from freestack.domain.service import Service
from freestack.domain.source import Source


class CatalogRepositoryContract:
    """Shared catalog repository behavior for every persistence implementation."""

    def make_repository(self) -> CatalogRepository:
        raise NotImplementedError

    def test_get_provider_returns_saved_provider(self) -> None:
        repository = self.make_repository()
        provider = _provider("cloudflare", name="Cloudflare", description="Edge network.")

        repository.add_provider(provider)

        assert repository.get_provider("cloudflare") == provider

    def test_get_missing_provider_returns_none(self) -> None:
        repository = self.make_repository()

        assert repository.get_provider("unknown") is None

    def test_list_providers_returns_tuple(self) -> None:
        repository = self.make_repository()
        repository.add_provider(_provider("cloudflare", name="Cloudflare"))

        listed = repository.list_providers()

        assert isinstance(listed, tuple)
        assert listed == (_provider("cloudflare", name="Cloudflare"),)

    def test_list_providers_empty_returns_empty_tuple(self) -> None:
        repository = self.make_repository()

        assert repository.list_providers() == ()

    def test_duplicate_provider_id_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        original = _provider("cloudflare", name="Cloudflare")
        repository.add_provider(original)

        with pytest.raises(DuplicateEntityError):
            repository.add_provider(_provider("cloudflare", name="Other", slug="other"))

        assert repository.get_provider("cloudflare") == original
        assert repository.list_providers() == (original,)

    def test_duplicate_provider_slug_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        original = _provider("cloudflare", name="Cloudflare", slug="cloudflare")
        repository.add_provider(original)

        with pytest.raises(DuplicateSlugError):
            repository.add_provider(_provider("other", name="Other", slug="cloudflare"))

        assert repository.get_provider("other") is None
        assert repository.list_providers() == (original,)

    def test_list_providers_is_sorted_by_id(self) -> None:
        repository = self.make_repository()
        for provider_id in ("z-provider", "a-provider", "m-provider"):
            repository.add_provider(_provider(provider_id))

        assert tuple(provider.id for provider in repository.list_providers()) == (
            "a-provider",
            "m-provider",
            "z-provider",
        )

    def test_get_service_returns_saved_service(self) -> None:
        repository = self.make_repository()
        repository.add_provider(_provider("cloudflare", name="Cloudflare"))
        service = _service("cloudflare-pages", "cloudflare", name="Pages", slug="pages")

        repository.add_service(service)

        assert repository.get_service("cloudflare-pages") == service

    def test_get_missing_service_returns_none(self) -> None:
        repository = self.make_repository()

        assert repository.get_service("unknown") is None

    def test_list_services_returns_services_for_provider(self) -> None:
        repository = self.make_repository()
        repository.add_provider(_provider("cloudflare", name="Cloudflare"))
        repository.add_provider(_provider("vercel", name="Vercel"))
        pages = _service("cloudflare-pages", "cloudflare", name="Pages", slug="pages")
        r2 = _service("cloudflare-r2", "cloudflare", name="R2", slug="r2")
        vercel_api = _service("vercel-api", "vercel", name="API", slug="api")
        repository.add_service(pages)
        repository.add_service(r2)
        repository.add_service(vercel_api)

        assert repository.list_services("missing") == ()
        assert repository.list_services("cloudflare") == (pages, r2)
        assert repository.list_services("vercel") == (vercel_api,)

    def test_add_service_missing_provider_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        service = _service("pages", "unknown", name="Pages", slug="pages")

        with pytest.raises(RelatedEntityNotFoundError):
            repository.add_service(service)

        assert repository.get_service("pages") is None
        assert repository.list_services("unknown") == ()

    def test_duplicate_service_id_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        repository.add_provider(_provider("cloudflare", name="Cloudflare"))
        original = _service("cloudflare-pages", "cloudflare", name="Pages", slug="pages")
        repository.add_service(original)

        with pytest.raises(DuplicateEntityError):
            repository.add_service(
                _service("cloudflare-pages", "cloudflare", name="Other", slug="other")
            )

        assert repository.get_service("cloudflare-pages") == original
        assert repository.list_services("cloudflare") == (original,)

    def test_duplicate_service_slug_in_provider_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        repository.add_provider(_provider("cloudflare", name="Cloudflare"))
        original = _service("cloudflare-pages", "cloudflare", name="Pages", slug="pages")
        repository.add_service(original)

        with pytest.raises(DuplicateSlugError):
            repository.add_service(
                _service("cloudflare-workers", "cloudflare", name="Workers", slug="pages")
            )

        assert repository.get_service("cloudflare-workers") is None
        assert repository.list_services("cloudflare") == (original,)

    def test_same_service_slug_allowed_for_different_providers(self) -> None:
        repository = self.make_repository()
        repository.add_provider(_provider("alpha", name="Alpha"))
        repository.add_provider(_provider("beta", name="Beta"))
        alpha_api = _service("alpha-api", "alpha", name="API", slug="api")
        beta_api = _service("beta-api", "beta", name="API", slug="api")

        repository.add_service(alpha_api)
        repository.add_service(beta_api)

        assert repository.get_service("alpha-api") == alpha_api
        assert repository.get_service("beta-api") == beta_api

    def test_list_services_is_sorted_by_id(self) -> None:
        repository = self.make_repository()
        repository.add_provider(_provider("cloudflare", name="Cloudflare"))
        for service_id in ("z-service", "a-service", "m-service"):
            repository.add_service(
                _service(service_id, "cloudflare", name="Service", slug=service_id)
            )

        assert tuple(service.id for service in repository.list_services("cloudflare")) == (
            "a-service",
            "m-service",
            "z-service",
        )

    def test_get_plan_returns_saved_plan(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        plan = _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")

        repository.add_plan(plan)

        assert repository.get_plan("cloudflare-pages-free") == plan

    def test_get_missing_plan_returns_none(self) -> None:
        repository = self.make_repository()

        assert repository.get_plan("unknown") is None

    def test_list_plans_returns_plans_for_service(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        repository.add_service(_service("cloudflare-r2", "cloudflare", name="R2", slug="r2"))
        pages_free = _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")
        r2_free = _plan("cloudflare-r2-free", "cloudflare-r2", name="Free", slug="free")
        repository.add_plan(pages_free)
        repository.add_plan(r2_free)

        assert repository.list_plans("missing") == ()
        assert repository.list_plans("cloudflare-pages") == (pages_free,)
        assert repository.list_plans("cloudflare-r2") == (r2_free,)

    def test_add_plan_missing_service_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        plan = _plan("pages-free", "unknown", name="Free", slug="free")

        with pytest.raises(RelatedEntityNotFoundError):
            repository.add_plan(plan)

        assert repository.get_plan("pages-free") is None
        assert repository.list_plans("unknown") == ()

    def test_duplicate_plan_id_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        original = _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")
        repository.add_plan(original)

        with pytest.raises(DuplicateEntityError):
            repository.add_plan(
                _plan("cloudflare-pages-free", "cloudflare-pages", name="Other", slug="other")
            )

        assert repository.get_plan("cloudflare-pages-free") == original
        assert repository.list_plans("cloudflare-pages") == (original,)

    def test_duplicate_plan_slug_in_service_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        original = _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")
        repository.add_plan(original)

        with pytest.raises(DuplicateSlugError):
            repository.add_plan(
                _plan("cloudflare-pages-pro", "cloudflare-pages", name="Pro", slug="free")
            )

        assert repository.get_plan("cloudflare-pages-pro") is None
        assert repository.list_plans("cloudflare-pages") == (original,)

    def test_same_plan_slug_allowed_for_different_services(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        repository.add_service(_service("cloudflare-r2", "cloudflare", name="R2", slug="r2"))
        pages_free = _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")
        r2_free = _plan("cloudflare-r2-free", "cloudflare-r2", name="Free", slug="free")

        repository.add_plan(pages_free)
        repository.add_plan(r2_free)

        assert repository.get_plan("cloudflare-pages-free") == pages_free
        assert repository.get_plan("cloudflare-r2-free") == r2_free

    def test_list_plans_is_sorted_by_id(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        for plan_id in ("z-plan", "a-plan", "m-plan"):
            repository.add_plan(
                _plan(plan_id, "cloudflare-pages", name="Plan", slug=plan_id)
            )

        assert tuple(plan.id for plan in repository.list_plans("cloudflare-pages")) == (
            "a-plan",
            "m-plan",
            "z-plan",
        )

    def test_list_all_plans_empty_returns_empty_tuple(self) -> None:
        repository = self.make_repository()

        assert repository.list_all_plans() == ()

    def test_list_all_plans_returns_plans_from_every_service(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        repository.add_service(_service("cloudflare-r2", "cloudflare", name="R2", slug="r2"))
        pages_free = _plan(
            "cloudflare-pages-free",
            "cloudflare-pages",
            name="Free",
            slug="free",
        )
        r2_free = _plan("cloudflare-r2-free", "cloudflare-r2", name="Free", slug="free")
        repository.add_plan(pages_free)
        repository.add_plan(r2_free)

        listed = repository.list_all_plans()

        assert isinstance(listed, tuple)
        assert listed == (pages_free, r2_free)

    def test_list_all_plans_is_sorted_by_id_independent_of_insertion_order(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        repository.add_service(_service("cloudflare-r2", "cloudflare", name="R2", slug="r2"))
        repository.add_plan(
            _plan("z-plan", "cloudflare-pages", name="Plan", slug="z-plan")
        )
        repository.add_plan(_plan("a-plan", "cloudflare-r2", name="Plan", slug="a-plan"))
        repository.add_plan(
            _plan("m-plan", "cloudflare-pages", name="Plan", slug="m-plan")
        )

        listed = repository.list_all_plans()

        assert isinstance(listed, tuple)
        assert tuple(plan.id for plan in listed) == ("a-plan", "m-plan", "z-plan")

    def test_cloudflare_pages_and_r2_free_plans(self) -> None:
        repository = self.make_repository()
        provider = _provider("cloudflare", name="Cloudflare", slug="cloudflare")
        pages = _service(
            "cloudflare-pages",
            "cloudflare",
            name="Pages",
            slug="pages",
        )
        r2 = _service("cloudflare-r2", "cloudflare", name="R2", slug="r2")
        pages_free = _plan(
            "cloudflare-pages-free",
            "cloudflare-pages",
            name="Free",
            slug="free",
        )
        r2_free = _plan("cloudflare-r2-free", "cloudflare-r2", name="Free", slug="free")

        repository.add_provider(provider)
        repository.add_service(pages)
        repository.add_service(r2)
        repository.add_plan(pages_free)
        repository.add_plan(r2_free)

        assert repository.get_provider("cloudflare") == provider
        assert repository.list_services("cloudflare") == (pages, r2)
        assert pages.provider_id == provider.id
        assert r2.provider_id == provider.id
        assert repository.list_plans("cloudflare-pages") == (pages_free,)
        assert repository.list_plans("cloudflare-r2") == (r2_free,)
        assert pages_free.service_id == pages.id
        assert r2_free.service_id == r2.id

    def test_plan_capabilities_are_preserved(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        capabilities = frozenset(
            {CapabilityKey.STATIC_HOSTING, CapabilityKey.SERVERLESS_FUNCTIONS}
        )
        plan = _plan(
            "cloudflare-pages-free",
            "cloudflare-pages",
            name="Free",
            slug="free",
            capabilities=capabilities,
        )

        repository.add_plan(plan)

        stored = repository.get_plan("cloudflare-pages-free")
        assert stored == plan
        assert stored is not None
        assert stored.capabilities == capabilities

    def test_get_source_returns_saved_source(self) -> None:
        repository = self.make_repository()
        source = _source("cloudflare-pages-pricing")

        repository.add_source(source)

        assert repository.get_source("cloudflare-pages-pricing") == source

    def test_get_missing_source_returns_none(self) -> None:
        repository = self.make_repository()

        assert repository.get_source("unknown") is None

    def test_list_sources_returns_tuple(self) -> None:
        repository = self.make_repository()
        source = _source("cloudflare-pages-pricing")
        repository.add_source(source)

        listed = repository.list_sources()

        assert isinstance(listed, tuple)
        assert listed == (source,)

    def test_list_sources_empty_returns_empty_tuple(self) -> None:
        repository = self.make_repository()

        assert repository.list_sources() == ()

    def test_list_sources_is_sorted_by_id(self) -> None:
        repository = self.make_repository()
        for source_id in ("z-source", "a-source", "m-source"):
            repository.add_source(_source(source_id, url=f"https://example.com/{source_id}"))

        assert tuple(source.id for source in repository.list_sources()) == (
            "a-source",
            "m-source",
            "z-source",
        )

    def test_duplicate_source_id_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        original = _source("cloudflare-pages-pricing", url="https://example.com/pages")
        repository.add_source(original)

        with pytest.raises(DuplicateEntityError):
            repository.add_source(
                _source("cloudflare-pages-pricing", url="https://example.com/other")
            )

        assert repository.get_source("cloudflare-pages-pricing") == original
        assert repository.list_sources() == (original,)

    def test_duplicate_source_url_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        original = _source("cloudflare-pages-pricing", url="https://example.com/pages")
        repository.add_source(original)

        with pytest.raises(DuplicateEntityError):
            repository.add_source(
                _source("other-source", url="https://example.com/pages")
            )

        assert repository.get_source("other-source") is None
        assert repository.list_sources() == (original,)

    def test_distinct_source_urls_are_not_normalized(self) -> None:
        repository = self.make_repository()
        first = _source("pages-doc", url="https://example.com/pages")
        second = _source("pages-doc-slash", url="https://example.com/pages/")

        repository.add_source(first)
        repository.add_source(second)

        assert repository.list_sources() == (first, second)

    def test_multiple_sources_can_be_stored(self) -> None:
        repository = self.make_repository()
        pages = _source("cloudflare-pages-pricing", url="https://example.com/pages")
        r2 = _source("cloudflare-r2-pricing", url="https://example.com/r2")

        repository.add_source(pages)
        repository.add_source(r2)

        assert repository.get_source("cloudflare-pages-pricing") == pages
        assert repository.get_source("cloudflare-r2-pricing") == r2

    def test_add_limit_and_list_limits_for_plan(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        limit = _limit(
            "cloudflare-pages-free",
            LimitMetric.REQUESTS,
            LimitPeriod.DAY,
            value=10,
        )

        repository.add_limit(limit)

        assert repository.list_limits("cloudflare-pages-free") == (limit,)

    def test_add_limit_missing_plan_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        repository.add_source(_source("cloudflare-pages-pricing"))

        with pytest.raises(RelatedEntityNotFoundError):
            repository.add_limit(
                _limit("missing-plan", LimitMetric.REQUESTS, LimitPeriod.DAY)
            )

        assert repository.list_limits("missing-plan") == ()

    def test_add_limit_missing_source_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        repository.add_plan(
            _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")
        )

        with pytest.raises(RelatedEntityNotFoundError):
            repository.add_limit(
                _limit(
                    "cloudflare-pages-free",
                    LimitMetric.REQUESTS,
                    LimitPeriod.DAY,
                    source_id="missing-source",
                )
            )

        assert repository.list_limits("cloudflare-pages-free") == ()

    def test_duplicate_limit_natural_key_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        original = _limit(
            "cloudflare-pages-free",
            LimitMetric.REQUESTS,
            LimitPeriod.DAY,
            value=10,
        )
        repository.add_limit(original)

        with pytest.raises(DuplicateEntityError):
            repository.add_limit(
                _limit(
                    "cloudflare-pages-free",
                    LimitMetric.REQUESTS,
                    LimitPeriod.DAY,
                    value=99,
                )
            )

        assert repository.list_limits("cloudflare-pages-free") == (original,)

    def test_same_metric_with_different_period_is_allowed(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        daily = _limit(
            "cloudflare-pages-free",
            LimitMetric.REQUESTS,
            LimitPeriod.DAY,
            value=10,
        )
        monthly = _limit(
            "cloudflare-pages-free",
            LimitMetric.REQUESTS,
            LimitPeriod.MONTH,
            value=100,
        )

        repository.add_limit(daily)
        repository.add_limit(monthly)

        assert repository.list_limits("cloudflare-pages-free") == (daily, monthly)

    def test_same_limit_key_is_allowed_for_different_plans(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        repository.add_service(_service("cloudflare-r2", "cloudflare", name="R2", slug="r2"))
        repository.add_plan(_plan("cloudflare-r2-free", "cloudflare-r2", name="Free", slug="free"))
        pages_limit = _limit(
            "cloudflare-pages-free",
            LimitMetric.REQUESTS,
            LimitPeriod.DAY,
            value=10,
        )
        r2_limit = _limit(
            "cloudflare-r2-free",
            LimitMetric.REQUESTS,
            LimitPeriod.DAY,
            value=20,
        )

        repository.add_limit(pages_limit)
        repository.add_limit(r2_limit)

        assert repository.list_limits("cloudflare-pages-free") == (pages_limit,)
        assert repository.list_limits("cloudflare-r2-free") == (r2_limit,)

    def test_list_limits_for_unknown_plan_returns_empty_tuple(self) -> None:
        repository = self.make_repository()

        assert repository.list_limits("missing-plan") == ()

    def test_limits_can_share_one_source(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        storage = _limit(
            "cloudflare-pages-free",
            LimitMetric.FILE_STORAGE_BYTES,
            LimitPeriod.NONE,
            value=None,
        )
        bandwidth = _limit(
            "cloudflare-pages-free",
            LimitMetric.BANDWIDTH_BYTES,
            LimitPeriod.MONTH,
            value=0,
        )

        repository.add_limit(storage)
        repository.add_limit(bandwidth)

        listed = repository.list_limits("cloudflare-pages-free")
        assert listed == (bandwidth, storage)
        assert {limit.source_id for limit in listed} == {"cloudflare-pages-pricing"}
        assert storage.value is None
        assert bandwidth.value == 0

    def test_list_limits_is_sorted_by_metric_then_period(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        build_month = _limit(
            "cloudflare-pages-free",
            LimitMetric.BUILD_SECONDS,
            LimitPeriod.MONTH,
            value=3,
        )
        bandwidth_month = _limit(
            "cloudflare-pages-free",
            LimitMetric.BANDWIDTH_BYTES,
            LimitPeriod.MONTH,
            value=2,
        )
        bandwidth_day = _limit(
            "cloudflare-pages-free",
            LimitMetric.BANDWIDTH_BYTES,
            LimitPeriod.DAY,
            value=1,
        )

        repository.add_limit(build_month)
        repository.add_limit(bandwidth_month)
        repository.add_limit(bandwidth_day)

        assert repository.list_limits("cloudflare-pages-free") == (
            bandwidth_day,
            bandwidth_month,
            build_month,
        )

    def test_cloudflare_catalog_metadata_uses_fictional_values(self) -> None:
        """Exercise catalog metadata. The numbers are not real provider limits."""

        repository = self.make_repository()
        _add_pages(repository)
        repository.add_service(_service("cloudflare-r2", "cloudflare", name="R2", slug="r2"))
        pages_free = _plan(
            "cloudflare-pages-free",
            "cloudflare-pages",
            name="Free",
            slug="free",
            capabilities=frozenset({CapabilityKey.STATIC_HOSTING}),
        )
        r2_free = _plan(
            "cloudflare-r2-free",
            "cloudflare-r2",
            name="Free",
            slug="free",
            capabilities=frozenset({CapabilityKey.FILE_STORAGE}),
        )
        pages_source = _source(
            "cloudflare-pages-pricing",
            url="https://example.com/pages-pricing",
        )
        r2_source = _source("cloudflare-r2-pricing", url="https://example.com/r2-pricing")
        bandwidth = _limit(
            "cloudflare-pages-free",
            LimitMetric.BANDWIDTH_BYTES,
            LimitPeriod.MONTH,
            value=111,
            source_id="cloudflare-pages-pricing",
        )
        builds = _limit(
            "cloudflare-pages-free",
            LimitMetric.BUILD_SECONDS,
            LimitPeriod.MONTH,
            value=222,
            source_id="cloudflare-pages-pricing",
        )
        storage = _limit(
            "cloudflare-r2-free",
            LimitMetric.FILE_STORAGE_BYTES,
            LimitPeriod.NONE,
            value=333,
            source_id="cloudflare-r2-pricing",
        )

        repository.add_plan(pages_free)
        repository.add_plan(r2_free)
        repository.add_source(pages_source)
        repository.add_source(r2_source)
        repository.add_limit(builds)
        repository.add_limit(bandwidth)
        repository.add_limit(storage)

        assert repository.get_plan("cloudflare-pages-free") == pages_free
        assert repository.get_plan("cloudflare-r2-free") == r2_free
        assert repository.list_limits("cloudflare-pages-free") == (bandwidth, builds)
        assert repository.list_limits("cloudflare-r2-free") == (storage,)
        assert repository.list_sources() == (pages_source, r2_source)

    def test_add_plan_pricing_missing_plan_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        source = _source("cloudflare-pages-pricing")
        repository.add_source(source)

        with pytest.raises(RelatedEntityNotFoundError, match="plan not found"):
            repository.add_plan_pricing(_pricing("missing-plan"))

        assert repository.get_plan_pricing("missing-plan") is None
        assert repository.list_sources() == (source,)
        assert repository.list_all_plans() == ()

    def test_add_plan_pricing_checks_plan_before_source(self) -> None:
        repository = self.make_repository()

        with pytest.raises(RelatedEntityNotFoundError, match="plan not found"):
            repository.add_plan_pricing(
                _pricing("missing-plan", source_id="missing-source")
            )

        assert repository.get_plan_pricing("missing-plan") is None

    def test_add_plan_pricing_missing_source_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        _add_pages(repository)
        plan = _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")
        repository.add_plan(plan)

        with pytest.raises(RelatedEntityNotFoundError, match="source not found"):
            repository.add_plan_pricing(_pricing(source_id="missing-source"))

        assert repository.get_plan("cloudflare-pages-free") == plan
        assert repository.get_plan_pricing("cloudflare-pages-free") is None
        assert repository.list_sources() == ()

    def test_duplicate_plan_pricing_raises_and_keeps_state(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        original = _pricing(
            monthly_base_fee_usd_cents=0,
            exceed_behaviors=frozenset({ExceedBehavior.SUSPENDED}),
        )
        repository.add_plan_pricing(original)

        with pytest.raises(DuplicateEntityError):
            repository.add_plan_pricing(
                _pricing(
                    monthly_base_fee_usd_cents=500,
                    exceed_behaviors=frozenset({ExceedBehavior.CHARGED}),
                )
            )

        assert repository.get_plan_pricing("cloudflare-pages-free") == original

    def test_get_plan_pricing_returns_saved_pricing(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        behaviors = frozenset({ExceedBehavior.CHARGED, ExceedBehavior.RESTRICTED})
        pricing = _pricing(
            monthly_base_fee_usd_cents=2500,
            exceed_behaviors=behaviors,
        )

        repository.add_plan_pricing(pricing)

        stored = repository.get_plan_pricing("cloudflare-pages-free")
        assert stored == pricing
        assert stored is not None
        assert stored.exceed_behaviors == behaviors
        assert stored.monthly_base_fee_usd_cents == 2500

    def test_get_missing_plan_pricing_returns_none(self) -> None:
        repository = self.make_repository()

        assert repository.get_plan_pricing("missing-plan") is None

    def test_each_plan_can_store_one_pricing(self) -> None:
        repository = self.make_repository()
        _add_priced_plan(repository)
        repository.add_service(_service("cloudflare-r2", "cloudflare", name="R2", slug="r2"))
        repository.add_plan(_plan("cloudflare-r2-free", "cloudflare-r2", name="Free", slug="free"))
        repository.add_source(_source("cloudflare-r2-pricing", url="https://example.com/r2"))
        pages_pricing = _pricing(monthly_base_fee_usd_cents=0)
        r2_pricing = _pricing(
            "cloudflare-r2-free",
            monthly_base_fee_usd_cents=100,
            source_id="cloudflare-r2-pricing",
            exceed_behaviors=frozenset({ExceedBehavior.CHARGED}),
        )

        repository.add_plan_pricing(pages_pricing)
        repository.add_plan_pricing(r2_pricing)

        assert repository.get_plan_pricing("cloudflare-pages-free") == pages_pricing
        assert repository.get_plan_pricing("cloudflare-r2-free") == r2_pricing


def _provider(
    provider_id: str,
    *,
    name: str = "Name",
    slug: str | None = None,
    description: str = "",
) -> Provider:
    return Provider(
        id=provider_id,
        name=name,
        slug=provider_id if slug is None else slug,
        description=description,
    )


def _service(
    service_id: str,
    provider_id: str,
    *,
    name: str,
    slug: str,
    description: str = "",
) -> Service:
    return Service(
        id=service_id,
        provider_id=provider_id,
        name=name,
        slug=slug,
        description=description,
    )


def _plan(
    plan_id: str,
    service_id: str,
    *,
    name: str,
    slug: str,
    description: str = "",
    capabilities: frozenset[CapabilityKey] = frozenset(),
) -> Plan:
    return Plan(
        id=plan_id,
        service_id=service_id,
        name=name,
        slug=slug,
        description=description,
        capabilities=capabilities,
    )


def _source(
    source_id: str,
    *,
    url: str = "https://example.com/source",
    notes: str = "",
) -> Source:
    return Source(
        id=source_id,
        url=url,
        checked_at=date(2026, 9, 29),
        notes=notes,
    )


def _limit(
    plan_id: str,
    metric: LimitMetric,
    period: LimitPeriod,
    *,
    value: int | None = 1,
    source_id: str = "cloudflare-pages-pricing",
) -> Limit:
    return Limit(
        plan_id=plan_id,
        metric=metric,
        period=period,
        value=value,
        source_id=source_id,
    )


def _add_pages(repository: CatalogRepository) -> None:
    repository.add_provider(_provider("cloudflare", name="Cloudflare"))
    repository.add_service(
        _service("cloudflare-pages", "cloudflare", name="Pages", slug="pages")
    )


def _pricing(
    plan_id: str = "cloudflare-pages-free",
    *,
    monthly_base_fee_usd_cents: int = 0,
    exceed_behaviors: frozenset[ExceedBehavior] | None = None,
    source_id: str = "cloudflare-pages-pricing",
) -> PlanPricing:
    if exceed_behaviors is None:
        exceed_behaviors = frozenset({ExceedBehavior.CHARGED})
    return PlanPricing(
        plan_id=plan_id,
        monthly_base_fee_usd_cents=monthly_base_fee_usd_cents,
        exceed_behaviors=exceed_behaviors,
        source_id=source_id,
    )


def _add_priced_plan(repository: CatalogRepository) -> None:
    _add_pages(repository)
    repository.add_plan(
        _plan("cloudflare-pages-free", "cloudflare-pages", name="Free", slug="free")
    )
    repository.add_source(_source("cloudflare-pages-pricing"))
