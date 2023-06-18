"""
Routes
"""
from datetime import datetime, timezone
import logging
from typing import Literal

from pyrogram import Client
from pyrogram.handlers import MessageHandler
from quart import Blueprint, request
import pandas as pd
import asyncio

from .util import run_query, SQLQueryRunner
from .core import manager, new_message, backround_tasks

from rabbit_mq.send import client

views = Blueprint("views", __name__)


# this is to sync up the host of this api and the provider api so the load balancer uses the same machine (session stickiness) between the two HTTP requests. This should be the first call between the provider API.
@views.route("/sync")
async def sync():
    return {"status": "success"}


async def create_and_send_code(
    phone_number: str,
    telegram_api_id: str,
    telegram_api_hash: str,
    client_type: Literal["on_message", "send_message"],
):
    name = phone_number + "-" + client_type
    client = Client(
        name,
        telegram_api_id,
        telegram_api_hash,
        phone_number=phone_number,
    )
    await client.connect()

    if client_type == "on_message":
        client.add_handler(MessageHandler(new_message))

    if client_type == "on_message":
        await manager.put_on_message_client(phone_number, client)
    elif client_type == "send_message":
        await manager.put_send_message_client(phone_number, client)

    try:
        sent_code = await client.send_code(phone_number)

    except Exception as e:
        logging.error("Error sending code: " + str(e))
        return {"success": False, "error": str(e)}

    logging.info("Sent code to: " + phone_number)
    phone_code_hash = sent_code.phone_code_hash

    return {
        "success": True,
        "phone_code_hash": phone_code_hash,
        "phone_number": phone_number,
    }


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

    response = await create_and_send_code(
        phone_number, telegram_api_id, telegram_api_hash, client_type="on_message"
    )

    return response


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

    response = await create_and_send_code(
        phone_number, telegram_api_id, telegram_api_hash, client_type="send_message"
    )

    return response


async def sign_in_and_start(
    phone_number: str,
    phone_code_hash: str,
    auth_code: str,
    client_type: Literal["on_message", "send_message"],
):
    if client_type == "on_message":
        client = await manager.get_on_message_client(phone_number)
    elif client_type == "send_message":
        client = await manager.get_send_message_client(phone_number)

    await client.sign_in(phone_number, phone_code_hash, auth_code)

    session_string = await client.export_session_string()

    with SQLQueryRunner() as cursor:
        logging.info("Inserting session string into database")

        if client_type == "on_message":
            sql = run_query(
                "insert_on_message_string.sql",
                phone_number=phone_number,
                on_message_string=session_string,
            )
        elif client_type == "send_message":
            sql = run_query(
                "insert_send_message_string.sql",
                phone_number=phone_number,
                send_message_string=session_string,
            )

        cursor.execute(sql)

    loop = asyncio.get_event_loop()
    task = loop.create_task(manager.start_client(client))
    backround_tasks.add(task)

    return {"success": True}


@views.route("/create_string_1", methods=["POST"])
async def create_string_1():
    payload = await request.get_json()

    phone_number = payload.get("phone_number")
    phone_code_hash = payload.get("phone_code_hash")
    auth_code = payload.get("auth_code")

    response = await sign_in_and_start(
        phone_number, phone_code_hash, auth_code, client_type="on_message"
    )

    return response


@views.route("/create_string_2", methods=["POST"])
async def create_string_2():
    payload = await request.get_json()

    phone_number = payload.get("phone_number")
    phone_code_hash = payload.get("phone_code_hash")
    auth_code = payload.get("auth_code")

    response = await sign_in_and_start(
        phone_number, phone_code_hash, auth_code, client_type="send_message"
    )

    # get the pd client id
    with SQLQueryRunner() as cursor:
        logging.info("Selecting phone number")
        sql = run_query("select_phone_number.sql", phone_number=phone_number)
        cursor.execute(sql)

        result = pd.DataFrame(cursor.fetchone(), index=[0]).iloc[0]

    pipedrive_client_id = result["pipedrive_client_id"]

    response["pipedrive_client_id"] = pipedrive_client_id

    return response


@views.route("/api/channels/messages", methods=["POST"])
async def post_message():
    data = await request.form
    data = data.to_dict()

    message = data["message"]
    # sender = data["senderId"]
    sender = "+19735248259"
    recipient = data["recipientIds[]"]
    recipient = "+" + recipient

    message_id = "msg-pd-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    logging.info(f"Incoming message from pipedrive with params {data}")

    _client = await client.connect()
    response = await _client.post_message_to_server(message, sender, recipient, message_id)
    logging.info(f"Response from telegram api: {response}")
    return response
