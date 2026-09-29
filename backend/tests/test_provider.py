from dataclasses import FrozenInstanceError

import pytest

from freestack.domain.provider import Provider

INVALID_IDENTIFIERS = [
    "",
    "Cloudflare",
    "cloud_flare",
    "cloudflare pages",
    "Cloud-Flare",
]


def _cloudflare() -> Provider:
    return Provider(
        id="cloudflare",
        name="Cloudflare",
        slug="cloudflare",
        description="Web application, edge network and developer platform services.",
    )


def test_create_provider() -> None:
    provider = _cloudflare()

    assert isinstance(provider, Provider)


def test_provider_fields() -> None:
    provider = _cloudflare()

    assert provider.id == "cloudflare"
    assert provider.name == "Cloudflare"
    assert provider.slug == "cloudflare"
    assert provider.description == (
        "Web application, edge network and developer platform services."
    )


def test_provider_allows_empty_description() -> None:
    provider = Provider(
        id="cloudflare",
        name="Cloudflare",
        slug="cloudflare",
        description="",
    )

    assert provider.description == ""


def test_provider_is_immutable() -> None:
    provider = _cloudflare()

    with pytest.raises(FrozenInstanceError):
        provider.name = "Render"


def test_provider_uses_slots() -> None:
    assert not hasattr(_cloudflare(), "__dict__")


def test_provider_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        Provider("cloudflare", "Cloudflare", "cloudflare", "")  # type: ignore[misc]


def test_provider_equality_and_hash() -> None:
    left = _cloudflare()
    right = _cloudflare()

    assert left == right
    assert hash(left) == hash(right)
    assert {left, right} == {left}
    assert {left: "catalog"}[right] == "catalog"


@pytest.mark.parametrize("field", ["id", "slug"])
@pytest.mark.parametrize("value", INVALID_IDENTIFIERS)
def test_provider_rejects_invalid_identifier(field: str, value: str) -> None:
    kwargs = {
        "id": "cloudflare",
        "name": "Cloudflare",
        "slug": "cloudflare",
        "description": "",
    }
    kwargs[field] = value

    with pytest.raises(ValueError, match=rf"invalid {field}:"):
        Provider(**kwargs)


@pytest.mark.parametrize("value", ["", "   "])
def test_provider_rejects_blank_name(value: str) -> None:
    with pytest.raises(ValueError, match=r"invalid name:"):
        Provider(
            id="cloudflare",
            name=value,
            slug="cloudflare",
            description="",
        )
