# worker.py
import asyncio
import json
from functools import partial
from pathlib import Path

import aio_pika
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from _config import config
from schemas.message import MessageSchema
from services import pdf_service
from models.text_cache import TextCacheModel
from models.image_cache import ImageCacheModel

import logging

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


async def save_to_cache(message: MessageSchema, pdf_url: str, redis: Redis):
    async for session in get_db_session():
        # Here you would save the PDF URL to your database
        session.add(
            TextCacheModel(**{"pdf_url": pdf_url, "text_encode": message.encoded_text})
        )
        session.add(
            ImageCacheModel(**{"pdf_url": pdf_url, "hash_id": message.image_hash})
        )
        await session.commit()

        await redis.set(message.encoded_text, pdf_url)
        await redis.set(message.image_hash, pdf_url)


async def handle_message(message: aio_pika.IncomingMessage, redis: Redis):
    async with message.process():
        data = message.body.decode()
        data = MessageSchema(**json.loads(data))
        logging.info(f"PDF: Received message from RabbitMQ, processing content {data}")
        # your business logic here, use shared functions or DB access
        text_to_translate = data.translated_text
        image_file_path = Path(data.file_path)
        file_uuid = image_file_path.with_suffix("")

        pdf_url = await pdf_service.text_to_pdf(
            text=text_to_translate, output_filename=str(f"{file_uuid}.pdf")
        )

        await save_to_cache(message=data, pdf_url=pdf_url, redis=redis)


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
