import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from main.enums import RabbitMessageType
from main.misc.exceptions import InternalServerError
from main.schemas.image import ImageMetadata
from main.schemas.message import MessageSchema
from main.services import image_service

from main.services.gcs_service import GCSService
from datetime import datetime, timezone


import os
from pathlib import Path


async def publish_rabbitmq_message(
    file_url: str,
    image_metadata: ImageMetadata,
    rabbit_connection,
    file_name: str | None = None,
):
    """
    Publish a message to RabbitMQ.
    """
    message = MessageSchema(
        type=RabbitMessageType.FILE_UPLOADED,
        file_url=file_url,
        image_hash=image_metadata.hash,
        is_file_from_gcs=True if file_name is None else False,
    )
    await rabbit_connection.send_messages(messages=message.model_dump())
    return {"success": True, "filename": file_name, "file_url": file_url}


async def _handle_proceed_from_local_storage(
    image_metadata: ImageMetadata, upload_folder: Path, rabbit_connection
) -> None:
    try:
        filename = uuid.uuid4().hex + "." + image_metadata.filename.split(".")[-1]

        # Save the uploaded file to the storage directory
        file_path = os.path.join(upload_folder, filename)
        with open(file_path, "wb") as f:
            f.write(image_metadata.image_bytes)

        await publish_rabbitmq_message(
            file_url=file_path,
            file_name=image_metadata.filename,
            image_metadata=image_metadata,
            rabbit_connection=rabbit_connection,
        )
        return None

    except Exception as e:
        raise InternalServerError(error_message=str(e))


async def _handle_proceed_from_gcs(
    image_metadata: ImageMetadata, rabbit_connection
) -> None:
    try:
        await publish_rabbitmq_message(
            file_url=image_metadata.file_url,
            image_metadata=image_metadata,
            rabbit_connection=rabbit_connection,
        )
        return None

    except Exception as e:
        raise InternalServerError(error_message=str(e))


async def _proceed_to_next_step(
    image_metadata: ImageMetadata,
    rabbit_connection,
    is_file_from_gcs: bool = False,
    upload_folder: Path | None = None,
) -> None:
    if not is_file_from_gcs:
        await _handle_proceed_from_local_storage(
            image_metadata=image_metadata,
            upload_folder=upload_folder,
            rabbit_connection=rabbit_connection,
        )
    else:
        await _handle_proceed_from_gcs(
            image_metadata=image_metadata, rabbit_connection=rabbit_connection
        )


async def handle_cache_miss(
    session: AsyncSession,
    image_metadata: ImageMetadata,
    cache_connection: Redis,
    rabbit_connection,
    upload_folder: Path | None = None,
) -> str | None:
    # Get from database
    cached_image = await image_service.get_cached_image(
        session=session, input_hash=image_metadata.hash
    )
    if cached_image:
        await cache_connection.set(image_metadata.hash, cached_image.pdf_url)
        return cached_image.pdf_url
    else:
        # Proceed to the next step
        await _proceed_to_next_step(
            image_metadata=image_metadata,
            is_file_from_gcs=True if not upload_folder else False,
            rabbit_connection=rabbit_connection,
        )
        return None


async def check_cache_from_db(
    session: AsyncSession,
    image_metadata: ImageMetadata,
    cache_connection: Redis,
) -> str | None:
    # Get from database
    cached_image = await image_service.get_cached_image(
        session=session, input_hash=image_metadata.hash
    )
    if cached_image:
        await cache_connection.set(image_metadata.hash, cached_image.pdf_url)
        return cached_image.pdf_url
    return None


async def generate_presigned_url(file_name: str) -> str:
    try:
        filename = f"{uuid.uuid4().hex}.{file_name.split('.')[-1]}"
        content_type = "application/octet-stream"

        gmt_time = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        # Upload to GCS
        gcs_service = GCSService()
        file_url = await gcs_service.get_presigned_url(
            destination_blob_name=f"images/{gmt_time}_{filename}",
            content_type=content_type,
        )
        return file_url

    except Exception as e:
        raise InternalServerError(error_message=str(e))
