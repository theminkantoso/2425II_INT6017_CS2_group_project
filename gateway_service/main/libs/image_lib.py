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


async def publish_rabbitmq_message(
    file_url: str, file_name: str, image_metadata: ImageMetadata, rabbit_connection
):
    """
    Publish a message to RabbitMQ.
    """
    message = MessageSchema(
        type=RabbitMessageType.FILE_UPLOADED,
        file_path=file_url,
        image_hash=image_metadata.hash,
    )
    await rabbit_connection.send_messages(messages=message.model_dump())
    return {"success": True, "filename": file_name, "file_path": file_path}


async def _proceed_to_next_step(
    image_metadata: ImageMetadata, rabbit_connection
) -> None:
    try:
        filename = f"{uuid.uuid4().hex}.{image_metadata.filename.split('.')[-1]}"
        content_type = 'application/octet-stream'

        gmt_time = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        # Upload to GCS
        gcs_service = GCSService()
        file_url = await gcs_service.get_presigned_url(
            destination_blob_name=f"images/{image_metadata.hash}_{filename}_{gmt_time}",
            content_type=content_type,
        )

        # await publish_rabbitmq_message(
        #     file_url=file_url,
        #     file_name=image_metadata.filename,
        #     image_metadata=image_metadata,
        #     rabbit_connection=rabbit_connection,
        # )
        return file_url

    except Exception as e:
        raise InternalServerError(error_message=str(e))


async def handle_cache_miss(
    session: AsyncSession,
    image_metadata: ImageMetadata,
    cache_connection: Redis,
    rabbit_connection,
) -> str | None:
    # Get from database
    cached_image = await image_service.get_cached_image(
        session=session, input_hash=image_metadata.hash
    )
    if cached_image:
        await cache_connection.set(image_metadata.hash, cached_image.pdf_url)
        return cached_image.pdf_url, None
    else:
        # Proceed to the next step
        presigned_url = await _proceed_to_next_step(
            image_metadata=image_metadata,
            rabbit_connection=rabbit_connection,
        )
        return None, presigned_url
