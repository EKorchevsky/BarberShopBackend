import logging
import mimetypes
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from config import settings

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.S3_BUCKET and settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY)


def _client():
    if not _is_configured():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Object storage is not configured on the server"
        )
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    )


def _base_url() -> str:
    if settings.S3_PUBLIC_BASE_URL:
        return settings.S3_PUBLIC_BASE_URL.rstrip("/")
    if settings.S3_ENDPOINT_URL:
        return f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET}"
    return f"https://{settings.S3_BUCKET}.s3.amazonaws.com"


async def upload_file(file: UploadFile, prefix: str) -> str:
    client = _client()
    ext = Path(file.filename or "").suffix
    key = f"{prefix.strip('/')}/{uuid.uuid4().hex}{ext}"
    content = await file.read()
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"

    def _put():
        client.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=content, ContentType=content_type)

    try:
        await run_in_threadpool(_put)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to upload file: {exc}")

    return f"{_base_url()}/{key}"


async def delete_file(url: str) -> None:
    if not _is_configured():
        return

    prefix = _base_url() + "/"
    if not url.startswith(prefix):
        return
    key = url[len(prefix):]

    client = _client()
    try:
        await run_in_threadpool(lambda: client.delete_object(Bucket=settings.S3_BUCKET, Key=key))
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Failed to delete %s from storage: %s", key, exc)
