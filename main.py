import asyncio
import os

import hypercorn
from hypercorn.config import Config
import hypercorn.asyncio

from website import create_app
from website.util import get_db
from website.core import manager
from rabbit_mq.send import client
from rabbit_mq.receive import server


app = create_app()
conn = get_db()


async def start():
    loop = asyncio.get_event_loop()

    @app.errorhandler(404)
    async def not_found(e):
        return "This page has not been found", 404

    @app.before_serving
    async def connect_all_async():
        await server.connect()
        await client.connect()
        await manager.create_clients()
        task = loop.create_task(server.start())
        manager.tasks.append(task)

    @app.after_serving
    async def close_conn():
        conn.close()
        await server.close()
        await client.close()
        await manager.close()

        for task in manager.tasks:
            task.cancel()

    config = Config()
    port = os.getenv("PORT", 8080)
    config.bind = [f"0.0.0.0:{port}"]

    await hypercorn.asyncio.serve(app, config)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
