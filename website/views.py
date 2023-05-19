"""
Routes
"""
import os

from quart import Blueprint, request, render_template

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

