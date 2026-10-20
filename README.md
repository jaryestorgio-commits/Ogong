# OGONG HARDWARE MANAGEMENT SYSTEM

A simple full-stack hardware store management and POS system.

## Structure

- `frontend/` - HTML, CSS, JavaScript UI
- `backend/` - Flask REST API
- `database/` - MySQL setup script

## Setup

1. Install Python and MySQL.
2. Start the MySQL service.
   - On Windows, start the MySQL server from Services, XAMPP, or MySQL Workbench.
   - Verify port 3306 is listening.
3. Create the database using `database/ogong_hardware.sql`.
4. Update `backend/config.py` with MySQL credentials if needed.
   - `host`: `127.0.0.1`
   - `port`: `3306`
   - `user`: your MySQL user
   - `password`: your MySQL password
   - `db`: `ogong_hardware`
5. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

6. Run backend:

   ```bash
   python backend/app.py
   ```

7. Open `frontend/index.html` in the browser or browse to `http://127.0.0.1:5000/`.
