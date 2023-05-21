"""
Routes
"""
import logging

from pyrogram import Client
from pyrogram.handlers import MessageHandler
from quart import Blueprint, request, jsonify
from .util import run_query, SQLQueryRunner, get_db

views = Blueprint("views", __name__)


async def new_message(client, message):
    msg = message.text
    sender_id = str(message.from_user.id)
    time = message.date

    logging.info("Got a message", msg, sender_id, time)

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

    # store this info in a database
    with SQLQueryRunner(get_db()) as cursor:
        logging.info("Inserting credentials into database")
        sql = run_query("insert_telegram_credentials", phone_number=phone_number, telegram_api_id=telegram_api_id, telegram_api_hash=telegram_api_hash, pipedrive_client_id=pipedrive_client_id, pipedrive_client_secret=pipedrive_client_secret)
        cursor.execute(sql)
    

    # create the client to send the code
    client = Client(phone_number, api_id=telegram_api_id, api_hash=telegram_api_hash)
    client.add_handler(MessageHandler(new_message))
    await client.connect()
    
    logging.info("Client connected")
    
    result = await jsonify({"message": "Payload received successfully"})

    return result
