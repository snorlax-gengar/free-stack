from fastapi import APIRouter, Depends

from freestack.api.dependencies import get_stack_composition_service
from freestack.api.errors import internal_error, invalid_requirement_error
from freestack.api.mappers import to_requirement, to_response
from freestack.api.schemas import RecommendationRequest, RecommendationResponse
from freestack.application.composition import StackCompositionService
from freestack.domain.errors import RepositoryError

router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
def create_recommendation(
    request: RecommendationRequest,
    service: StackCompositionService = Depends(get_stack_composition_service),
) -> RecommendationResponse:
    try:
        requirement = to_requirement(request)
    except ValueError as exc:
        raise invalid_requirement_error(str(exc)) from exc

    try:
        result = service.compose_stacks(requirement)
    except ValueError:
        raise internal_error() from None
    except RepositoryError:
        raise internal_error() from None
    return to_response(result)
