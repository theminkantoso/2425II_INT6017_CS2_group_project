# worker.py
import asyncio
import json

import aio_pika
from _config import config
from schemas.message import MessageSchema
from services import translation_service

import logging

logging.basicConfig(level=logging.INFO)


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = message.body.decode()
        data = MessageSchema(**json.loads(data))
        logging.info(
            f"Translation: Received message from RabbitMQ, processing content {data}"
        )
        # your business logic here, use shared functions or DB access
        text_to_translate = data.text_to_translate
        translated_text = await translation_service.translate(text=text_to_translate)

        data.translated_text = translated_text
        await publish_message(message=json.dumps(data.model_dump()))


async def publish_message(message: str):
    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=config.RABBITMQ_QUEUE_TRANSLATE_TO_PDF,
        )
        logging.info(f"Translation: Published message {message} to RabbitMQ")


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
