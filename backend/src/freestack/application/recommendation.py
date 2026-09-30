from dataclasses import dataclass

from freestack.domain.caveat import Caveat
from freestack.domain.errors import RelatedEntityNotFoundError
from freestack.domain.limit import Limit
from freestack.domain.needs import derive_needs
from freestack.domain.plan import Plan
from freestack.domain.pricing import PlanPricing
from freestack.domain.provider import Provider
from freestack.domain.recommendation.checks import LimitCheck
from freestack.domain.recommendation.evaluation import (
    RecommendationEvaluation,
    evaluate,
)
from freestack.domain.repositories import CatalogRepository, CaveatCatalog
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.service import Service
from freestack.domain.source import Source


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanDetail:
    """Catalog identity attached to one plan. This does not judge the plan."""

    plan: Plan
    service: Service
    provider: Provider
    pricing: PlanPricing | None
    caveats: tuple[Caveat, ...]
    sources: tuple[Source, ...]

    def __post_init__(self) -> None:
        if self.service.id != self.plan.service_id:
            raise ValueError(
                f"invalid service: {self.service.id!r} does not own plan {self.plan.id!r}"
            )
        if self.provider.id != self.service.provider_id:
            raise ValueError(
                f"invalid provider: {self.provider.id!r} does not own service {self.service.id!r}"
            )
        if self.pricing is not None and self.pricing.plan_id != self.plan.id:
            raise ValueError(
                f"invalid pricing: {self.pricing.plan_id!r} does not match plan {self.plan.id!r}"
            )
        if not isinstance(self.caveats, tuple) or any(
            not isinstance(caveat, Caveat) for caveat in self.caveats
        ):
            raise ValueError(f"invalid caveats: {self.caveats!r}")
        if any(caveat.plan_id != self.plan.id for caveat in self.caveats):
            raise ValueError(f"invalid caveats: {self.caveats!r}")
        if not isinstance(self.sources, tuple) or any(
            not isinstance(source, Source) for source in self.sources
        ):
            raise ValueError(f"invalid sources: {self.sources!r}")
        source_ids = tuple(source.id for source in self.sources)
        if source_ids != tuple(sorted(set(source_ids))):
            raise ValueError(f"invalid sources: {source_ids!r}")
        known_source_ids = set(source_ids)
        if any(caveat.source_id not in known_source_ids for caveat in self.caveats):
            raise ValueError(f"invalid caveats: {self.caveats!r}")
        if self.pricing is not None and self.pricing.source_id not in known_source_ids:
            raise ValueError(
                f"invalid pricing source: {self.pricing.source_id!r} for plan {self.plan.id!r}"
            )


@dataclass(frozen=True, slots=True)
class _SourceUse:
    source_id: str
    kind: str
    plan_id: str
    metric: str | None = None
    period: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RecommendationResult:
    """Engine evaluation plus catalog details for plans that appear in it."""

    evaluation: RecommendationEvaluation
    plans: tuple[PlanDetail, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation, RecommendationEvaluation):
            raise ValueError(f"invalid evaluation: {self.evaluation!r}")
        if not isinstance(self.plans, tuple) or any(
            not isinstance(detail, PlanDetail) for detail in self.plans
        ):
            raise ValueError(f"invalid plans: {self.plans!r}")
        plan_ids = tuple(detail.plan.id for detail in self.plans)
        if plan_ids != tuple(sorted(set(plan_ids))):
            raise ValueError(f"invalid plans: {plan_ids!r}")
        if set(plan_ids) != _evaluation_plan_ids(self.evaluation):
            raise ValueError(f"invalid plans: {plan_ids!r}")


class RecommendationService:
    """Collect catalog data, delegate judgment, and attach catalog identity."""

    def __init__(self, *, catalog: CatalogRepository, caveats: CaveatCatalog) -> None:
        self._catalog = catalog
        self._caveats = caveats

    def recommend(self, requirement: ProjectRequirement) -> RecommendationResult:
        plans = self._catalog.list_all_plans()
        limits_by_plan = {plan.id: self._catalog.list_limits(plan.id) for plan in plans}
        pricing_by_plan: dict[str, PlanPricing] = {}
        for plan in plans:
            pricing = self._catalog.get_plan_pricing(plan.id)
            if pricing is not None:
                pricing_by_plan[plan.id] = pricing

        evaluation = evaluate(
            derive_needs(requirement),
            plans,
            limits_by_plan,
            pricing_by_plan,
        )
        return RecommendationResult(
            evaluation=evaluation,
            plans=self._plan_details(
                evaluation,
                pricing_by_plan,
                {plan.id for plan in plans},
            ),
        )

    def _plan_details(
        self,
        evaluation: RecommendationEvaluation,
        pricing_by_plan: dict[str, PlanPricing],
        loaded_plan_ids: set[str],
    ) -> tuple[PlanDetail, ...]:
        services_by_id: dict[str, Service] = {}
        providers_by_id: dict[str, Provider] = {}
        sources_by_id: dict[str, Source] = {}
        details: list[PlanDetail] = []
        for plan in _appearing_plans(evaluation):
            if plan.id not in loaded_plan_ids:
                raise RelatedEntityNotFoundError(f"plan not found: {plan.id}")
            service = self._service(plan.service_id, services_by_id)
            provider = self._provider(service.provider_id, providers_by_id)
            pricing = pricing_by_plan.get(plan.id)
            caveats = self._caveats_for(plan.id)
            details.append(
                PlanDetail(
                    plan=plan,
                    service=service,
                    provider=provider,
                    pricing=pricing,
                    caveats=caveats,
                    sources=self._sources(plan.id, evaluation, pricing, caveats, sources_by_id),
                )
            )
        return tuple(details)

    def _caveats_for(self, plan_id: str) -> tuple[Caveat, ...]:
        caveats = self._caveats.list_caveats(plan_id)
        for caveat in caveats:
            if caveat.plan_id != plan_id:
                raise RelatedEntityNotFoundError(
                    f"caveat plan_id mismatch: {caveat.plan_id} plan_id={plan_id}"
                )
        return caveats

    def _sources(
        self,
        plan_id: str,
        evaluation: RecommendationEvaluation,
        pricing: PlanPricing | None,
        caveats: tuple[Caveat, ...],
        sources_by_id: dict[str, Source],
    ) -> tuple[Source, ...]:
        uses = _source_uses(plan_id, evaluation, pricing, caveats)
        sources: list[Source] = []
        for use in uses:
            sources.append(self._source(use, sources_by_id))
        return tuple(sources)

    def _source(self, use: _SourceUse, sources_by_id: dict[str, Source]) -> Source:
        cached = sources_by_id.get(use.source_id)
        if cached is not None:
            return cached
        source = self._catalog.get_source(use.source_id)
        if source is None:
            raise RelatedEntityNotFoundError(_missing_source_message(use))
        sources_by_id[use.source_id] = source
        return source

    def _service(self, service_id: str, services_by_id: dict[str, Service]) -> Service:
        cached = services_by_id.get(service_id)
        if cached is not None:
            return cached
        service = self._catalog.get_service(service_id)
        if service is None:
            raise RelatedEntityNotFoundError(f"service not found: {service_id}")
        services_by_id[service_id] = service
        return service

    def _provider(self, provider_id: str, providers_by_id: dict[str, Provider]) -> Provider:
        cached = providers_by_id.get(provider_id)
        if cached is not None:
            return cached
        provider = self._catalog.get_provider(provider_id)
        if provider is None:
            raise RelatedEntityNotFoundError(f"provider not found: {provider_id}")
        providers_by_id[provider_id] = provider
        return provider


def _source_uses(
    plan_id: str,
    evaluation: RecommendationEvaluation,
    pricing: PlanPricing | None,
    caveats: tuple[Caveat, ...],
) -> tuple[_SourceUse, ...]:
    uses: list[_SourceUse] = []
    for role in evaluation.roles:
        for bucket in (role.compatible, role.unknown, role.incompatible):
            for item in bucket:
                if item.plan.id != plan_id:
                    continue
                for check in (*item.quantity_checks, *item.global_quantity_checks):
                    if not isinstance(check, LimitCheck):
                        continue
                    if check.limit is not None:
                        uses.append(_limit_use(plan_id, check.limit))
                    for limit in check.other_period_limits:
                        uses.append(_limit_use(plan_id, limit))
    if pricing is not None:
        uses.append(_SourceUse(pricing.source_id, "pricing", plan_id))
    for caveat in caveats:
        uses.append(_SourceUse(caveat.source_id, "caveat", plan_id))
    ordered = sorted(uses, key=lambda use: (use.source_id, use.kind, use.metric or "", use.period or ""))
    unique: list[_SourceUse] = []
    seen: set[str] = set()
    for use in ordered:
        if use.source_id in seen:
            continue
        seen.add(use.source_id)
        unique.append(use)
    return tuple(unique)


def _limit_use(plan_id: str, limit: Limit) -> _SourceUse:
    return _SourceUse(
        limit.source_id,
        "limit",
        plan_id,
        limit.metric.value,
        limit.period.value,
    )


def _missing_source_message(use: _SourceUse) -> str:
    if use.kind == "limit":
        return (
            f"source not found: {use.source_id} "
            f"plan_id={use.plan_id} metric={use.metric} period={use.period}"
        )
    return f"source not found: {use.source_id} plan_id={use.plan_id}"


def _appearing_plans(evaluation: RecommendationEvaluation) -> tuple[Plan, ...]:
    by_id: dict[str, Plan] = {}
    for role in evaluation.roles:
        for bucket in (role.compatible, role.unknown, role.incompatible):
            for item in bucket:
                by_id.setdefault(item.plan.id, item.plan)
    return tuple(by_id[plan_id] for plan_id in sorted(by_id))


def _evaluation_plan_ids(evaluation: RecommendationEvaluation) -> set[str]:
    return {plan.id for plan in _appearing_plans(evaluation)}
