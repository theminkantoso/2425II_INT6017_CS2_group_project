import json
import os
import uuid
from pathlib import Path

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from main.enums import RabbitMessageType
from main.misc.exceptions import InternalServerError
from main.schemas.image import ImageMetadata
from main.schemas.message import MessageSchema
from main.services import image_service


async def publish_rabbitmq_message(
    file_path: str, file_name: str, image_metadata: ImageMetadata, rabbit_connection
):
    """
    Publish a message to RabbitMQ.
    """
    message = MessageSchema(
        type=RabbitMessageType.FILE_UPLOADED,
        file_path=file_path,
        image_hash=image_metadata.hash,
    )
    await rabbit_connection.send_messages(messages=json.dumps(message.model_dump()))
    return {"success": True, "filename": file_name, "file_path": file_path}


async def _proceed_to_next_step(
    image_metadata: ImageMetadata, upload_folder: Path, rabbit_connection
) -> None:
    try:
        filename = uuid.uuid4().hex + "." + image_metadata.filename.split(".")[-1]

        # Save the uploaded file to the storage directory
        file_path = os.path.join(upload_folder, filename)
        with open(file_path, "wb") as f:
            f.write(image_metadata.image_bytes)

        await publish_rabbitmq_message(
            file_path=file_path,
            file_name=image_metadata.filename,
            image_metadata=image_metadata,
            rabbit_connection=rabbit_connection,
        )
        return None

    except Exception as e:
        raise InternalServerError(error_message=str(e))


async def handle_cache_miss(
    session: AsyncSession,
    image_metadata: ImageMetadata,
    upload_folder: Path,
    cache_connection: Redis,
    rabbit_connection,
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
            upload_folder=upload_folder,
            rabbit_connection=rabbit_connection,
        )
        return None
