import asyncio
import os
import hypercorn
from hypercorn.config import Config
from website import create_app
from website.settings import settings

app = create_app()

async def start():
    config = Config()
    port = os.getenv("PORT", 5000)
    config.bind = [f"0.0.0.0:{port}"]

    await hypercorn.asyncio.serve(app, config)


if __name__ == "__main__":
    asyncio.run(start())
