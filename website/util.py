import logging
import os
from dotenv import load_dotenv

import pymysql
import pymysql.cursors
from jinja2 import Environment, FileSystemLoader

from website.settings import settings

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

queries_dir = os.path.join(os.getcwd(), "website", "queries")

# Set up the Jinja environment to load templates from the "/queries" directory
jinja_env = Environment(loader=FileSystemLoader(queries_dir), autoescape=True)

db = None


def run_query(file_name: str, **kwargs):
    return jinja_env.get_template(file_name).render(kwargs)


class SQLQueryRunner:
    def __init__(self, connection=None):
        if connection is None:
            connection = get_db()

        self.connection = connection

    def __enter__(self):
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Handle any exceptions raised within the context
            logging.error(f"An error occurred: {exc_type} - {exc_val}")
        self.cursor.close()


def get_db():
    global db
    if db is not None:
        return db

    # Read environment variables
    db_username = settings.db_username
    db_password = settings.db_password
    db_endpoint = settings.db_endpoint
    db_port = settings.db_port

    try:
        conn = pymysql.connect(
            host=db_endpoint,
            port=db_port,
            user=db_username,
            password=db_password,
            database="BASE",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

        logging.info("Connected to the database")

        db = conn

        # Return the connection object
        return conn

    except pymysql.MySQLError as e:
        logging.error("Error connecting to MySQL database: %s", str(e))
        return None


def remove_session_files():
    base_directory = os.getcwd()
    files_to_remove = []

    for file_name in os.listdir(base_directory):
        if file_name.endswith(".session") or file_name.endswith(".session-journal"):
            files_to_remove.append(file_name)

    for file_name in files_to_remove:
        file_path = os.path.join(base_directory, file_name)
        os.remove(file_path)
        print(f"Removed file: {file_path}")
