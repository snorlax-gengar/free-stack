import pytest
from dataclasses import FrozenInstanceError

from freestack.domain.provider import Provider


def _cloudflare() -> Provider:
    return Provider(
        id="provider-cloudflare",
        name="Cloudflare",
        slug="cloudflare",
        description="Web application, edge network and developer platform services.",
    )


def test_create_provider() -> None:
    provider = _cloudflare()

    assert isinstance(provider, Provider)


def test_provider_fields() -> None:
    provider = _cloudflare()

    assert provider.id == "provider-cloudflare"
    assert provider.name == "Cloudflare"
    assert provider.slug == "cloudflare"
    assert provider.description == (
        "Web application, edge network and developer platform services."
    )


def test_provider_is_immutable() -> None:
    provider = _cloudflare()

    with pytest.raises(FrozenInstanceError):
        provider.name = "Render"
