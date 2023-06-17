import asyncio
import json
import logging

from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage
from rabbit_mq.client import BaseClient

from website.core import manager
from website.settings import settings


# this is the function that handles the main logic when someone sends a message from pipedrive to us. This assumes that both the sender and recipient have installed the plugin, because we can't modify our own chat history (i.e. we can't tell telegram that a user sent a message to us)
async def post_message(message, sender, recipient, message_id) -> dict:
    client = await manager.get_send_message_client(sender)
    if client is None:
        return {"success": False, "id": message_id}

    try:
        # the sender sent a message to us, update the chat with the message
        await client.send_message(recipient, message)
        return {"success": True, "id": message_id}
    except Exception as e:
        logging.exception(e)
        return {"success": False, "id": message_id}


class Server(BaseClient):
    async def connect(self) -> "Server":
        await super()._connect()

        self.queue = await self.channel.declare_queue(
            "rpc_queue", durable=True, exclusive=True
        )
        return self

    async def bind_queue(self, routing_key: str) -> None:
        await self.queue.bind(self.exchange, routing_key=routing_key)

    async def listen(self) -> None:
        logging.info("Listening for messages")
        async with self.queue.iterator() as qiterator:
            message: AbstractIncomingMessage
            async for message in qiterator:
                try:
                    async with message.process(requeue=False):
                        assert message.reply_to is not None

                        body = json.loads(message.body.decode())

                        information = body["message"]
                        sender = body["sender"]
                        recipient = body["recipient"]
                        message_id = body["message_id"]

                        response = await post_message(
                            information, sender, recipient, message_id
                        )

                        await self.exchange.publish(
                            Message(
                                body=json.dumps(response).encode(),
                                correlation_id=message.correlation_id,
                            ),
                            routing_key=message.reply_to,
                        )

                except Exception:
                    logging.exception("Processing error for message %r", message)

    async def close(self) -> None:
        await self.connection.close()


server = Server(
    settings.AWS_RABBIT_MQ_USERNAME,
    settings.AWS_RABBIT_MQ_PASSWORD,
    settings.AWS_RABBIT_MQ_HOST,
)

async def main() -> None:
    await server.connect().listen()

if __name__ == "__main__":
    asyncio.run(main())
