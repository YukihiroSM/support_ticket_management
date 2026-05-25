from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router
from app.config import get_settings
from app.database import engine
from app.logging import configure_logging, get_logger

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    log = get_logger(__name__)
    settings = get_settings()
    log.info("app_starting", env=settings.app_env, version=settings.api_version)
    try:
        yield
    finally:
        await engine.dispose()
        log.info("app_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app


app = create_app()
