import ast
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from freestack.api import routes
from freestack.api.dependencies import DEFAULT_MAX_COMBINATIONS, get_stack_composition_service
from freestack.api.routes import recommendations as recommendations_route
from freestack.application.composition import StackCompositionService
from freestack.application.recommendation import RecommendationService
from freestack.domain.errors import RelatedEntityNotFoundError
from freestack.domain.feature import Feature
from freestack.domain.requirement import ProjectRequirement
from freestack.domain.units import GB
from freestack.infrastructure.catalog.caveats import SeedCaveatCatalog
from freestack.infrastructure.catalog.loader import load_catalog
from freestack.infrastructure.catalog.registry import ALL_BUNDLES
from freestack.infrastructure.persistence.in_memory import InMemoryCatalogRepository
from freestack.main import create_app

_COMPOSED_BODY = {
    "features": ["backend-server", "database", "file-uploads"],
    "file_storage_bytes": 500_000_000,
}


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
async def client(app: FastAPI):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest.mark.anyio
async def test_health_stays_available(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_recommendation_returns_the_composition_contract(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/recommendations", json=_COMPOSED_BODY)
    body = response.json()

    assert response.status_code == 200
    assert set(body) == {
        "requirement",
        "roles",
        "composition",
        "unevaluated_features",
        "plans",
        "sources",
    }
    assert body["composition"]["status"] == "composed"
    assert body["composition"]["compatible"]
    assert "render-web-service-free" in body["plans"]
    assert body["roles"]


@pytest.mark.anyio
async def test_requirement_value_error_is_invalid_requirement(client: httpx.AsyncClient) -> None:
    try:
        ProjectRequirement(
            features=frozenset({Feature.DATABASE}),
            file_storage_bytes=1000,
        )
    except ValueError as exc:
        expected = str(exc)
    else:
        raise AssertionError("database without file-uploads must fail in the domain")

    response = await client.post(
        "/api/v1/recommendations",
        json={"features": ["database"], "file_storage_bytes": 1000},
    )
    body = response.json()

    assert response.status_code == 422
    assert body["error"]["code"] == "INVALID_REQUIREMENT"
    assert body["error"]["message"] == expected
    assert "Traceback" not in response.text
    assert "ValueError" not in response.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {"features": ["database"], "monthly_budget_usd_cents": "100"},
        {"features": ["database"], "unknown_field": "unexpected"},
        {"features": ["database", "database"]},
        {"features": ["object-storage"]},
    ],
)
async def test_request_schema_failures_stay_on_the_validation_contract(
    client: httpx.AsyncClient,
    payload: dict[str, object],
) -> None:
    response = await client.post("/api/v1/recommendations", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert body == {
        "error": {
            "code": "REQUEST_VALIDATION_FAILED",
            "message": "Request validation failed.",
        }
    }


@pytest.mark.anyio
async def test_blocked_and_no_roles_are_successful_results(client: httpx.AsyncClient) -> None:
    blocked = await client.post(
        "/api/v1/recommendations",
        json={
            "features": ["authentication", "realtime"],
            "monthly_bandwidth_bytes": 10 * GB,
        },
    )
    no_roles = await client.post("/api/v1/recommendations", json={"features": ["ai-api"]})

    assert blocked.status_code == 200
    assert blocked.json()["composition"]["status"] == "blocked"
    assert no_roles.status_code == 200
    assert no_roles.json()["composition"]["status"] == "no-roles"


@pytest.mark.anyio
async def test_dependency_override_changes_the_combination_limit(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    produced = await client.post("/api/v1/recommendations", json=_COMPOSED_BODY)
    app.dependency_overrides[get_stack_composition_service] = lambda: _seed_service(1)
    limited = await client.post("/api/v1/recommendations", json=_COMPOSED_BODY)

    assert DEFAULT_MAX_COMBINATIONS == 10
    assert produced.status_code == 200
    assert produced.json()["composition"]["status"] == "composed"
    assert limited.status_code == 200
    assert limited.json()["composition"]["status"] == "too-many-combinations"
    assert limited.json()["composition"]["combination_count"] == 2


@pytest.mark.anyio
async def test_compose_value_error_hides_the_internal_message(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    app.dependency_overrides[get_stack_composition_service] = lambda: _FailingService()

    response = await client.post("/api/v1/recommendations", json={"features": ["database"]})

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred."}
    }
    assert "internal failure" not in response.text
    assert "Traceback" not in response.text
    assert "ValueError" not in response.text


@pytest.mark.anyio
async def test_catalog_error_hides_the_repository_message(
    app: FastAPI,
    client: httpx.AsyncClient,
) -> None:
    app.dependency_overrides[get_stack_composition_service] = lambda: _CatalogFailingService()

    response = await client.post("/api/v1/recommendations", json={"features": ["database"]})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "source is missing" not in response.text
    assert "RelatedEntityNotFoundError" not in response.text


def test_router_does_not_assemble_the_catalog() -> None:
    source = Path(recommendations_route.__file__).read_text(encoding="utf-8")
    imported = _imported_modules(source)
    forbidden = (
        "freestack.infrastructure",
        "freestack.domain.repositories",
        "freestack.domain.composition.composer",
        "freestack.domain.composition.budget",
    )
    for name in imported:
        assert all(name != item and not name.startswith(f"{item}.") for item in forbidden)
    assert "InMemoryCatalogRepository" not in source
    assert "RecommendationService" not in source
    assert "compose_stacks" in source
    assert "to_requirement" in source
    assert "to_response" in source

    dependency_source = Path(get_stack_composition_service.__code__.co_filename).read_text(
        encoding="utf-8"
    )
    dependency_imports = _imported_modules(dependency_source)
    assert "freestack.infrastructure.persistence.in_memory" in dependency_imports
    assert "freestack.infrastructure.catalog.loader" in dependency_imports
    route_root = Path(routes.__file__).parent
    for path in route_root.rglob("*.py"):
        assert "freestack.infrastructure" not in path.read_text(encoding="utf-8")


class _FailingService:
    def compose_stacks(self, requirement: object) -> object:
        raise ValueError("internal failure")


class _CatalogFailingService:
    def compose_stacks(self, requirement: object) -> object:
        raise RelatedEntityNotFoundError("source is missing")


def _seed_service(max_combinations: int) -> StackCompositionService:
    repository = InMemoryCatalogRepository()
    load_catalog(repository, ALL_BUNDLES)
    return StackCompositionService(
        recommendations=RecommendationService(catalog=repository, caveats=SeedCaveatCatalog()),
        max_combinations=max_combinations,
    )


def _imported_modules(source: str) -> list[str]:
    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
    return imported
