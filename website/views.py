"""
Routes
"""
import os

from quart import Blueprint, request, render_template

from website.api.channels.util import create_channel

views = Blueprint("views", __name__)


@views.route("/", methods=["GET", "POST"])
async def send_code():
    if request.method == "POST":
        form = await request.form
        phone_number = form.get("phone_number")
        telegram_api_id = form.get("telegram_api_id")
        telegram_api_hash = form.get("telegram_api_hash")
        pipedrive_client_id = form.get("pipedrive_client_id")
        pipedrive_client_secret = form.get("pipedrive_client_secret")

        # make an api call to our Telegram API here
        return "Call our Telegram API"

    else:
        return await render_template("base.html")


@views.route("/create_channel", methods=["GET", "POST"])
async def _create_channel(access_token: str):
    if request.method == "POST":
        form = await request.form
        channel_id = form.get("channel_id")
        provider_type = form.get("provider_type", "other")
        channel_name = form.get("channel_name")

        success = await create_channel(
            access_token, channel_id, channel_name, provider_type
        )

        if success:
            return await render_template("success.html")
        else:
            return await render_template("error.html")

    return await render_template("create_channel.html")
