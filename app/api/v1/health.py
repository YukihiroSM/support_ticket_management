from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    return {"status": "ok"}
