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

        super()._connect()

        self.callback_queue = await self.channel.declare_queue(
            durable=True, exclusive=True
        )
        await self.callback_queue.bind(
            self.exchange, routing_key=self.callback_queue.name
        )
        await self.callback_queue.consume(self.on_response)

        return self

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            logging.info(f"Received message without correlation id: {message}")
            return

        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

    async def post_message_to_server(
        self, message, sender: str, recipient: str, message_id: str
    ) -> dict:
        correlation_id = str(uuid.uuid4())

        future = self.loop.create_future()
        self.futures[correlation_id] = future

        body = {
            "message": message,
            "sender": sender,
            "recipient": recipient,
            "message_id": message_id,
        }

        await self.exchange.publish(
            Message(
                body=json.dumps(body).encode(),
                content_type="application/json",
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name,
            ),
            routing_key=sender,
        )

        res = await future
        return json.loads(res.decode())

    async def close(self):
        await self.connection.close()


client = Client(
    settings.AWS_RABBIT_MQ_USERNAME,
    settings.AWS_RABBIT_MQ_PASSWORD,
    settings.AWS_RABBIT_MQ_HOST,
)


async def main() -> None:
    client: Client = await client().connect()

    args = {
        "message": "Hello, world!",
        "sender": "Bennett",
        "recipient": "+19735248259",
        "message_id": "1234",
    }

    print(f" [x] Requesting {args}")
    response = await client.post_message_to_server(**args)
    print(f" [.] Got {response}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
