# worker.py
import asyncio
import json
from functools import partial

import aio_pika
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from _config import config
from schemas.message import MessageSchema
from models.image_cache import ImageCacheModel
from misc.utils.encoder import encode_text
from services import ocr_service, text_cache_service

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


async def check_if_text_cached(
    input_text: str, redis: Redis, message: MessageSchema
) -> tuple[str | None, str]:
    encoded_text = encode_text(input_text=input_text)
    # Check if the text is already cached in Redis
    cached_text = await redis.get(encoded_text)
    async for session in get_db_session():
        if cached_text:
            logging.info(f"Text is already cached in Redis: {cached_text}")
            await handle_add_new_cache(
                image_hash=message.image_hash,
                pdf_url=cached_text.pdf_url,
                redis=redis,
                session=session,
            )
            return cached_text, encoded_text
        else:
            cached_text_record = await text_cache_service.get_cached_image(
                session=session, input_text=encoded_text
            )
            if cached_text_record:
                await redis.set(encoded_text, cached_text_record.pdf_url)
                await handle_add_new_cache(
                    image_hash=message.image_hash,
                    pdf_url=cached_text_record.pdf_url,
                    redis=redis,
                    session=session,
                )
                return cached_text_record.pdf_url, encoded_text

    return None, encoded_text


async def handle_add_new_cache(
    image_hash: str, pdf_url: str, redis: Redis, session: AsyncSession
):
    await redis.set(image_hash, pdf_url)
    session.add(ImageCacheModel(**{"hash_id": image_hash, "pdf_url": pdf_url}))
    await session.commit()


async def handle_message(message: aio_pika.IncomingMessage, redis: Redis):
    async with message.process():
        data = message.body.decode()
        data = MessageSchema(**json.loads(data))
        logging.info(f"OCR: Received message from RabbitMQ, processing content {data}")

        file_path = data.file_path
        text = await ocr_service.image_to_text(image_path=str(file_path))

        cached_pdf_url, encode_text = await check_if_text_cached(
            input_text=text, redis=redis, message=data
        )
        if cached_pdf_url:
            # TODO: Handle cached scenario
            logging.info(f"Text is already cached in Redis: {cached_pdf_url}")

        else:
            # publish the result to RabbitMQ
            data.encoded_text = encode_text
            data.text_to_translate = text
            await publish_message(message=data.model_dump())


async def publish_message(message: str):
    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=config.RABBITMQ_QUEUE_TRANSLATE,
        )
        logging.info(f"OCR: Published message {message} to RabbitMQ")


async def main():
    redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    channel = await connection.channel()
    queue = await channel.declare_queue(config.RABBITMQ_QUEUE, durable=True)

    handler = partial(handle_message, redis=redis)
    text = await queue.consume(handler)

    await asyncio.Future()  # keep the script alive


if __name__ == "__main__":

    asyncio.run(main())
