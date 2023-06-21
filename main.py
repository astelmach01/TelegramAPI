import asyncio
import logging
import os

import hypercorn
from hypercorn.config import Config
import hypercorn.asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from website import create_app
from website.util import get_db, remove_session_files
from website.core import manager, backround_tasks
from rabbit_mq.send import rpc_client
from rabbit_mq.receive import server


app = create_app()

conn = get_db()

async def print_manager_stats():
    while True:
        await asyncio.sleep(5 * 60)
        await manager.report()
    
async def start():
    logging.info("Starting server")
    
    loop = asyncio.get_event_loop()
    
    await app.app_context().push()

    @app.errorhandler(404)
    async def not_found(e):
        return "This page has not been found", 404

    @app.before_serving
    async def connect_all_async():
        
        remove_session_files()
        await server.connect()
        await rpc_client.connect()
        await manager.create_clients()
        task = loop.create_task(server.start())
        backround_tasks.add(task)

    @app.after_serving
    async def close_conn():
        conn.close()
        await server.close()
        await rpc_client.close()
        await manager.close()

        for task in backround_tasks:
            task.cancel()
            
    app.add_background_task(print_manager_stats)

    config = Config()
    port = os.getenv("PORT", 8080)
    config.bind = [f"0.0.0.0:{port}"]
    
    await hypercorn.asyncio.serve(app, config)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start())
