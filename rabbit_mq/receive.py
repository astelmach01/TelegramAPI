import json
import logging

from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage
from rabbit_mq.functions import functions
from rabbit_mq.client import BaseClient

from website.settings import settings


class Server(BaseClient):
    async def connect(self) -> "Server":
        logging.info("Connecting server to rabbitmq")
        await super()._connect()
        logging.info("Connected server to rabbitmq")

        queue_name = "rpc_queue_1"  # change this to multiple queues
        self.queue = await self.channel.declare_queue(
            queue_name, durable=True, exclusive=True
        )
        logging.info(f"Server declared queue {queue_name}")
        return self

    async def bind_queue(self, routing_key: str) -> None:
        await self.queue.bind(self.exchange, routing_key=routing_key)
        logging.info(
            f"Server bound queue {self.queue.name} to routing key {routing_key}"
        )

    async def listen(self) -> None:
        if self.connection is None:
            await self.connect()

        logging.info("Server listening for messages")
        async with self.queue.iterator() as qiterator:
            message: AbstractIncomingMessage
            async for message in qiterator:
                try:
                    async with message.process():
                        assert message.reply_to is not None

                        body = json.loads(message.body.decode())

                        logging.info(f"Server received message {body}")

                        func = functions[body["function"]]

                        response = await func(body)

                        logging.info(f"Server sending response {response}")

                        await self.exchange.publish(
                            Message(
                                body=json.dumps(response).encode(),
                                correlation_id=message.correlation_id,
                            ),
                            routing_key=message.reply_to,
                        )

                        logging.info(f"Server published response {response}")

                except Exception as e:
                    logging.exception(f"Server error processing message {e}")

    async def start(self) -> None:
        logging.info("Server listening for messages")
        await self.listen()

    async def close(self) -> None:
        logging.info("Server closing connection to rabbitmq")
        await self.connection.close()


server = Server(
    username=settings.AWS_RABBIT_MQ_USERNAME,
    password=settings.AWS_RABBIT_MQ_PASSWORD,
    broker_id=settings.AWS_RABBIT_MQ_BROKER_ID,
)
