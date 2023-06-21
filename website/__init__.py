import logging
import os

from quart import Quart
from .util import run_query, SQLQueryRunner, get_db

conn = get_db()


def create_app():
    app = Quart(__name__)
    app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY")

    from .views import views
    from .auth import auth
    from .api.messages import messages_route
    from .api.conversations import conversations_route

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(messages_route, url_prefix="/api/messages")
    app.register_blueprint(conversations_route, url_prefix="/api/conversations")

    create_database()

    return app


def create_database():
    logging.info("Creating session table")

    with SQLQueryRunner(conn) as cursor:
        sql = run_query("create_session_table.sql")
        cursor.execute(sql)

    logging.info("Creating client credentials table")

    with SQLQueryRunner(conn) as cursor:
        sql = run_query("create_client_credentials_table.sql")
        cursor.execute(sql)
