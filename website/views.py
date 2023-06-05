"""
Routes
"""
import json
import logging

from pyrogram import Client
from pyrogram.handlers import MessageHandler
from quart import Blueprint, render_template, request, jsonify
import pandas as pd
from .util import run_query, SQLQueryRunner, get_db
from .core import storage

views = Blueprint("views", __name__)

# this is to sync up the host of this api and the provider api so the load balancer uses the same machine (session stickiness) between the two HTTP requests. This should be the first call between the provider API.
@views.route("/sync")
async def sync():
    return jsonify({"status": "success"})


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


@views.route("/send_code_1", methods=["POST"])
async def send_code_1():
    payload = await request.get_json()

    phone_number = payload.get("phone_number")
    telegram_api_id = payload.get("telegram_api_id")
    telegram_api_hash = payload.get("telegram_api_hash")
    pipedrive_client_id = payload.get("pipedrive_client_id")
    pipedrive_client_secret = payload.get("pipedrive_client_secret")

    # store this info in a database
    with SQLQueryRunner() as cursor:
        logging.info("Inserting credentials into database")
        sql = run_query(
            "insert_telegram_credentials.sql",
            phone_number=phone_number,
            telegram_api_id=telegram_api_id,
            telegram_api_hash=telegram_api_hash,
            pipedrive_client_id=pipedrive_client_id,
            pipedrive_client_secret=pipedrive_client_secret,
        )
        cursor.execute(sql)

    client = Client(phone_number + "-on-message", telegram_api_id, telegram_api_hash)
    await client.connect()
    
    await storage.put_on_message_client(phone_number, client)

    try:
        sent_code = await client.send_code(phone_number)

    except Exception as e:
        logging.error("Error sending code: " + str(e))
        return jsonify({"success": False, "error": str(e)})

    logging.info("Sent code to: " + phone_number)

    phone_code_hash = sent_code.phone_code_hash

    return jsonify(
        {
            "success": True,
            "phone_code_hash": phone_code_hash,
            "phone_number": phone_number,
        }
    )


@views.route("/send_code_2", methods=["POST"])
async def send_code_2():
    payload = await request.get_json()

    phone_number = payload.get("phone_number")

    with SQLQueryRunner() as cursor:
        logging.info("Selecting phone number")
        sql = run_query("select_phone_number.sql", phone_number=phone_number)
        cursor.execute(sql)

        result = pd.DataFrame(cursor.fetchone(), index=[0]).iloc[0]

    telegram_api_id = result["telegram_api_id"]
    telegram_api_hash = result["telegram_api_hash"]
    
    client = Client(phone_number + "-send-message", telegram_api_id, telegram_api_hash)
    await client.connect()
    
    await storage.put_send_message_client(phone_number, client)

    try:
        sent_code = await client.send_code(phone_number)
    except Exception as e:
        logging.error("Error sending code: " + str(e))
        return jsonify({"success": False, "error": str(e)})
    
    phone_code_hash = sent_code.phone_code_hash

    return jsonify(
        {
            "success": True,
            "phone_code_hash": phone_code_hash,
            "phone_number": phone_number,
        }
    )


@views.route("/create_string_1", methods=["POST"])
async def create_string_1():
    payload = await request.get_json()

    phone_number = payload.get("phone_number")
    phone_code_hash = payload.get("phone_code_hash")
    auth_code = payload.get("auth_code")

    client = await storage.get_on_message_client(phone_number)
    await client.sign_in(phone_number, phone_code_hash, auth_code)
    
    session_string = await client.export_session_string()

    with SQLQueryRunner() as cursor:
        logging.info("Inserting session string into database")
        sql = run_query(
            "insert_on_message_string.sql",
            phone_number=phone_number,
            on_message_string=session_string,
        )
        cursor.execute(sql)

    return jsonify({"success": True})


@views.route("/create_string_2", methods=["POST"])
async def create_string_2():
    payload = await request.get_json()

    phone_number = payload.get("phone_number")
    phone_code_hash = payload.get("phone_code_hash")
    auth_code = payload.get("auth_code")

    with SQLQueryRunner() as cursor:
        logging.info("Selecting phone number")
        sql = run_query("select_phone_number.sql", phone_number=phone_number)
        cursor.execute(sql)

        result = pd.DataFrame(cursor.fetchone(), index=[0]).iloc[0]

    pipedrive_client_id = result["pipedrive_client_id"]

    client = await storage.get_send_message_client(phone_number)
    await client.sign_in(phone_number, phone_code_hash, auth_code)
    
    session_string = await client.export_session_string()

    with SQLQueryRunner() as cursor:
        logging.info("Inserting session string into database")
        sql = run_query(
            "insert_send_message_string.sql",
            phone_number=phone_number,
            send_message_string=session_string,
        )
        cursor.execute(sql)

    return jsonify({"success": True, "pipedrive_client_id": pipedrive_client_id})
