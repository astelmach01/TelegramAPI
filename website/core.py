class ClientStorage:
    def __init__(self):
        self.clients = {}

    async def put_client(self, phone_number, client):
        self.clients[phone_number] = client

    async def get_client(self, phone_number: str):
        return self.clients.get(phone_number)


storage = ClientStorage()
