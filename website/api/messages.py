from datetime import datetime, timedelta, timezone
import logging

from quart import Blueprint, request
from website.core import manager
from pyrogram import Client
from rabbit_mq.send import rpc_client

messages_route = Blueprint("messages", __name__)


# this is the function that handles the main logic when someone sends a message from pipedrive to us. This assumes that both the sender and recipient have installed the plugin, because we can't modify our own chat history (i.e. we can't tell telegram that a user sent a message to us)
async def post_message(body: dict) -> dict:
    message = body["message"]
    sender = body["sender"]
    recipient = body["recipient"]
    message_id = body["message_id"]

    client = await manager.get_client_by_id(sender)
    if client is None:
        return {"success": False, "data": {"id": message_id}}

    try:
        # the sender sent a message to us, update the chat with the message
        await client.send_message(recipient, message)
        return {"success": True, "data": {"id": message_id}}
    except Exception as e:
        logging.exception(e)
        return {"success": False, "data": {"id": message_id}}


async def formatted_messages_by_convo_id(
    client: Client, conversation_id: str, messages_limit: int
):
    messages = []
    async for message in client.get_chat_history(conversation_id, limit=messages_limit):
        # if the message is None, it is something like "the name of the group was changed to ...", ignore it
        if not message.text:
            continue

        formatted = {
            "id": str(message.id),
            "status": "sent",
            "created_at": message.date.strftime("%Y-%m-%d %H:%M:%S"),
            "message": message.text or "",
            "sender_id": str(message.from_user.id),
            "reply_by": (message.date + timedelta(days=365)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "attachments": [],
        }

        messages.append(formatted)

    return messages


@messages_route.route("/postMessage", methods=["POST"])
async def post_message():
    data = await request.form
    data = data.to_dict()
    
    function = "post_message"
    recipient = data["recipientIds[]"]

    if recipient[0] != "+":
        recipient = "+" + recipient

    message_id = "msg-pd-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    body = {
        "function": function,
        "routing_key": data["senderId"],
        "message": data["message"],
        "sender": data["senderId"],
        "recipient": recipient,
        "message_id": message_id,
    }

    logging.info(f"Incoming message from pipedrive with params {data}")

    _rpc_client = await rpc_client.connect()
    response = await _rpc_client.post_message_to_server(body)

    logging.info(f"Response from telegram api: {response}")
    return response