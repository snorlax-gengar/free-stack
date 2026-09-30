import httpx
import pytest
from fastapi import FastAPI

from freestack.api.dependencies import get_stack_composition_service
from freestack.api.mappers import to_requirement, to_response
from freestack.api.schemas import RecommendationRequest
from freestack.main import create_app

_COMPOSED_BODY = {
    "features": ["backend-server", "database", "file-uploads"],
    "file_storage_bytes": 500_000_000,
}
_BUDGET_BODY = {**_COMPOSED_BODY, "monthly_budget_usd_cents": 0}
_PLAN_FIELDS = {"plan", "service", "provider", "pricing", "caveats", "sources"}
_CAVEAT_FIELDS = {"plan_id", "statement", "source_id"}
_SOURCE_FIELDS = {"id", "url", "checked_at", "notes"}
_BUDGET_FIELDS = {
    "budget_usd_cents",
    "priced_plan_ids",
    "unpriced_plan_ids",
    "known_total_usd_cents",
    "reason",
    "outcome",
}


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
async def client(app: FastAPI):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


def test_openapi_publishes_the_recommendation_contract(app: FastAPI) -> None:
    spec = app.openapi()
    operation = spec["paths"]["/api/v1/recommendations"]["post"]
    schemas = spec["components"]["schemas"]
    request = schemas["RecommendationRequest"]
    response = schemas["RecommendationResponse"]
    error = schemas["ErrorResponse"]

    assert set(spec["paths"]) == {"/health", "/api/v1/recommendations"}
    assert set(spec["paths"]["/api/v1/recommendations"]) == {"post"}
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/RecommendationRequest"
    )
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/RecommendationResponse"
    )
    assert operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )
    assert operation["responses"]["500"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/ErrorResponse"
    )
    assert "HTTPValidationError" not in operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]

    assert request["additionalProperties"] is False
    assert request["required"] == ["features"]
    assert set(request["properties"]) == {
        "features",
        "file_storage_bytes",
        "database_size_bytes",
        "monthly_bandwidth_bytes",
        "monthly_budget_usd_cents",
    }
    for name in (
        "file_storage_bytes",
        "database_size_bytes",
        "monthly_bandwidth_bytes",
        "monthly_budget_usd_cents",
    ):
        variants = request["properties"][name]["anyOf"]
        assert {"type": "integer"} in variants
        assert {"type": "null"} in variants
    assert "database" in schemas["Feature"]["enum"]
    assert "file-uploads" in schemas["Feature"]["enum"]

    assert response["additionalProperties"] is False
    assert set(response["required"]) == {
        "requirement",
        "roles",
        "composition",
        "unevaluated_features",
        "plans",
        "sources",
    }
    assert set(schemas["CaveatResponse"]["required"]) == _CAVEAT_FIELDS
    assert set(schemas["SourceResponse"]["required"]) == _SOURCE_FIELDS
    assert set(schemas["CheckResponse"]["required"]) == {"reason_code", "outcome"}
    assert set(schemas["StackBudgetCheckResponse"]["required"]) == _BUDGET_FIELDS
    assert "id" not in schemas["StackResponse"]["properties"]
    assert "kind" not in schemas["CheckResponse"]["properties"]
    assert "required" not in schemas["QuantityCheckResponse"]["properties"]
    assert set(error["required"]) == {"error"}
    assert set(schemas["ErrorObject"]["required"]) == {"code", "message"}


@pytest.mark.anyio
async def test_openapi_document_and_docs_page_are_available(client: httpx.AsyncClient) -> None:
    spec = await client.get("/openapi.json")
    docs = await client.get("/docs")

    assert spec.status_code == 200
    assert spec.headers["content-type"].startswith("application/json")
    assert "post" in spec.json()["paths"]["/api/v1/recommendations"]
    assert docs.status_code == 200
    assert docs.headers["content-type"].startswith("text/html")


@pytest.mark.anyio
async def test_successful_response_matches_the_application_result(client: httpx.AsyncClient) -> None:
    first = await client.post("/api/v1/recommendations", json=_COMPOSED_BODY)
    second = await client.post("/api/v1/recommendations", json=_COMPOSED_BODY)
    body = first.json()
    stack = body["composition"]["compatible"][0]

    assert first.status_code == 200
    assert first.headers["content-type"].startswith("application/json")
    assert body == _application_json(_COMPOSED_BODY)
    assert second.json()["composition"]["compatible"][0]["key"] == stack["key"]
    assert stack["key"]
    assert [item["plan_id"] for item in stack["assignments"]] != stack["plan_ids"]
    assert stack["budget_check"] is None
    for plan_id, detail in body["plans"].items():
        assert set(detail) == _PLAN_FIELDS
        assert detail["plan"]["id"] == plan_id
        assert detail["pricing"] is None
        for caveat in detail["caveats"]:
            assert set(caveat) == _CAVEAT_FIELDS
        for source in detail["sources"]:
            assert set(source) == _SOURCE_FIELDS
            assert source["id"] in body["sources"]
            assert set(body["sources"][source["id"]]) == _SOURCE_FIELDS


@pytest.mark.anyio
async def test_budgeted_response_keeps_the_recorded_budget_check(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/v1/recommendations", json=_BUDGET_BODY)
    body = response.json()
    check = body["composition"]["unknown"][0]["budget_check"]

    assert response.status_code == 200
    assert body == _application_json(_BUDGET_BODY)
    assert set(check) == _BUDGET_FIELDS
    assert check["budget_usd_cents"] == 0
    assert check["reason"] == "pricing-not-found"
    assert isinstance(check["known_total_usd_cents"], int)
    assert all(detail["pricing"] is None for detail in body["plans"].values())


@pytest.mark.anyio
async def test_recommendation_route_rejects_other_methods_and_paths(client: httpx.AsyncClient) -> None:
    wrong_method = await client.get("/api/v1/recommendations")
    missing = await client.post("/recommendations", json=_COMPOSED_BODY)
    missing_prefix = await client.post("/api/recommendations", json=_COMPOSED_BODY)

    assert wrong_method.status_code == 405
    assert "composition" not in wrong_method.json()
    assert missing.status_code == 404
    assert missing_prefix.status_code == 404


def _application_json(payload: dict[str, object]) -> dict[str, object]:
    requirement = to_requirement(RecommendationRequest.model_validate(payload))
    result = get_stack_composition_service().compose_stacks(requirement)
    return to_response(result).model_dump(mode="json")
