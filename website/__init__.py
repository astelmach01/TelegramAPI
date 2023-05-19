import os

from dotenv import load_dotenv
from quart import Quart, redirect, render_template, request


load_dotenv()


def create_app():

    app = Quart(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")

    return app
