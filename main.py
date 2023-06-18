import asyncio
import os

import hypercorn
from hypercorn.config import Config
import hypercorn.asyncio

from website import create_app
from website.util import remove_session_files
from rabbit_mq.send import client
from rabbit_mq.receive import server

app = create_app()


async def start():
    remove_session_files()
    
    @app.before_serving
    async def connect_rabbit_mq():
        await server.connect()
        await client.connect()

    config = Config()
    port = os.getenv("PORT", 8080)
    config.bind = [f"0.0.0.0:{port}"]

    await hypercorn.asyncio.serve(app, config)


if __name__ == "__main__":
    asyncio.run(start())
