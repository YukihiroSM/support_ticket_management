from contextlib import asynccontextmanager
from typing import Any

import aioboto3

from app.config import Settings


@asynccontextmanager
async def sqs_client(settings: Settings):
    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_default_region,
    )
    kwargs: dict[str, Any] = {}
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    async with session.client("sqs", **kwargs) as client:
        yield client
