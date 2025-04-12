# worker.py
import asyncio
import json
from pathlib import Path

import aio_pika
from _config import config
from services import pdf_service

import logging

logging.basicConfig(level=logging.INFO)


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = message.body.decode()
        data = json.loads(data)
        logging.info(f"PDF: Received message from RabbitMQ, processing content {data}")
        # your business logic here, use shared functions or DB access
        text_to_translate = data["translated_text"]
        image_file_path = Path(data["file_path"])
        file_uuid = image_file_path.with_suffix("")

        await pdf_service.text_to_pdf(
            text=text_to_translate, output_filename=str(f"{file_uuid}.pdf")
        )


async def main():
    connection = await aio_pika.connect_robust(config.RABBITMQ_CONNECTION)
    channel = await connection.channel()
    queue = await channel.declare_queue(config.RABBITMQ_QUEUE_PDF, durable=True)
    await queue.consume(handle_message)

    await asyncio.Future()  # keep the script alive


if __name__ == "__main__":
    asyncio.run(main())
