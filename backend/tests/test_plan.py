from dataclasses import FrozenInstanceError

import pytest

from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.service import Service

INVALID_IDENTIFIERS = [
    "",
    "Cloudflare",
    "cloud_flare",
    "cloudflare pages",
    "Cloud-Flare",
]


def _free_plan() -> Plan:
    return Plan(
        id="cloudflare-pages-free",
        service_id="cloudflare-pages",
        name="Free",
        slug="free",
        description="Free tier for Cloudflare Pages.",
    )


def test_create_plan() -> None:
    plan = _free_plan()

    assert isinstance(plan, Plan)


def test_plan_fields() -> None:
    plan = _free_plan()

    assert plan.id == "cloudflare-pages-free"
    assert plan.service_id == "cloudflare-pages"
    assert plan.name == "Free"
    assert plan.slug == "free"
    assert plan.description == "Free tier for Cloudflare Pages."


def test_plan_allows_empty_description() -> None:
    plan = Plan(
        id="cloudflare-pages-free",
        service_id="cloudflare-pages",
        name="Free",
        slug="free",
        description="",
    )

    assert plan.description == ""


def test_plan_is_immutable() -> None:
    plan = _free_plan()

    with pytest.raises(FrozenInstanceError):
        plan.name = "Pro"


def test_plan_uses_slots() -> None:
    assert not hasattr(_free_plan(), "__dict__")


def test_plan_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        Plan("cloudflare-pages-free", "cloudflare-pages", "Free", "free", "")  # type: ignore[misc]


def test_plan_equality_and_hash() -> None:
    left = _free_plan()
    right = _free_plan()

    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}
    assert {left: "catalog"}[right] == "catalog"


@pytest.mark.parametrize("field", ["id", "service_id", "slug"])
@pytest.mark.parametrize("value", INVALID_IDENTIFIERS)
def test_plan_rejects_invalid_identifier(field: str, value: str) -> None:
    kwargs = {
        "id": "cloudflare-pages-free",
        "service_id": "cloudflare-pages",
        "name": "Free",
        "slug": "free",
        "description": "",
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=rf"invalid {field}:"):
        Plan(**kwargs)


@pytest.mark.parametrize("value", ["", "   "])
def test_plan_rejects_blank_name(value: str) -> None:
    with pytest.raises(ValueError, match=r"invalid name:"):
        Plan(
            id="cloudflare-pages-free",
            service_id="cloudflare-pages",
            name=value,
            slug="free",
            description="",
        )


def test_cloudflare_pages_free_relates_by_id() -> None:
    provider = Provider(
        id="cloudflare",
        name="Cloudflare",
        slug="cloudflare",
        description="",
    )
    service = Service(
        id="cloudflare-pages",
        provider_id="cloudflare",
        name="Pages",
        slug="pages",
        description="",
    )
    plan = Plan(
        id="cloudflare-pages-free",
        service_id="cloudflare-pages",
        name="Free",
        slug="free",
        description="",
    )

    assert service.provider_id == provider.id
    assert plan.service_id == service.id
    assert not hasattr(provider, "services")
    assert not hasattr(service, "plans")
