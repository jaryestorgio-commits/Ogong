import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip() or None
DB_CONFIG = {
    "database_url": DATABASE_URL,
    "connect_timeout": 10,
}

SECRET_KEY = os.environ.get("OGONG_SECRET_KEY")
