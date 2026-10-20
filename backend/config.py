import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / 'ogong_hardware.db'

def get_database_path():
    configured_name = os.environ.get('OGONG_DB_NAME')
    configured_path = os.environ.get('OGONG_DB_PATH')

    if configured_path:
        return configured_path

    if configured_name:
        if os.path.isabs(configured_name):
            return configured_name
        return str(BASE_DIR / configured_name)

    return str(DEFAULT_DB_PATH)


DB_CONFIG = {
    'database': get_database_path(),
    'timeout': 30,
}

SECRET_KEY = os.environ.get('OGONG_SECRET_KEY', 'ogongsecret')
