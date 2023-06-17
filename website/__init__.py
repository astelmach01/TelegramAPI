import logging
import os

from quart import Quart
from .util import run_query, SQLQueryRunner, get_db
from rabbit_mq.send import client


conn = get_db()


def create_app():
    app = Quart(__name__)
    app.config["SECRET_KEY"] = os.getenv("APP_SECRET_KEY")

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")

    @app.after_serving
    def close_conn():
        conn.close()

    @app.errorhandler(404)
    async def not_found(e):
        return "This page has not been found", 404

    create_database()
    client.connect()

    return app


def create_database():
    logging.info("Creating session table")

    with SQLQueryRunner(conn) as cursor:
        sql = "DROP TABLE IF EXISTS sessions;"
        cursor.execute(sql)

        sql = run_query("create_session_table.sql")
        cursor.execute(sql)

    logging.info("Creating client credentials table")

    with SQLQueryRunner(conn) as cursor:
        sql = "DROP TABLE IF EXISTS telegram_credentials;"
        cursor.execute(sql)

        sql = run_query("create_client_credentials_table.sql")
        cursor.execute(sql)
