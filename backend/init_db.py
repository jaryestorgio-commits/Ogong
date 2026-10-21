from pathlib import Path

import psycopg

from config import DB_CONFIG

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT_DIR / "database" / "ogong_hardware_postgresql.sql"


def init_db():
    database_url = DB_CONFIG["database_url"]
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to initialize PostgreSQL.")

    with psycopg.connect(database_url, connect_timeout=DB_CONFIG["connect_timeout"]) as conn:
        with conn.cursor() as cursor:
            for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    cursor.execute(statement)


if __name__ == "__main__":
    init_db()
    print("PostgreSQL schema initialized.")
