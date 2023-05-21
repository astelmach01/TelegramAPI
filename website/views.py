"""
Routes
"""
import os

from pyrogram.handlers import MessageHandler
from quart import Blueprint, request, render_template, jsonify
from pyrogram import Client

views = Blueprint("views", __name__)


async def new_message(client, message):
    msg = message.text
    sender_id = str(message.from_user.id)
    time = message.date

    print("Got a message", msg, sender_id, time)

    await send_message_to_PD(
        access_token,
        time=time,
        msg=msg,
        sender_id=sender_id,
    )


@views.route("/create", methods=["POST"])
async def create():
    payload = await request.get_json()
    
    phone_number = payload.get("phone_number")
    telegram_api_id = payload.get("telegram_api_id")
    telegram_api_hash = payload.get("telegram_api_hash")
    pipedrive_client_id = payload.get("pipedrive_client_id")
    pipedrive_client_secret = payload.get("pipedrive_client_secret")

    # TODO: store this info in a database

    # create the client to send the code
    client = Client(phone_number, api_id=telegram_api_id, api_hash=telegram_api_hash)
    client.add_handler(MessageHandler(new_message))
    await client.connect()

    return jsonify({"message": "Payload received successfully"})
