import os
from jinja2 import Environment, FileSystemLoader
import pymysql
from dotenv import load_dotenv

load_dotenv()

queries_dir = os.path.join(os.getcwd(), 'website', "queries")
print(queries_dir)

# Set up the Jinja environment to load templates from the "/queries" directory
jinja_env = Environment(loader=FileSystemLoader(queries_dir), autoescape=True)


def run_query(file_name: str, **kwargs):
    return jinja_env.get_template(file_name).render(kwargs)


class SQLQueryRunner:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.cursor = self.connection.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Handle any exceptions raised within the context
            print(f"An error occurred: {exc_type} - {exc_val}")
        self.cursor.close()


def connect_to_db():
    # Read environment variables
    db_username = os.environ.get('DB_USERNAME')
    db_password = os.environ.get('DB_PASSWORD')
    db_endpoint = os.environ.get('DB_ENDPOINT')
    db_port = os.environ.get('DB_PORT')

    try:
        # Establish a connection to the MySQL database
        conn = pymysql.connect(
            host=db_endpoint,
            port=int(db_port),
            user=db_username,
            password=db_password,
            database='BASE',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        # Return the connection object
        return conn

    except pymysql.MySQLError as e:
        print("Error connecting to MySQL database:", str(e))
        return None

