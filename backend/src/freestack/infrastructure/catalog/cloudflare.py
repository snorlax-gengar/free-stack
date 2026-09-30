from datetime import date

from freestack.domain.capability import CapabilityKey
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.service import Service
from freestack.domain.source import Source
from freestack.domain.units import GB
from freestack.infrastructure.catalog.bundle import CatalogBundle, UnmodeledFact

CHECKED_AT = date(2026, 9, 30)

CLOUDFLARE = CatalogBundle(
    provider=Provider(
        id="cloudflare",
        name="Cloudflare",
        slug="cloudflare",
        description="Edge network and developer platform.",
    ),
    services=(
        Service(
            id="cloudflare-pages",
            provider_id="cloudflare",
            name="Pages",
            slug="pages",
            description="Static site hosting.",
        ),
        Service(
            id="cloudflare-r2",
            provider_id="cloudflare",
            name="R2",
            slug="r2",
            description="Object storage.",
        ),
    ),
    plans=(
        Plan(
            id="cloudflare-pages-free",
            service_id="cloudflare-pages",
            name="Free",
            slug="free",
            description="Free Cloudflare Pages plan.",
            capabilities=frozenset({CapabilityKey.STATIC_HOSTING}),
        ),
        Plan(
            id="cloudflare-r2-free",
            service_id="cloudflare-r2",
            name="Free",
            slug="free",
            description="Free Cloudflare R2 allowance.",
            capabilities=frozenset({CapabilityKey.FILE_STORAGE}),
        ),
    ),
    sources=(
        Source(
            id="cloudflare-pages-limits",
            url="https://developers.cloudflare.com/pages/platform/limits/",
            checked_at=CHECKED_AT,
            notes="Official Cloudflare Pages limits.",
        ),
        Source(
            id="cloudflare-r2-pricing",
            url="https://developers.cloudflare.com/r2/pricing/",
            checked_at=CHECKED_AT,
            notes="Official Cloudflare R2 pricing.",
        ),
    ),
    limits=(
        Limit(
            plan_id="cloudflare-r2-free",
            metric=LimitMetric.FILE_STORAGE_BYTES,
            period=LimitPeriod.NONE,
            value=10 * GB,
            source_id="cloudflare-r2-pricing",
        ),
        Limit(
            plan_id="cloudflare-r2-free",
            metric=LimitMetric.BANDWIDTH_BYTES,
            period=LimitPeriod.MONTH,
            value=None,
            source_id="cloudflare-r2-pricing",
        ),
    ),
    unmodeled_facts=(
        UnmodeledFact(
            plan_id="cloudflare-pages-free",
            statement="The Free plan includes 500 builds per month.",
            source_id="cloudflare-pages-limits",
        ),
        UnmodeledFact(
            plan_id="cloudflare-pages-free",
            statement="The Free plan allows one build at a time.",
            source_id="cloudflare-pages-limits",
        ),
        UnmodeledFact(
            plan_id="cloudflare-pages-free",
            statement="Builds time out after 20 minutes.",
            source_id="cloudflare-pages-limits",
        ),
        UnmodeledFact(
            plan_id="cloudflare-pages-free",
            statement="A Free plan site can contain up to 20,000 files.",
            source_id="cloudflare-pages-limits",
        ),
        UnmodeledFact(
            plan_id="cloudflare-pages-free",
            statement="A single Pages asset can be at most 25 MiB.",
            source_id="cloudflare-pages-limits",
        ),
        UnmodeledFact(
            plan_id="cloudflare-pages-free",
            statement="Requests to Pages Functions count toward the Workers plan quota.",
            source_id="cloudflare-pages-limits",
        ),
        UnmodeledFact(
            plan_id="cloudflare-r2-free",
            statement="The free tier includes 1 million Class A operations per month.",
            source_id="cloudflare-r2-pricing",
        ),
        UnmodeledFact(
            plan_id="cloudflare-r2-free",
            statement="The free tier includes 10 million Class B operations per month.",
            source_id="cloudflare-r2-pricing",
        ),
        UnmodeledFact(
            plan_id="cloudflare-r2-free",
            statement=(
                "The free tier applies only to Standard storage, "
                "and usage beyond the included amount is billed."
            ),
            source_id="cloudflare-r2-pricing",
        ),
    ),
)
