from freestack.application.recommendation import RecommendationService
from freestack.domain.caveat import Caveat
from freestack.domain.feature import Feature
from freestack.domain.needs import derive_needs
from freestack.domain.recommendation.evaluation import evaluate
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.units import GB, MB
from freestack.infrastructure.catalog.caveats import SeedCaveatCatalog
from freestack.infrastructure.catalog.loader import load_catalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository


def _seeded_repository() -> InMemoryCatalogRepository:
    repository = InMemoryCatalogRepository()
    load_catalog(repository, ALL_BUNDLES)
    return repository


def _direct(repository: InMemoryCatalogRepository, requirement: ProjectRequirement):
    plans = repository.list_all_plans()
    limits_by_plan = {plan.id: repository.list_limits(plan.id) for plan in plans}
    pricing_by_plan = {}
    for plan in plans:
        pricing = repository.get_plan_pricing(plan.id)
        if pricing is not None:
            pricing_by_plan[plan.id] = pricing
    return evaluate(derive_needs(requirement), plans, limits_by_plan, pricing_by_plan)


def test_seed_catalog_attaches_provider_and_service_without_changing_evaluation() -> None:
    repository = _seeded_repository()
    requirement = ProjectRequirement(
        features=frozenset(
            {
                Feature.BACKEND_SERVER,
                Feature.DATABASE,
                Feature.FILE_UPLOADS,
            }
        ),
        database_size_bytes=100 * MB,
        file_storage_bytes=100 * MB,
        monthly_bandwidth_bytes=1 * GB,
        monthly_budget_usd_cents=0,
    )

    result = RecommendationService(
        catalog=repository,
        caveats=SeedCaveatCatalog(),
    ).recommend(requirement)

    assert result.evaluation == _direct(repository, requirement)
    assert tuple(detail.plan.id for detail in result.plans) == (
        "cloudflare-r2-free",
        "render-web-service-free",
        "supabase-platform-free",
    )
    by_role = {role.role: role for role in result.evaluation.roles}
    assert "render-web-service-free" in {
        item.plan.id for item in by_role[Feature.BACKEND_SERVER].unknown
    }
    assert "supabase-platform-free" in {
        item.plan.id for item in by_role[Feature.DATABASE].unknown
    }
    assert {
        item.plan.id for item in by_role[Feature.FILE_UPLOADS].unknown
    } == {"cloudflare-r2-free", "supabase-platform-free"}
    assert all(detail.pricing is None for detail in result.plans)

    details = {detail.plan.id: detail for detail in result.plans}
    assert details["cloudflare-r2-free"].service.id == "cloudflare-r2"
    assert details["cloudflare-r2-free"].provider.id == "cloudflare"
    assert details["render-web-service-free"].service.id == "render-web-service"
    assert details["render-web-service-free"].provider.id == "render"
    assert details["supabase-platform-free"].service.id == "supabase-platform"
    assert details["supabase-platform-free"].provider.id == "supabase"
    assert sum(detail.plan.id == "supabase-platform-free" for detail in result.plans) == 1
    assert tuple(caveat.statement for caveat in details["cloudflare-r2-free"].caveats) == (
        "The free tier includes 1 million Class A operations per month.",
        "The free tier includes 10 million Class B operations per month.",
        "The free tier applies only to Standard storage, "
        "and usage beyond the included amount is billed.",
    )
    assert tuple(source.id for source in details["cloudflare-r2-free"].sources) == (
        "cloudflare-r2-pricing",
    )
    assert tuple(caveat.statement for caveat in details["render-web-service-free"].caveats) == (
        "Each workspace receives 750 Free instance hours per calendar month.",
        "When Free instance hours are exhausted, "
        "Free web services are suspended until the next month.",
        "A Free web service spins down after 15 minutes without inbound traffic.",
        "Spinning a Free web service back up takes about one minute.",
        "Free web services have an ephemeral filesystem.",
        "A persistent disk cannot be attached to a Free web service.",
        "A Free web service cannot scale beyond a single instance.",
        "Render may restart a Free web service at any time.",
        "Render says not to use Free instances for production applications.",
        "The Free web service compute plan provides 0.1 CPU.",
        "The Free web service compute plan provides 512 MB of RAM.",
    )
    assert tuple(source.id for source in details["render-web-service-free"].sources) == (
        "render-compute-plans",
        "render-free",
    )
    assert tuple(caveat.statement for caveat in details["supabase-platform-free"].caveats) == (
        "The Free plan includes two projects.",
        "The 500 MB database size quota applies per project.",
        "The 1 GB storage quota applies per organization.",
        "The 5 GB egress quota applies per organization.",
        "The Free plan includes 50,000 monthly active users.",
        "The Free plan includes 500,000 Edge Function invocations.",
        "The Free plan includes 2,000,000 Realtime messages.",
        "The Free plan includes 200 Realtime peak connections.",
    )
    assert tuple(source.id for source in details["supabase-platform-free"].sources) == (
        "supabase-billing",
    )
    assert all(caveat.plan_id == detail.plan.id for detail in result.plans for caveat in detail.caveats)
    assert "cloudflare-pages-limits" not in {
        source.id for detail in result.plans for source in detail.sources
    }
    assert all(isinstance(caveat, Caveat) for detail in result.plans for caveat in detail.caveats)
