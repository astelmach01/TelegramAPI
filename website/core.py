from pyrogram import Client


class ClientStorage:
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


storage = ClientStorage()
