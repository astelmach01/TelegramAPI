"""
Routes
"""
import logging

from pyrogram import Client
from pyrogram.handlers import MessageHandler
from quart import Blueprint, request, jsonify
import pandas as pd
from .util import run_query, SQLQueryRunner, get_db
from .core import storage

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

    # create the client to send the code
    client = Client(phone_number, api_id=telegram_api_id, api_hash=telegram_api_hash)
    await storage.put_client(phone_number, client)
    await client.connect()
    logging.info("Client connected, sending code")

    sent_code = await client.send_code(phone_number)
    logging.info("Sent code to: " + phone_number)

    phone_code_hash = sent_code.phone_code_hash

    # store this info in a database
    with SQLQueryRunner(get_db()) as cursor:
        logging.info("Inserting credentials into database")
        sql = run_query("insert_telegram_credentials.sql", phone_number=phone_number, phone_code_hash=phone_code_hash,
                        telegram_api_id=telegram_api_id, telegram_api_hash=telegram_api_hash,
                        pipedrive_client_id=pipedrive_client_id, pipedrive_client_secret=pipedrive_client_secret)
        cursor.execute(sql)

    result = jsonify({"message": "Payload received successfully"})

    return result


@views.route('/verify', methods=['POST'])
async def verify():
    payload = await request.get_json()

    phone_number = payload.get("phone_number")
    auth_code = payload.get("auth_code")

    with SQLQueryRunner(get_db()) as cursor:
        logging.info("Selecting phone number")
        sql = run_query('select_phone_number.sql', phone_number=phone_number)
        cursor.execute(sql)

        result = pd.DataFrame(cursor.fetchall()).iloc[0]

    phone_code_hash = result['phone_code_hash']

    client = await storage.get_client(phone_number)
    client.add_handler(MessageHandler(new_message))
    await client.sign_in(phone_number=phone_number, phone_code_hash=phone_code_hash, phone_code=auth_code)

    return jsonify({"message": "Successfully signed in to " + phone_number})
