from website.api.conversations import get_name
from website.core import manager


async def get_sender_by_id(body: dict):
    sender_id = body["sender"]

    client = await manager.get_client_by_id(sender_id)
    sender_info = await client.get_users(sender_id)

    name = get_name(sender_info)
    name = name or sender_info.username

    return {
        "success": True,
        "data": {
            "id": sender_info.id,
            "name": name,
        },
    }
