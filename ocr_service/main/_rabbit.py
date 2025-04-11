import json
import logging
from dataclasses import dataclass
from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from .enums import RabbitStatus


@dataclass
class RabbitConnection:
    connection: AbstractRobustConnection | None = None
    channel: AbstractRobustChannel | None = None

    def status(self) -> bool:
        """
        Checks if connection established

        :return: True if connection established
        """
        if self.connection.is_closed or self.channel.is_closed:
            return False
        return True

    async def _clear(self) -> None:
        if not self.channel.is_closed:
            await self.channel.close()
        if not self.connection.is_closed:
            await self.connection.close()

        self.connection = None
        self.channel = None

    async def connect(self) -> None:
        """
        Establish connection with the RabbitMQ

        :return: None
        """
        logging.info(RabbitStatus.CONNECTING)
        try:
            from ._config import config

            self.connection = await connect_robust(config.RABBITMQ_CONNECTION)
            self.channel = await self.connection.channel(publisher_confirms=False)
            logging.info(RabbitStatus.CONNECTED)
        except Exception as e:
            await self._clear()
            logging.error(e.__dict__)

    async def disconnect(self) -> None:
        """
        Disconnect and clear connections from RabbitMQ

        :return: None
        """
        await self._clear()

    async def send_messages(
        self, messages: list | dict, routing_key: str = None
    ) -> None:
        """
        Public message or messages to the RabbitMQ queue.

        :param messages: list or dict with messages objects.
        :param routing_key: Routing key of RabbitMQ, not required. Tip: the same as in the consumer.
        """
        if not routing_key:
            from ._config import config

            routing_key = config.RABBITMQ_QUEUE

        if not self.channel:
            raise RuntimeError(RabbitStatus.NOT_CONNECTED)

        if isinstance(messages, dict):
            messages = [messages]

        async with self.channel.transaction():
            for message in messages:
                message = Message(body=json.dumps(message).encode())

                await self.channel.default_exchange.publish(
                    message,
                    routing_key=routing_key,
                )


rabbit_connection = RabbitConnection()
