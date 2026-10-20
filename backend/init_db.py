import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / 'ogong_hardware.db'
SCHEMA_PATH = ROOT_DIR / 'database' / 'ogong_hardware_sqlite.sql'


def init_db(db_path: str | None = None):
    target_db = Path(db_path) if db_path else DB_PATH
    target_db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target_db)
    conn.execute('PRAGMA foreign_keys = ON')

    schema_sql = SCHEMA_PATH.read_text(encoding='utf-8')
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

    return str(target_db)


if __name__ == '__main__':
    print(f'Initializing SQLite database at: {init_db()}')
