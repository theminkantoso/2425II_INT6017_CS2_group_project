# worker.py
import asyncio
import json

import aio_pika
from _config import config
from services import ocr_service

import logging

logging.basicConfig(level=logging.INFO)


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = message.body.decode()
        data = json.loads(data)
        logging.info(f"OCR: Received message from RabbitMQ, processing content {data}")
        # your business logic here, use shared functions or DB access
        file_path = data["file_path"]
        text = await ocr_service.image_to_text(image_path=str(file_path))

        # publish the result to RabbitMQ
        await publish_message(
            message=json.dumps({"text_to_translate": text, "file_path": str(file_path)})
        )


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
    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    channel = await connection.channel()
    queue = await channel.declare_queue(config.RABBITMQ_QUEUE, durable=True)
    text = await queue.consume(handle_message)

    await asyncio.Future()  # keep the script alive


if __name__ == "__main__":
    asyncio.run(main())
