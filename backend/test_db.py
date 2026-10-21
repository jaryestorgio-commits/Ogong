import psycopg
from psycopg.rows import dict_row

from config import DB_CONFIG


def main():
    database_url = DB_CONFIG["database_url"]
    if not database_url:
        raise RuntimeError("DATABASE_URL is required to test PostgreSQL connectivity.")

    with psycopg.connect(
        database_url,
        connect_timeout=DB_CONFIG["connect_timeout"],
        row_factory=dict_row,
    ) as conn:
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        ).fetchall()

    print("Connected to PostgreSQL.")
    print("Tables:", [row["table_name"] for row in tables])


if __name__ == "__main__":
    main()
