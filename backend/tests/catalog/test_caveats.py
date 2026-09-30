import re

from freestack.domain.caveat import Caveat
from freestack.infrastructure.catalog.caveats import SeedCaveatCatalog

_IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

EXPECTED_CAVEATS: dict[str, tuple[tuple[str, str], ...]] = {
    "cloudflare-pages-free": (
        (
            "The Free plan includes 500 builds per month.",
            "cloudflare-pages-limits",
        ),
        (
            "The Free plan allows one build at a time.",
            "cloudflare-pages-limits",
        ),
        (
            "Builds time out after 20 minutes.",
            "cloudflare-pages-limits",
        ),
        (
            "A Free plan site can contain up to 20,000 files.",
            "cloudflare-pages-limits",
        ),
        (
            "A single Pages asset can be at most 25 MiB.",
            "cloudflare-pages-limits",
        ),
        (
            "Requests to Pages Functions count toward the Workers plan quota.",
            "cloudflare-pages-limits",
        ),
    ),
    "cloudflare-r2-free": (
        (
            "The free tier includes 1 million Class A operations per month.",
            "cloudflare-r2-pricing",
        ),
        (
            "The free tier includes 10 million Class B operations per month.",
            "cloudflare-r2-pricing",
        ),
        (
            "The free tier applies only to Standard storage, "
            "and usage beyond the included amount is billed.",
            "cloudflare-r2-pricing",
        ),
    ),
    "render-web-service-free": (
        (
            "Each workspace receives 750 Free instance hours per calendar month.",
            "render-free",
        ),
        (
            "When Free instance hours are exhausted, "
            "Free web services are suspended until the next month.",
            "render-free",
        ),
        (
            "A Free web service spins down after 15 minutes without inbound traffic.",
            "render-free",
        ),
        (
            "Spinning a Free web service back up takes about one minute.",
            "render-free",
        ),
        (
            "Free web services have an ephemeral filesystem.",
            "render-free",
        ),
        (
            "A persistent disk cannot be attached to a Free web service.",
            "render-free",
        ),
        (
            "A Free web service cannot scale beyond a single instance.",
            "render-free",
        ),
        (
            "Render may restart a Free web service at any time.",
            "render-free",
        ),
        (
            "Render says not to use Free instances for production applications.",
            "render-free",
        ),
        (
            "The Free web service compute plan provides 0.1 CPU.",
            "render-compute-plans",
        ),
        (
            "The Free web service compute plan provides 512 MB of RAM.",
            "render-compute-plans",
        ),
    ),
    "supabase-platform-free": (
        (
            "The Free plan includes two projects.",
            "supabase-billing",
        ),
        (
            "The 500 MB database size quota applies per project.",
            "supabase-billing",
        ),
        (
            "The 1 GB storage quota applies per organization.",
            "supabase-billing",
        ),
        (
            "The 5 GB egress quota applies per organization.",
            "supabase-billing",
        ),
        (
            "The Free plan includes 50,000 monthly active users.",
            "supabase-billing",
        ),
        (
            "The Free plan includes 500,000 Edge Function invocations.",
            "supabase-billing",
        ),
        (
            "The Free plan includes 2,000,000 Realtime messages.",
            "supabase-billing",
        ),
        (
            "The Free plan includes 200 Realtime peak connections.",
            "supabase-billing",
        ),
    ),
}


def _listed(catalog: SeedCaveatCatalog, plan_id: str) -> tuple[Caveat, ...]:
    listed = catalog.list_caveats(plan_id)
    assert isinstance(listed, tuple)
    return listed


def test_seed_caveats_match_the_documented_facts() -> None:
    catalog = SeedCaveatCatalog()
    listed = {
        plan_id: _listed(catalog, plan_id) for plan_id in EXPECTED_CAVEATS
    }

    assert sum(len(caveats) for caveats in listed.values()) == 28
    for plan_id, expected in EXPECTED_CAVEATS.items():
        caveats = listed[plan_id]
        assert len(caveats) == len(expected)
        assert tuple((caveat.statement, caveat.source_id) for caveat in caveats) == expected
        assert all(caveat.plan_id == plan_id for caveat in caveats)


def test_missing_plan_has_no_caveats() -> None:
    catalog = SeedCaveatCatalog()

    assert catalog.list_caveats("missing-plan") == ()


def test_seed_caveats_are_readable_notes_with_real_sources(catalog) -> None:
    caveats = [
        caveat
        for plan_id in EXPECTED_CAVEATS
        for caveat in SeedCaveatCatalog().list_caveats(plan_id)
    ]
    stored_source_ids = {source.id for source in catalog.list_sources()}

    assert len(caveats) == 28
    for caveat in caveats:
        assert caveat.statement.strip() != ""
        assert _IDENTIFIER.fullmatch(caveat.plan_id) is not None
        assert _IDENTIFIER.fullmatch(caveat.source_id) is not None
        assert caveat.source_id in stored_source_ids
