import logging
import ssl
import aio_pika


class BaseClient:
    def __init__(
        self,
        username: str,
        password: str,
        broker_id: str,
        region: str = "us-east-2",
        port: int = 5671,
    ) -> None:
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.ssl_context.set_ciphers("ECDHE+AESGCM:!ECDSA")

        self.url = f"amqps://{username}:{password}@{broker_id}.mq.{region}.amazonaws.com:{port}"
        self.connection = None

    async def _connect(self) -> None:
        if self.connection is not None:
            return

        logging.info(f"Connecting to {self.url}")
        self.connection = await aio_pika.connect(
            url=self.url, ssl_context=self.ssl_context
        )
        self.channel = await self.connection.channel()

        self.exchange = await self.channel.declare_exchange(
            "exchange", aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def close(self) -> None:
        await self.connection.close()
