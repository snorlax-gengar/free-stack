from dataclasses import FrozenInstanceError

import pytest

from freestack.domain.service import Service

INVALID_IDENTIFIERS = [
    "",
    "Cloudflare",
    "cloud_flare",
    "cloudflare pages",
    "Cloud-Flare",
]


def _pages() -> Service:
    return Service(
        id="cloudflare-pages",
        provider_id="cloudflare",
        name="Pages",
        slug="pages",
        description="Frontend hosting on Cloudflare.",
    )


def test_create_service() -> None:
    service = _pages()

    assert isinstance(service, Service)


def test_service_fields() -> None:
    service = _pages()

    assert service.id == "cloudflare-pages"
    assert service.provider_id == "cloudflare"
    assert service.name == "Pages"
    assert service.slug == "pages"
    assert service.description == "Frontend hosting on Cloudflare."


def test_service_allows_empty_description() -> None:
    service = Service(
        id="cloudflare-pages",
        provider_id="cloudflare",
        name="Pages",
        slug="pages",
        description="",
    )

    assert service.description == ""


def test_service_is_immutable() -> None:
    service = _pages()

    with pytest.raises(FrozenInstanceError):
        service.name = "Workers"


def test_service_uses_slots() -> None:
    assert not hasattr(_pages(), "__dict__")


def test_service_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        Service("cloudflare-pages", "cloudflare", "Pages", "pages", "")  # type: ignore[misc]


def test_service_equality_and_hash() -> None:
    left = _pages()
    right = _pages()

    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}
    assert {left: "catalog"}[right] == "catalog"


@pytest.mark.parametrize("field", ["id", "provider_id", "slug"])
@pytest.mark.parametrize("value", INVALID_IDENTIFIERS)
def test_service_rejects_invalid_identifier(field: str, value: str) -> None:
    kwargs = {
        "id": "cloudflare-pages",
        "provider_id": "cloudflare",
        "name": "Pages",
        "slug": "pages",
        "description": "",
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=rf"invalid {field}:"):
        Service(**kwargs)


@pytest.mark.parametrize("value", ["", "   "])
def test_service_rejects_blank_name(value: str) -> None:
    with pytest.raises(ValueError, match=r"invalid name:"):
        Service(
            id="cloudflare-pages",
            provider_id="cloudflare",
            name=value,
            slug="pages",
            description="",
        )
