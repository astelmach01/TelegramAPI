import logging
from pyrogram.enums import ChatType
from pyrogram.types import User
from pyrogram import Client
from quart import Blueprint, request

from website.api.messages import formatted_messages_by_convo_id
from website.core import manager
from rabbit_mq.send import rpc_client

conversations_route = Blueprint("conversations", __name__)


def get_name(user):
    return (
        f"{user.first_name} {user.last_name}"
        if user.first_name and user.last_name
        else user.first_name
    )


async def formatted_participants_by_convo_id(
    client: Client, conversation_id: str, me: User
):
    conversation = await client.get_chat(conversation_id)

    if conversation.type != ChatType.PRIVATE:
        return []

    person_talking_to_name = get_name(conversation)
    person_talking_to_name = person_talking_to_name or conversation.username

    me_name = get_name(me)
    me_name = me_name or me.username

    return [
        {
            # the user we are talking to
            "id": str(conversation.id),
            "name": person_talking_to_name,
            "role": "source_user",
            "avatar_url": 'https://gravatar.com/avatar/2eb4c1887fa17ea75944707163aebeb9?s=400&d=robohash&r=x'
        },
        {
            # us
            "id": str(me.id),
            "name": me_name,
            "role": "source_user",
            "avatar_url": 'https://gravatar.com/avatar/2eb4c1887fa17ea75944707163aebeb9?s=400&d=robohash&r=x'
        },
    ]


async def get_conversation_by_id(body: dict):
    sender = body["sender"]
    conversation_id = body["conversation_id"]
    messages_limit = body.get("messages_limit")

    client = await manager.get_client_by_id(sender)

    conversation = await client.get_chat(conversation_id)
    messages = await formatted_messages_by_convo_id(
        client, conversation_id, messages_limit
    )
    participants = await formatted_participants_by_convo_id(client, conversation_id)

    return {
        "success": True,
        "data": {
            "id": conversation_id,
            "status": "open",
            "seen": conversation.unread_messages_count == 0,
            "next_messages_cursor": None,
            "messages": messages,
            "participants": participants,
            "link": f"https://google.com",
        },
        "additional_data": {
            "after": "c-next",
        },
    }


@conversations_route.route("/getConversationById")
async def get_conversation_by_id_route(body: dict):
    body["function"] = "getConversationById"
    body["routing_key"] = body["sender"]

    _rpc_client = await rpc_client.connect()
    response = await _rpc_client.post_message_to_server(body)

    logging.info(f"Response from telegram api: {response}")
    return response


async def get_conversations(body: dict):
    sender = body["sender"]
    conversations_limit = body.get("conversations_limit")
    messages_limit = body.get("messages_limit")

    conversations = []
    client = await manager.get_on_message_client(sender)
    me = await client.get_me()

    logging.info(f"Getting conversations with params {body} and client {client}")

    async for conversation in client.get_dialogs(limit=conversations_limit):
        # only supporting private chats for now, group chat support will be added later
        if conversation.chat.type != ChatType.PRIVATE:
            continue

        convo_id = str(conversation.chat.id)
        # messages = await formatted_messages_by_convo_id(
        #     client, convo_id, messages_limit
        # )
        messages = []
        participants = await formatted_participants_by_convo_id(client, convo_id, me)

        conversations.append(
            {
                "id": convo_id,
                "status": "open",
                "seen": conversation.unread_messages_count == 0,
                "next_messages_cursor": None,
                "messages": messages,
                "participants": participants,
            }
        )

    return {
        "success": True,
        "data": conversations,
        "additional_data": {
            "after": "c-next",
        },
    }


@conversations_route.route("/getConversations")
async def get_conversations_route():
    body = await request.get_json()

    body["function"] = "getConversations"
    body["routing_key"] = body["sender"]
    # body["conversations_limit"] = body.get("conversations_limit", 30)
    # body["messages_limit"] = body.get("messages_limit", 30)
    body["conversations_limit"] = 1
    body["messages_limit"] = 1

    _rpc_client = await rpc_client.connect()
    response = await _rpc_client.post_message_to_server(body)

    logging.info(f"Response from telegram api: {response}")
    return response
