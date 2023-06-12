from datetime import datetime
import aiohttp
import logging

from pyrogram import Client

from website.settings import settings


class ClientManager:
    def __init__(self):
        self.on_message_clients: dict[str, Client] = {}
        self.send_message_clients: dict[str, Client] = {}

    async def get_on_message_client(self, phone_number):
        return self.on_message_clients.get(phone_number)

    async def get_send_message_client(self, phone_number):
        return self.send_message_clients.get(phone_number)

    async def put_on_message_client(self, phone_number, client):
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
