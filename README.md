# OGONG HARDWARE MANAGEMENT SYSTEM

A simple full-stack hardware store management and POS system.

## Structure

- `frontend/` - HTML, CSS, JavaScript UI
- `backend/` - Flask REST API and PostgreSQL database tools
- `database/` - SQLite and PostgreSQL schema files

## PostgreSQL setup

Install PostgreSQL and create an empty database, for example:

```sql
CREATE DATABASE ogong_hardware;
```

Copy `.env.example` to `.env` and set `DATABASE_URL` to your local PostgreSQL
connection string. Keep `.env` private and use the hosted database's connection
string in the deployment platform's environment settings, not in source code.
For example:

```text
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/ogong_hardware
OGONG_SECRET_KEY=<a-unique-random-secret>
```

The backend loads `.env` for local development. Production hosts such as Render
should provide `DATABASE_URL` and `OGONG_SECRET_KEY` as environment variables.
The application does not fall back to SQLite. Application tables use
PostgreSQL's `public` schema, matching the SQLite migration.

## Install and run locally

```bash
python -m pip install -r requirements.txt
python backend/init_db.py
python backend/app.py
```

Open `http://127.0.0.1:5000/` to use the application. The schema initializer is
safe to rerun and does not drop tables or seed/reset records.

## Migrate existing SQLite data

Set `DATABASE_URL` in `.env` (or the current shell) to the PostgreSQL database
that will receive the existing records. From the repository root, run:

```bash
python backend/migrate_sqlite_to_postgres.py
```

This command creates a consistent backup under `.backups/` before connecting
to PostgreSQL, applies the PostgreSQL schema, copies all eight SQLite tables
while preserving IDs, verifies copied records and foreign-key relationships,
and resets identity sequences. It is safe to rerun against the same target:
rows with existing IDs are not duplicated or overwritten, and conflicting
records fail verification instead of being silently changed.

To use another SQLite file:

```bash
python backend/migrate_sqlite_to_postgres.py --sqlite path/to/ogong_hardware.db
```

The original SQLite database is never modified or removed.

## Production startup

The included `Procfile` starts the Flask API with Gunicorn. For Render, deploy
the repository root as a Web Service and configure:

- Root Directory: `.`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --chdir backend app:app`
- Health Check Path: `/api/health`
- `DATABASE_URL`: the Render PostgreSQL connection string (prefer the internal
  connection string when the services are in the same region)
- `OGONG_SECRET_KEY`: a unique secret generated in Render's environment settings
- `OGONG_FRONTEND_ORIGINS`: `https://ogong-1.onrender.com` (no trailing
  slash). Separate multiple allowed origins with commas.

Deploy `frontend/` as a Render Static Site with Root Directory `frontend`,
Build Command `echo "No build step"`, and Publish Directory `.`. Its JavaScript
is configured to call
`https://pos-system-el4v.onrender.com/api`. The API health check is available
at `https://pos-system-el4v.onrender.com/api/health` and reports database
connectivity and whether the required tables exist. If it reports missing
tables, run `python backend/init_db.py` with the Render `DATABASE_URL` before
using the API. Do not commit `.env` or production credentials.
