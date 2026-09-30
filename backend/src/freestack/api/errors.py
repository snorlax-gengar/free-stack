from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from freestack.domain.errors import RepositoryError

INTERNAL_ERROR_MESSAGE = "An internal error occurred."


class APIError(Exception):
    """An HTTP error with a stable code and message."""

    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def invalid_requirement_error(message: str) -> APIError:
    return APIError(status_code=422, code="INVALID_REQUIREMENT", message=message)


def internal_error() -> APIError:
    return APIError(status_code=500, code="INTERNAL_ERROR", message=INTERNAL_ERROR_MESSAGE)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def handle_api_error(_request: Request, exc: APIError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        _request: Request,
        _exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(422, "REQUEST_VALIDATION_FAILED", "Request validation failed.")

    @app.exception_handler(RepositoryError)
    async def handle_repository_error(_request: Request, _exc: RepositoryError) -> JSONResponse:
        return _error_response(500, "INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )
