# worker.py
import asyncio
import json
import traceback

import aio_pika
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from _config import config
from schemas.message import MessageSchema
from services import translation_service
from models.retry_job import RetryJobModel
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


PHASE = 2


async def publish_message(message: str):
    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=config.RABBITMQ_QUEUE_TRANSLATE_TO_PDF,
        )
        logging.info(f"Translation: Published message {message} to RabbitMQ")


async def create_retry_job(session: AsyncSession, data: dict) -> RetryJobModel:
    job = RetryJobModel(**data)
    session.add(job)
    await session.commit()
    return job


async def handle_normal_flow(data: dict, session: AsyncSession):
    data = MessageSchema(**data)
    logging.info(
        f"Translation: Received message from RabbitMQ, processing content {data}"
    )
    # your business logic here, use shared functions or DB access
    text_to_translate = data.text_to_translate
    try:
        translated_text = await translation_service.translate(text=text_to_translate)

        data.translated_text = translated_text
        await publish_message(message=json.dumps(data.model_dump()))
    except Exception:
        await create_retry_job(
            session=session,
            data={
                "step": PHASE,
                "file_url": data.file_url,
                "image_hash": data.image_hash,
                "text_to_translate": data.text_to_translate,
                "encoded_text": data.encoded_text,
                "job_metadata": json.dumps(
                    {
                        "error": str(traceback.format_exc()),
                        "trace": traceback.format_exc(),
                    }
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


async def handle_retry_flow(session: AsyncSession, job_ids: list[int]):
    NEXT_PHASE = 3
    failed_jobs = await get_failed_jobs(session=session, job_ids=job_ids)
    if failed_jobs:
        for job in failed_jobs:
            try:
                text_to_translate = job.text_to_translate
                translated_text = await translation_service.translate(
                    text=text_to_translate
                )
                job.translated_text = translated_text
                job.step = NEXT_PHASE

            except Exception as e:
                job.job_metadata = json.dumps(
                    {"error": str(e), "trace": traceback.format_exc()}
                )

    await session.commit()


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = message.body.decode()
        data = json.loads(data)
        async for session in get_db_session():
            if not (job_ids := data.get("job_ids")):
                await handle_normal_flow(data=data, session=session)
            else:
                await handle_retry_flow(session=session, job_ids=job_ids)


async def main():
    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    channel = await connection.channel()
    queue = await channel.declare_queue(
        config.RABBITMQ_QUEUE_OCR_TO_TRANSLATE, durable=True
    )
    await queue.consume(handle_message)

    await asyncio.Future()  # keep the script alive


if __name__ == "__main__":
    asyncio.run(main())
