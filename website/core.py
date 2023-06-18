import asyncio
from datetime import datetime
import aiohttp
import logging
import pandas as pd

from pyrogram import Client
from pyrogram.handlers import MessageHandler

from website.util import SQLQueryRunner, run_query
from website.settings import settings


class ClientManager:
    def __init__(self):
        self.on_message_clients: dict[str, Client] = {}
        self.send_message_clients: dict[str, Client] = {}
        self.tasks = []

    async def get_on_message_client(self, phone_number):
        return self.on_message_clients.get(phone_number)

    async def get_send_message_client(self, phone_number):
        return self.send_message_clients.get(phone_number)

    async def put_on_message_client(self, phone_number, client):
        from rabbit_mq.receive import server

        await server.bind_queue(phone_number)
        self.on_message_clients[phone_number] = client

    async def put_send_message_client(self, phone_number, client):
        self.send_message_clients[phone_number] = client

    async def start_client(self, client: Client):
        try:
            await client.disconnect()
        except:
            # client was not connected in the first place, that's fine
            pass
        logging.info("Starting client!")
        await client.start()

    async def create_clients(self):
        with SQLQueryRunner() as cursor:
            sql = run_query("select_all.sql")
            cursor.execute(sql)

            result = pd.DataFrame(cursor.fetchall())

        # iterate through the rows
        for _, user in result.iterrows():
            logging.info(f"Creating client for {user['phone_number']}")
            phone_number = user["phone_number"]
            on_message_string = user["on_message"]
            send_message_string = user["send_message"]

            on_message_client = Client(
                phone_number + "-" + "on_message",
                session_string=on_message_string,
                phone_number=phone_number,
            )

            send_message_client = Client(
                phone_number + "-" + "send_message",
                session_string=send_message_string,
                phone_number=phone_number,
            )

            on_message_client.add_handler(MessageHandler(new_message))
            send_message_client.add_handler(MessageHandler(new_message))

            loop = asyncio.get_event_loop()
            task = loop.create_task(self.start_client(on_message_client))
            self.tasks.append(task)

            await self.put_on_message_client(phone_number, on_message_client)
            await self.put_send_message_client(phone_number, send_message_client)

            logging.info(f"Started client for {user['phone_number']}")

    async def close(self):
        await self.stop_clients()

    async def stop_clients(self):
        logging.info("Stopping clients")
        for client in self.on_message_clients.values():
            try:
                await client.stop()
            except ConnectionError:
                pass

        for client in self.send_message_clients.values():
            try:
                await client.stop()
            except ConnectionError:
                pass

        logging.info("Stopped clients")


async def new_message(client, message):
    msg = message.text
    sender_id = str(message.from_user.id)
    conversation_id = str(message.chat.id)
    receiving_phone_number = client.phone_number
    time = message.date

    await send_message_to_provider(
        receiving_phone_number=receiving_phone_number,
        time=time,
        msg=msg,
        conversation_id=conversation_id,
        sender_id=sender_id,
    )


async def send_message_to_provider(
    msg: str,
    receiving_phone_number: str,
    time: datetime | str,
    sender_id: str,
    conversation_id: str,
):
    if msg == None or str(msg) == "None" or str(msg) == "":
        return

    logging.info("Sending message from Telegram to Pipedrive Provider API")

    url = settings.PIPEDRIVE_API_URL

    if type(time) != str:
        time = time.strftime("%Y-%m-%d %H:%M:%S")

    json = {
        "msg": msg,
        "receiving_phone_number": receiving_phone_number,
        "time": time,
        "sender_id": sender_id,
        "conversation_id": conversation_id,
    }

    # send a post request to url + "/channels/messages/receive
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url + "api/channels/messages/receive", json=json
        ) as response:
            res = await response.json()
            logging.info("Response from Pipedrive Provider API", res)


manager = ClientManager()
