from datetime import date

from freestack.domain.capability import CapabilityKey
from freestack.domain.limit import Limit, LimitMetric, LimitPeriod
from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.service import Service
from freestack.domain.source import Source
from freestack.domain.units import GB, MB
from freestack.infrastructure.catalog.bundle import CatalogBundle, UnmodeledFact

CHECKED_AT = date(2026, 9, 30)

SUPABASE = CatalogBundle(
    provider=Provider(
        id="supabase",
        name="Supabase",
        slug="supabase",
        description="Hosted Postgres and application backend platform.",
    ),
    services=(
        Service(
            id="supabase-platform",
            provider_id="supabase",
            name="Platform",
            slug="platform",
            description="Database, auth, storage, and related backend services.",
        ),
    ),
    plans=(
        Plan(
            id="supabase-platform-free",
            service_id="supabase-platform",
            name="Free",
            slug="free",
            description="Free Supabase plan.",
            capabilities=frozenset(
                {
                    CapabilityKey.DATABASE,
                    CapabilityKey.AUTHENTICATION,
                    CapabilityKey.FILE_STORAGE,
                    CapabilityKey.REALTIME,
                    CapabilityKey.SERVERLESS_FUNCTIONS,
                }
            ),
        ),
    ),
    sources=(
        Source(
            id="supabase-billing",
            url="https://supabase.com/docs/guides/platform/billing-on-supabase",
            checked_at=CHECKED_AT,
            notes="Official Supabase billing documentation.",
        ),
    ),
    limits=(
        Limit(
            plan_id="supabase-platform-free",
            metric=LimitMetric.DATABASE_SIZE_BYTES,
            period=LimitPeriod.NONE,
            value=500 * MB,
            source_id="supabase-billing",
        ),
        Limit(
            plan_id="supabase-platform-free",
            metric=LimitMetric.FILE_STORAGE_BYTES,
            period=LimitPeriod.NONE,
            value=1 * GB,
            source_id="supabase-billing",
        ),
        Limit(
            plan_id="supabase-platform-free",
            metric=LimitMetric.BANDWIDTH_BYTES,
            period=LimitPeriod.MONTH,
            value=5 * GB,
            source_id="supabase-billing",
        ),
    ),
    unmodeled_facts=(
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The Free plan includes two projects.",
            source_id="supabase-billing",
        ),
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The 500 MB database size quota applies per project.",
            source_id="supabase-billing",
        ),
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The 1 GB storage quota applies per organization.",
            source_id="supabase-billing",
        ),
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The 5 GB egress quota applies per organization.",
            source_id="supabase-billing",
        ),
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The Free plan includes 50,000 monthly active users.",
            source_id="supabase-billing",
        ),
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The Free plan includes 500,000 Edge Function invocations.",
            source_id="supabase-billing",
        ),
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The Free plan includes 2,000,000 Realtime messages.",
            source_id="supabase-billing",
        ),
        UnmodeledFact(
            plan_id="supabase-platform-free",
            statement="The Free plan includes 200 Realtime peak connections.",
            source_id="supabase-billing",
        ),
    ),
)
