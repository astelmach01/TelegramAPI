import asyncio
import os

import hypercorn
from hypercorn.config import Config
import hypercorn.asyncio
import pandas as pd

from website import create_app
from website.util import remove_session_files, get_db
from website.core import manager
from rabbit_mq.send import client
from rabbit_mq.receive import server

app = create_app()
conn = get_db()


async def start():
    remove_session_files()

    @app.before_serving
    async def connect_all_async():
        await manager.create_clients()
        await server.connect()
        await client.connect()
        
    @app.after_serving
    async def close_conn():
        conn.close()
        await server.close()
        await client.close()

    config = Config()
    port = os.getenv("PORT", 8080)
    config.bind = [f"0.0.0.0:{port}"]

    await hypercorn.asyncio.serve(app, config)


if __name__ == "__main__":        
    asyncio.run(start())
