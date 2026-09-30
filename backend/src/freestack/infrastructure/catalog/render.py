from datetime import date

from freestack.domain.capability import CapabilityKey
from freestack.domain.plan import Plan
from freestack.domain.provider import Provider
from freestack.domain.service import Service
from freestack.domain.source import Source
from freestack.infrastructure.catalog.bundle import CatalogBundle, UnmodeledFact

CHECKED_AT = date(2026, 9, 30)

RENDER = CatalogBundle(
    provider=Provider(
        id="render",
        name="Render",
        slug="render",
        description="Application hosting platform.",
    ),
    services=(
        Service(
            id="render-web-service",
            provider_id="render",
            name="Web Service",
            slug="web-service",
            description="Hosted web application compute.",
        ),
    ),
    plans=(
        Plan(
            id="render-web-service-free",
            service_id="render-web-service",
            name="Free",
            slug="free",
            description="Free Render web service instance.",
            capabilities=frozenset({CapabilityKey.SERVER_COMPUTE}),
        ),
    ),
    sources=(
        Source(
            id="render-free",
            url="https://render.com/docs/free",
            checked_at=CHECKED_AT,
            notes="Official Render Free instance documentation.",
        ),
        Source(
            id="render-compute-plans",
            url="https://render.com/docs/compute-plans",
            checked_at=CHECKED_AT,
            notes="Official Render compute plan specifications.",
        ),
    ),
    limits=(),
    unmodeled_facts=(
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="Each workspace receives 750 Free instance hours per calendar month.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement=(
                "When Free instance hours are exhausted, "
                "Free web services are suspended until the next month."
            ),
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="A Free web service spins down after 15 minutes without inbound traffic.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="Spinning a Free web service back up takes about one minute.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="Free web services have an ephemeral filesystem.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="A persistent disk cannot be attached to a Free web service.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="A Free web service cannot scale beyond a single instance.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="Render may restart a Free web service at any time.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="Render says not to use Free instances for production applications.",
            source_id="render-free",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="The Free web service compute plan provides 0.1 CPU.",
            source_id="render-compute-plans",
        ),
        UnmodeledFact(
            plan_id="render-web-service-free",
            statement="The Free web service compute plan provides 512 MB of RAM.",
            source_id="render-compute-plans",
        ),
    ),
)
