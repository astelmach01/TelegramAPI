import logging
import os

from dotenv import load_dotenv
from quart import Quart
from .util import run_query, SQLQueryRunner, get_db

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

conn = get_db()


def create_app():
    app = Quart(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

    from .views import views
    from .auth import auth

    create_database()

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")

    @app.after_serving
    def close_conn():
        conn.close()

    return app


def create_database():

    with SQLQueryRunner(conn) as cursor:
        sql = run_query("create_session_table")
        cursor.execute(sql)
        
    with SQLQueryRunner(conn) as cursor:
        sql = run_query("create_client_credentials_table")
        cursor.execute(sql)
