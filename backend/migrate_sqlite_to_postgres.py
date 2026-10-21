import argparse
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from config import DB_CONFIG

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = ROOT_DIR / "ogong_hardware.db"
DEFAULT_BACKUP_DIR = ROOT_DIR / ".backups"
TABLES = (
    "users",
    "categories",
    "suppliers",
    "credit_customers",
    "credit_payments",
    "products",
    "sales",
    "sale_items",
)
TIMESTAMP_COLUMNS = {"created_at", "payment_date", "sale_date"}
NUMERIC_COLUMNS = {
    "total_credit",
    "total_paid",
    "balance",
    "amount_paid",
    "price",
    "cost",
    "total_amount",
    "amount_received",
    "change_amount",
    "subtotal",
}
FOREIGN_KEYS = (
    ("credit_payments", "credit_customer_id", "credit_customers"),
    ("products", "category_id", "categories"),
    ("products", "supplier_id", "suppliers"),
    ("sales", "user_id", "users"),
    ("sale_items", "sale_id", "sales"),
    ("sale_items", "product_id", "products"),
)


def create_sqlite_backup(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup_path = backup_dir / f"{source_path.stem}-{timestamp}{source_path.suffix}"
    with closing(sqlite3.connect(source_path)) as source:
        with closing(sqlite3.connect(backup_path)) as backup:
            source.backup(backup)
    return backup_path


def adapt_value(column: str, value):
    if value is None:
        return None
    if column in TIMESTAMP_COLUMNS and isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    if column in NUMERIC_COLUMNS and isinstance(value, (int, float)):
        return Decimal(str(value))
    return value


def normalize_value(column: str, value):
    if value is None:
        return None
    if column in TIMESTAMP_COLUMNS and isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    if column in NUMERIC_COLUMNS and isinstance(value, (int, float)):
        return Decimal(str(value))
    return value


def apply_schema(conn):
    schema_path = ROOT_DIR / "database" / "ogong_hardware_postgresql.sql"
    for statement in schema_path.read_text(encoding="utf-8").split(";"):
        if statement.strip():
            conn.execute(statement)


def copy_table(source, target, table: str) -> int:
    source_rows = source.execute(f'SELECT * FROM "{table}"').fetchall()
    if not source_rows:
        return 0

    columns = [column[1] for column in source.execute(f'PRAGMA table_info("{table}")')]
    column_sql = sql.SQL(", ").join(sql.Identifier(column) for column in columns)
    insert = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (id) DO NOTHING"
    ).format(
        sql.Identifier("public", table),
        column_sql,
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
    )
    select_row = sql.SQL("SELECT {} FROM {} WHERE id = %s").format(
        column_sql, sql.Identifier("public", table)
    )

    for row in source_rows:
        values = [adapt_value(column, row[column]) for column in columns]
        target.execute(insert, values)
        migrated_row = target.execute(select_row, (row["id"],)).fetchone()
        if migrated_row is None or any(
            normalize_value(column, migrated_row[column])
            != normalize_value(column, row[column])
            for column in columns
        ):
            raise RuntimeError(
                f"Data verification failed for {table} id={row['id']}."
            )
    return len(source_rows)


def verify_foreign_keys(conn):
    for table, column, referenced_table in FOREIGN_KEYS:
        result = conn.execute(
            sql.SQL(
                "SELECT COUNT(*) AS count FROM {} child "
                "LEFT JOIN {} parent ON child.{} = parent.id "
                "WHERE child.{} IS NOT NULL AND parent.id IS NULL"
            ).format(
                sql.Identifier("public", table),
                sql.Identifier("public", referenced_table),
                sql.Identifier(column),
                sql.Identifier(column),
            )
        ).fetchone()
        if result["count"]:
            raise RuntimeError(
                f"Foreign-key verification failed: {table}.{column} has "
                f"{result['count']} orphaned rows."
            )


def reset_sequences(conn):
    for table in TABLES:
        conn.execute(
            sql.SQL(
                "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                "GREATEST(COALESCE(MAX(id), 1), 1), MAX(id) IS NOT NULL) "
                "FROM {}"
            ).format(sql.Identifier("public", table)),
            (f"public.{table}",),
        )
        maximum_id = conn.execute(
            sql.SQL("SELECT MAX(id) AS maximum_id FROM {}").format(
                sql.Identifier("public", table)
            )
        ).fetchone()["maximum_id"]
        sequence_value = conn.execute(
            "SELECT pg_sequence_last_value("
            "pg_get_serial_sequence(%s, 'id')::regclass) AS sequence_value",
            (f"public.{table}",),
        ).fetchone()["sequence_value"]
        if sequence_value != maximum_id:
            raise RuntimeError(f"Identity sequence verification failed for {table}.")


def migrate(sqlite_path: Path, backup_dir: Path, database_url: str | None = None):
    connection_url = database_url or DB_CONFIG["database_url"]
    if not connection_url:
        raise RuntimeError("Set DATABASE_URL before running the migration.")
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")

    backup_path = create_sqlite_backup(sqlite_path, backup_dir)
    print(f"SQLite backup created at: {backup_path}")
    copied_counts = {}
    with closing(sqlite3.connect(sqlite_path)) as source:
        source.row_factory = sqlite3.Row
        with psycopg.connect(
            connection_url,
            connect_timeout=DB_CONFIG["connect_timeout"],
            row_factory=dict_row,
        ) as target:
            apply_schema(target)
            for table in TABLES:
                copied_counts[table] = copy_table(source, target, table)
            reset_sequences(target)
            verify_foreign_keys(target)

            for table, source_count in copied_counts.items():
                target_count = target.execute(
                    sql.SQL("SELECT COUNT(*) AS count FROM {}").format(
                        sql.Identifier("public", table)
                    )
                ).fetchone()["count"]
                print(f"{table}: source={source_count}, PostgreSQL={target_count}")

def main():
    parser = argparse.ArgumentParser(
        description="Back up SQLite and migrate its records to PostgreSQL."
    )
    parser.add_argument(
        "--sqlite",
        type=Path,
        default=DEFAULT_SQLITE_PATH,
        help="SQLite database file (default: project-root ogong_hardware.db).",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Directory for the pre-migration SQLite backup.",
    )
    args = parser.parse_args()
    migrate(args.sqlite.resolve(), args.backup_dir.resolve())


if __name__ == "__main__":
    main()
