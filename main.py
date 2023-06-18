import asyncio
import os

import hypercorn
from hypercorn.config import Config
import hypercorn.asyncio
import pandas as pd

from website import create_app
from website.util import SQLQueryRunner, remove_session_files, run_query
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
    # with SQLQueryRunner() as cursor:
    #     sql = run_query("select_all_credentials.sql")
    #     cursor.execute(sql)

    #     credentials = pd.DataFrame(cursor.fetchall())
        
    #     sql = run_query("select_all_sessions.sql")
    #     cursor.execute(sql)
        
    #     sessions = pd.DataFrame(cursor.fetchall())
        
        
    # print(credentials)
    # print(sessions)
    # exit()
        
    asyncio.run(start())
