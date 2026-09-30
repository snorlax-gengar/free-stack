import pytest
from pydantic import ValidationError

from freestack.api.mappers import to_requirement
from freestack.api.schemas import RecommendationRequest
from freestack.domain.feature import Feature


def test_minimum_request_is_valid() -> None:
    dto = RecommendationRequest.model_validate({"features": ["database"]})

    assert dto.features == [Feature.DATABASE]
    assert dto.file_storage_bytes is None
    assert dto.database_size_bytes is None
    assert dto.monthly_bandwidth_bytes is None
    assert dto.monthly_budget_usd_cents is None


def test_request_accepts_every_optional_field() -> None:
    dto = RecommendationRequest.model_validate(
        {
            "features": ["backend-server", "database", "file-uploads"],
            "file_storage_bytes": 500_000_000,
            "database_size_bytes": 1,
            "monthly_bandwidth_bytes": 2,
            "monthly_budget_usd_cents": 0,
        }
    )

    requirement = to_requirement(dto)

    assert requirement.features == frozenset(
        {Feature.BACKEND_SERVER, Feature.DATABASE, Feature.FILE_UPLOADS}
    )
    assert requirement.file_storage_bytes == 500_000_000
    assert requirement.database_size_bytes == 1
    assert requirement.monthly_bandwidth_bytes == 2
    assert requirement.monthly_budget_usd_cents == 0


def test_request_accepts_null_optional_fields() -> None:
    dto = RecommendationRequest.model_validate(
        {
            "features": ["file-uploads"],
            "file_storage_bytes": None,
            "database_size_bytes": None,
            "monthly_bandwidth_bytes": None,
            "monthly_budget_usd_cents": None,
        }
    )

    assert dto.file_storage_bytes is None
    assert dto.monthly_budget_usd_cents is None


def test_empty_feature_list_reaches_domain_validation() -> None:
    dto = RecommendationRequest.model_validate({"features": []})

    with pytest.raises(ValueError, match=r"invalid features:"):
        to_requirement(dto)


def test_negative_quantity_reaches_domain_validation() -> None:
    dto = RecommendationRequest.model_validate(
        {"features": ["file-uploads"], "file_storage_bytes": -1}
    )

    with pytest.raises(ValueError, match=r"invalid file_storage_bytes:"):
        to_requirement(dto)


def test_request_rejects_missing_features() -> None:
    with pytest.raises(ValidationError):
        RecommendationRequest.model_validate({})


def test_request_rejects_an_unknown_feature() -> None:
    with pytest.raises(ValidationError):
        RecommendationRequest.model_validate({"features": ["object-storage"]})


def test_request_rejects_duplicate_features() -> None:
    with pytest.raises(ValidationError, match="duplicate features"):
        RecommendationRequest.model_validate({"features": ["database", "database"]})


def test_request_rejects_an_unknown_field() -> None:
    with pytest.raises(ValidationError):
        RecommendationRequest.model_validate({"features": ["database"], "unknown_field": 123})


@pytest.mark.parametrize(
    "value",
    [True, False, 1.5, "10"],
)
def test_request_rejects_non_strict_integers(value: object) -> None:
    with pytest.raises(ValidationError):
        RecommendationRequest.model_validate(
            {"features": ["database"], "monthly_budget_usd_cents": value}
        )
