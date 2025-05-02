# worker.py
import asyncio
import json
import traceback
from functools import partial
from io import BytesIO

import aio_pika
from PIL import ImageFile, Image
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from _config import config
from models.retry_job import RetryJobModel
from models.text_cache import TextCacheModel
from schemas.message import MessageSchema
from models.image_cache import ImageCacheModel
from misc.utils.encoder import encode_text
from services import ocr_service, gcp_service

import logging

logging.basicConfig(level=logging.INFO)


# Initialize the async engine and session
async_engine = create_async_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Dependency to get the session
async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session


PHASE = 1


async def check_if_text_cached(
    input_text: str, redis: Redis, image_hash: str, session: AsyncSession
) -> tuple[str | None, str]:
    encoded_text = encode_text(input_text=input_text)
    # Check if the text is already cached in Redis
    cached_text = await redis.get(encoded_text)
    if cached_text:
        logging.info(f"Text is already cached in Redis: {cached_text}")
        await handle_add_new_cache(
            image_hash=image_hash,
            pdf_url=cached_text.pdf_url,
            redis=redis,
            session=session,
        )
        return cached_text, encoded_text
    else:
        cached_text_record = await get_cached_image(
            session=session, input_text=encoded_text
        )
        if cached_text_record:
            await redis.set(encoded_text, cached_text_record.pdf_url)
            await handle_add_new_cache(
                image_hash=image_hash,
                pdf_url=cached_text_record.pdf_url,
                redis=redis,
                session=session,
            )
            return cached_text_record.pdf_url, encoded_text

    return None, encoded_text


async def get_cached_image(
    session: AsyncSession, input_text: str
) -> TextCacheModel | None:
    stmt = select(TextCacheModel).where(TextCacheModel.text_encode == input_text)
    stmt = stmt.where(TextCacheModel.is_deleted.is_(False))
    result = await session.execute(stmt)
    return result.scalars().first()


async def handle_add_new_cache(
    image_hash: str, pdf_url: str, redis: Redis, session: AsyncSession
):
    await redis.set(image_hash, pdf_url)
    session.add(ImageCacheModel(**{"hash_id": image_hash, "pdf_url": pdf_url}))
    await session.commit()


async def create_retry_job(session: AsyncSession, data: dict) -> RetryJobModel:
    job = RetryJobModel(**data)
    session.add(job)
    await session.commit()
    return job


async def publish_message(message: str):
    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=config.RABBITMQ_QUEUE_OCR_TO_TRANSLATE,
        )
        logging.info(f"OCR: Published message {message} to RabbitMQ")


async def get_failed_jobs(
    session: AsyncSession, job_ids: list[int]
) -> list[RetryJobModel]:
    stmt = (
        select(RetryJobModel)
        .where(RetryJobModel.id.in_(job_ids))
        .where(RetryJobModel.step == PHASE)
    )
    stmt = stmt.where(RetryJobModel.is_deleted.is_(False))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _get_image(file_url: str, is_from_gcs: bool) -> ImageFile.ImageFile:
    if is_from_gcs:
        image_byte = await gcp_service.download_image_from_gcs_to_memory(
            public_url=file_url
        )
        image = Image.open(BytesIO(image_byte))
    else:
        # Load the image from the specified path
        image = Image.open(file_url)
    return image


async def handle_retry_flow(session: AsyncSession, redis: Redis, job_ids: list[int]):
    NEXT_PHASE = 2
    failed_jobs = await get_failed_jobs(session=session, job_ids=job_ids)
    if failed_jobs:
        for job in failed_jobs:
            try:
                image = await _get_image(
                    file_url=job.file_url, is_from_gcs=job.is_file_from_gcs
                )
                text = await ocr_service.image_to_text(image=image)

                cached_pdf_url, encoded_text = await check_if_text_cached(
                    input_text=text,
                    redis=redis,
                    image_hash=job.image_hash,
                    session=session,
                )
                if cached_pdf_url:
                    # TODO: Handle cached scenario
                    job.is_deleted = True
                    logging.info(f"Text is already cached in Redis: {cached_pdf_url}")

                else:
                    # publish the result to RabbitMQ
                    # data = MessageSchema(file_url=job.file_url, image_hash=job.image_hash, encoded_text=text, text_to_translate=text)
                    # await publish_message(message=json.dumps(data.model_dump()))
                    job.text_to_translate = text
                    job.encoded_text = encoded_text
                    job.step = NEXT_PHASE

            except Exception as e:
                job.job_metadata = json.dumps(
                    {"error": str(e), "trace": traceback.format_exc()}
                )

    await session.commit()


async def handle_normal_flow(session: AsyncSession, data: dict, redis: Redis):
    data = MessageSchema(**data)
    logging.info(
        f"OCR: Received message from RabbitMQ, processing content {str(data.model_dump())}"
    )
    try:
        image = await _get_image(
            file_url=data.file_url, is_from_gcs=data.is_file_from_gcs
        )
        text = await ocr_service.image_to_text(image=image)

        cached_pdf_url, encoded_text = await check_if_text_cached(
            input_text=text, redis=redis, image_hash=data.image_hash, session=session
        )
        if cached_pdf_url:
            # TODO: Handle cached scenario
            logging.info(f"Text is already cached in Redis: {cached_pdf_url}")

        else:
            # publish the result to RabbitMQ
            data.encoded_text = encoded_text
            data.text_to_translate = text
            await publish_message(message=json.dumps(data.model_dump()))
    except Exception as e:
        await create_retry_job(
            session=session,
            data={
                "step": PHASE,
                "file_url": data.file_url,
                "image_hash": data.image_hash,
                "is_file_from_gcs": data.is_file_from_gcs,
                "job_metadata": json.dumps(
                    {"error": str(e), "trace": traceback.format_exc()}
                ),
            },
        )


async def handle_message(message: aio_pika.IncomingMessage, redis: Redis):
    async with message.process():
        data = message.body.decode()
        data = json.loads(data)
        async for session in get_db_session():
            if not (job_ids := data.get("job_ids")):
                await handle_normal_flow(data=data, redis=redis, session=session)
            else:
                await handle_retry_flow(redis=redis, session=session, job_ids=job_ids)


async def main():
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    channel = await connection.channel()
    queue = await channel.declare_queue(
        config.RABBITMQ_QUEUE_GATEWAY_TO_OCR, durable=True
    )

    handler = partial(handle_message, redis=redis)
    await queue.consume(handler)

    await asyncio.Future()  # keep the script alive


if __name__ == "__main__":

    asyncio.run(main())
