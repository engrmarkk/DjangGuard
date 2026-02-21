import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))
CACHE_REDIS_URL = os.getenv("CACHE_REDIS_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
