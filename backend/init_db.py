from pathlib import Path

import psycopg

from config import DB_CONFIG

ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT_DIR / "database" / "ogong_hardware_postgresql.sql"
REQUIRED_TABLES = {
    "categories",
    "products",
    "sale_items",
    "sales",
    "suppliers",
    "users",
}


def init_db():
    database_url = DB_CONFIG["database_url"]
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to initialize PostgreSQL.")

    with psycopg.connect(database_url, connect_timeout=DB_CONFIG["connect_timeout"]) as conn:
        with conn.cursor() as cursor:
            for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    cursor.execute(statement)

            cursor.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = current_schema() "
                "AND table_name = ANY(%s)",
                (list(REQUIRED_TABLES),),
            )
            existing_tables = {row[0] for row in cursor.fetchall()}

    missing_tables = REQUIRED_TABLES - existing_tables
    if missing_tables:
        raise RuntimeError(
            "PostgreSQL schema initialization did not create required tables: "
            + ", ".join(sorted(missing_tables))
        )


if __name__ == "__main__":
    init_db()
    print("PostgreSQL schema initialized.")
