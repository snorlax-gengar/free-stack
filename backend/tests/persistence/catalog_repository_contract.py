import pytest

from freestack.domain.errors import (
    DuplicateEntityError,
    DuplicateSlugError,
    RelatedEntityNotFoundError,
)
from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.repositories import CatalogRepository
from freestack.domain.service import Service


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
) -> Plan:
    return Plan(
        id=plan_id,
        service_id=service_id,
        name=name,
        slug=slug,
        description=description,
    )


def _add_pages(repository: CatalogRepository) -> None:
    repository.add_provider(_provider("cloudflare", name="Cloudflare"))
    repository.add_service(
        _service("cloudflare-pages", "cloudflare", name="Pages", slug="pages")
    )
