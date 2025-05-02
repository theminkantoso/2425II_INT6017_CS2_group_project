# worker.py
import asyncio
import json
import traceback
from functools import partial
from pathlib import Path

import aio_pika
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from _config import config
from schemas.message import MessageSchema
from services import pdf_service
from models.text_cache import TextCacheModel
from models.image_cache import ImageCacheModel

import logging
from models.retry_job import RetryJobModel

logging.basicConfig(level=logging.INFO)

# Initialize the async engine and session
async_engine = create_async_engine(config.SQLALCHEMY_DATABASE_URI, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session


PHASE = 3


async def save_to_cache(encoded_text: str, image_hash: str, pdf_url: str, redis: Redis):
    async for session in get_db_session():
        # Here you would save the PDF URL to your database
        session.add(TextCacheModel(**{"pdf_url": pdf_url, "text_encode": encoded_text}))
        session.add(ImageCacheModel(**{"pdf_url": pdf_url, "hash_id": image_hash}))
        await session.commit()

        await redis.set(encoded_text, pdf_url)
        await redis.set(image_hash, pdf_url)


async def create_retry_job(session: AsyncSession, data: dict) -> RetryJobModel:
    job = RetryJobModel(**data)
    session.add(job)
    await session.commit()
    return job


async def handle_normal_flow(session: AsyncSession, data: dict, redis: Redis):
    data = MessageSchema(**data)
    logging.info(f"PDF: Received message from RabbitMQ, processing content {data}")
    # your business logic here, use shared functions or DB access
    translated_text = data.translated_text
    image_file_url = Path(data.file_url)
    file_uuid = image_file_url.with_suffix("")

    try:
        pdf_url = await pdf_service.text_to_pdf(
            text=translated_text, output_filename=str(f"{file_uuid}.pdf")
        )

        await save_to_cache(
            image_hash=data.image_hash,
            encoded_text=data.encoded_text,
            pdf_url=pdf_url,
            redis=redis,
        )
    except Exception as e:
        await create_retry_job(
            session=session,
            data={
                "step": PHASE,
                "file_url": data.file_url,
                "image_hash": data.image_hash,
                "text_to_translate": data.text_to_translate,
                "encoded_text": data.encoded_text,
                "translated_text": translated_text,
                "job_metadata": json.dumps(
                    {"error": str(e), "trace": traceback.format_exc()}
                ),
            },
        )


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


async def handle_retry_flow(redis: Redis, session: AsyncSession, job_ids: list[int]):
    failed_jobs = await get_failed_jobs(session=session, job_ids=job_ids)
    if failed_jobs:
        for job in failed_jobs:
            try:
                translated_text = job.translated_text
                image_file_url = Path(job.file_url)
                file_uuid = image_file_url.with_suffix("")

                pdf_url = await pdf_service.text_to_pdf(
                    text=translated_text, output_filename=str(f"{file_uuid}.pdf")
                )

                await save_to_cache(
                    image_hash=job.image_hash,
                    encoded_text=job.encoded_text,
                    pdf_url=pdf_url,
                    redis=redis,
                )

                # Remove the job from the retry queue, since all the flow has been completed
                job.is_deleted = True

            except Exception as e:
                job.job_metadata = json.dumps(
                    {"error": str(e), "trace": traceback.format_exc()}
                )

    await session.commit()


async def handle_message(message: aio_pika.IncomingMessage, redis: Redis):
    async with message.process():
        data = message.body.decode()
        data = json.loads(data)
        async for session in get_db_session():
            if not (job_ids := data.get("job_ids")):
                await handle_normal_flow(session=session, data=data, redis=redis)
            else:
                await handle_retry_flow(redis=redis, session=session, job_ids=job_ids)


async def main():
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    channel = await connection.channel()
    queue = await channel.declare_queue(
        config.RABBITMQ_QUEUE_TRANSLATE_TO_PDF, durable=True
    )

    handler = partial(handle_message, redis=redis)
    await queue.consume(handler)

    await asyncio.Future()  # keep the script alive


if __name__ == "__main__":
    asyncio.run(main())
