import asyncio
import json
import logging
import uuid
from aio_pika import Message
from aio_pika.abc import (
    AbstractChannel,
    AbstractConnection,
    AbstractIncomingMessage,
    AbstractQueue,
)
from rabbit_mq.client import BaseClient

from website.settings import settings


class Client(BaseClient):
    connection: AbstractConnection | None
    channel: AbstractChannel
    callback_queue: AbstractQueue
    loop: asyncio.AbstractEventLoop

    def __init__(
        self, username: str, password: str, broker_id: str, region: str = "us-east-2"
    ) -> None:
        super().__init__(username, password, broker_id, region)
        self.futures: dict[str, asyncio.Future] = {}
        self.loop = asyncio.get_event_loop()

    async def connect(self) -> "Client":
        if self.connection is not None:
            return self

        logging.info("Connecting client to rabbitmq")
        await super()._connect()

        # replace number queue with db call
        self.callback_queue = await self.channel.declare_queue(
            "callback_queue_1", durable=True, exclusive=True
        )
        await self.callback_queue.bind(
            self.exchange, routing_key=self.callback_queue.name
        )

        logging.info("Connected client to rabbitmq")

        await self.callback_queue.consume(self.on_response)

        logging.info("Client consuming messages from rabbitmq")

        return self

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            logging.info(f"Received message without correlation id: {message}")
            return

        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

        await message.ack()

    async def post_message_to_server(self, body: dict) -> dict:
        correlation_id = str(uuid.uuid4())
        routing_key = body["routing_key"]

        future = self.loop.create_future()
        self.futures[correlation_id] = future

        logging.info(f"Client publishing message {body} to server")
        await self.exchange.publish(
            Message(
                body=json.dumps(body).encode(),
                content_type="application/json",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=routing_key,
        )
        logging.info(f"Client published message {body} to server, awaiting response")

        # wait for a max of 30 seconds for a response
        try:
            res = await asyncio.wait_for(future, timeout=25)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            logging.info(f"Client timed out waiting for response from server")
            return {"success": False, "error": "timeout"}
            
        logging.info(f"Client received response {res} from server")
        return json.loads(res.decode())

    async def close(self):
        logging.info("Client closing connection to rabbitmq")
        await self.connection.close()


rpc_client = Client(
    username=settings.AWS_RABBIT_MQ_USERNAME,
    password=settings.AWS_RABBIT_MQ_PASSWORD,
    broker_id=settings.AWS_RABBIT_MQ_BROKER_ID,
)
