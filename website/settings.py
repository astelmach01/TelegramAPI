import json
import logging
import os

import boto3
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

region_name = "us-east-2"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    raise Exception(
        "AWS_ACCESS_KEY or AWS_SECRET_ACCESS_KEY not found in environment variables"
    )

else:
    # Create a Secrets Manager client
    session = boto3.session.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

client = session.client(service_name="secretsmanager", region_name=region_name)

# Configure secret cache
cache_config = SecretCacheConfig()
cache = SecretCache(config=cache_config, client=client)
secrets: dict = json.loads(cache.get_secret_string(os.getenv("SECRET_NAME")))


def get_secret(secret_name: str):
    return secrets.get(secret_name)


class Settings(BaseSettings):
    db_username: str = get_secret("username")
    db_password: str = get_secret("password")
    db_endpoint: str
    db_port: int
    TELEGRAM_API_ID: str
    TELEGRAM_API_HASH: str
    ENVIRONMENT: str
    PORT: int

    class Config:
        env_file = ".env"


settings = Settings()
