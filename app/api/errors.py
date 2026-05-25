from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import AppError
from app.logging import get_logger
from app.schemas.common import ErrorResponse

log = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=exc.code, message=exc.message, details=exc.details or None
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                code="validation_error",
                message="Request validation failed",
                details={"errors": exc.errors()},
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code="http_error",
                message=str(exc.detail),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled_exception", path=str(request.url))
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code="internal_error",
                message="Internal server error",
            ).model_dump(),
        )
