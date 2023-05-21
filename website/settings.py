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
    handlers=[
        logging.StreamHandler()
    ]
)

region_name = "us-east-2"

# Create a Secrets Manager client
session = boto3.session.Session()
client = session.client(
    service_name='secretsmanager',
    region_name=region_name
)

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

    class Config:
        env_file = ".env"


settings = Settings()
