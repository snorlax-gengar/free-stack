from datetime import date
from urllib.parse import urlparse

ALLOWED_HOSTS = {
    "developers.cloudflare.com",
    "render.com",
    "supabase.com",
}

OFFICIAL_URLS = {
    "https://developers.cloudflare.com/pages/platform/limits/",
    "https://developers.cloudflare.com/r2/pricing/",
    "https://render.com/docs/free",
    "https://render.com/docs/compute-plans",
    "https://supabase.com/docs/guides/platform/billing-on-supabase",
}


def test_sources_use_official_https_documents(catalog) -> None:
    sources = catalog.list_sources()
    source_ids = [source.id for source in sources]

    assert len(source_ids) == len(set(source_ids))
    assert {source.url for source in sources} == OFFICIAL_URLS
    for source in sources:
        parsed = urlparse(source.url)
        assert parsed.scheme == "https"
        assert parsed.netloc in ALLOWED_HOSTS
        assert type(source.checked_at) is date
        assert not any(character.isspace() for character in source.url)
