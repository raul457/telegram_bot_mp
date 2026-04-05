import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_NAME = "bot_database.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                signup_date TEXT,
                status TEXT,
                expiration_date TEXT,
                plan_type TEXT,
                last_payment_id TEXT
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pending_payments (
                payment_id TEXT PRIMARY KEY,
                telegram_id INTEGER,
                plan_type TEXT,
                amount INTEGER,
                status TEXT,
                created_at TEXT,
                qr_code TEXT,
                qr_code_base64 TEXT,
                ticket_url TEXT
            )
        ''')

def register_user(telegram_id, name, username):
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if not user:
            signup_date = datetime.now().isoformat()
            conn.execute('''
                INSERT INTO users (telegram_id, name, username, signup_date, status, expiration_date, plan_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (telegram_id, name, username, signup_date, "inactive", "", ""))

def activate_subscription(telegram_id, days, plan_type, payment_id):
    expiration_date = (datetime.now() + timedelta(days=days)).isoformat()
    with get_db() as conn:
        conn.execute('''
            UPDATE users 
            SET status = 'active', expiration_date = ?, plan_type = ?, last_payment_id = ?
            WHERE telegram_id = ?
        ''', (expiration_date, plan_type, payment_id, telegram_id))

def get_user(telegram_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()

def get_all_users():
    with get_db() as conn:
        return conn.execute("SELECT * FROM users").fetchall()

def get_active_users():
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE status = 'active' AND expiration_date > ?", 
                           (datetime.now().isoformat(),)).fetchall()

def get_expired_users():
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE status = 'active' AND expiration_date <= ?", 
                           (datetime.now().isoformat(),)).fetchall()

def update_status(telegram_id, status):
    with get_db() as conn:
        conn.execute("UPDATE users SET status = ? WHERE telegram_id = ?", (status, telegram_id))

def save_pending_payment(payment_id, telegram_id, plan_type, amount, qr_data):
    with get_db() as conn:
        conn.execute('''
            INSERT INTO pending_payments (payment_id, telegram_id, plan_type, amount, status, created_at, qr_code, qr_code_base64, ticket_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (payment_id, telegram_id, plan_type, amount, "pending", datetime.now().isoformat(),
              qr_data.get("qr_code", ""), qr_data.get("qr_code_base64", ""), qr_data.get("ticket_url", "")))

def update_payment_status(payment_id, status):
    with get_db() as conn:
        conn.execute("UPDATE pending_payments SET status = ? WHERE payment_id = ?", (status, payment_id))

def get_pending_payment(payment_id):
    with get_db() as conn:
        return conn.execute("SELECT * FROM pending_payments WHERE payment_id = ?", (payment_id,)).fetchone()