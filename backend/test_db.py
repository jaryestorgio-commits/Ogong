import sqlite3
import traceback
import importlib.util
from pathlib import Path


config_path = Path(__file__).resolve().parent / "config.py"
spec = importlib.util.spec_from_file_location("backend_config", str(config_path))
config = importlib.util.module_from_spec(spec)  # type: ignore
assert spec is not None
assert spec.loader is not None
spec.loader.exec_module(config)
DB_CONFIG = config.DB_CONFIG

print("DB config:", DB_CONFIG)

try:
    conn = sqlite3.connect(DB_CONFIG['database'])
    conn.row_factory = sqlite3.Row
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    print('Connected OK')
    print('Tables:', [row[0] for row in tables])
    conn.close()
except Exception as e:
    print('Connection failed:', type(e).__name__, str(e))
    traceback.print_exc()
