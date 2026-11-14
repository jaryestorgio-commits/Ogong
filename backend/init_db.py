from pathlib import Path

import psycopg
from psycopg import sql

from config import DB_CONFIG, DB_SCHEMA

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT_DIR / "database" / "ogong_hardware_postgresql.sql"


def init_db():
    database_url = DB_CONFIG["database_url"]
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to initialize PostgreSQL.")

    with psycopg.connect(
        database_url,
        connect_timeout=DB_CONFIG["connect_timeout"],
        options=f"-c search_path={DB_SCHEMA}",
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(DB_SCHEMA)
                )
            )
            cursor.execute(
                sql.SQL("SET search_path TO {}").format(
                    sql.Identifier(DB_SCHEMA)
                )
            )
            for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    cursor.execute(statement)

if __name__ == "__main__":
    init_db()
    print("PostgreSQL schema initialized.")
