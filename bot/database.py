# db placeholder
import sqlite3
from datetime import datetime
from pathlib import Path
from .config import DB_PATH

DB_PATH = Path(DB_PATH)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id     INTEGER PRIMARY KEY,
        username    TEXT,
        created_at  TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS gifts (
        id          INTEGER PRIMARY KEY,
        name        TEXT,
        emoji       TEXT,
        stars       INTEGER,
        price       INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER,
        recipient_id    INTEGER,
        gift_id         INTEGER,
        price           INTEGER,
        status          TEXT,      -- created, awaiting_check, ready_to_send, sent, canceled
        created_at      TEXT,
        paid_at         TEXT,
        check_file_id   TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        link    TEXT UNIQUE
    );
    """)

    conn.commit()
    conn.close()


def ensure_user(user_id: int, username: str | None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
            (user_id, username, datetime.utcnow().isoformat())
        )
        conn.commit()
    conn.close()


def get_gifts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gifts ORDER BY id;")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_gift(gift_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gifts WHERE id = ?", (gift_id,))
    row = cur.fetchone()
    conn.close()
    return row


def create_order(user_id: int, recipient_id: int, gift_id: int, price: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (user_id, recipient_id, gift_id, price, status, created_at)
        VALUES (?, ?, ?, ?, 'created', ?)
    """, (user_id, recipient_id, gift_id, price, datetime.utcnow().isoformat()))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def set_order_check(order_id: int, file_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE orders
        SET check_file_id = ?, status = 'ready_to_send', paid_at = ?
        WHERE id = ?
    """, (file_id, datetime.utcnow().isoformat(), order_id))
    conn.commit()
    conn.close()


def get_last_open_order(user_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM orders
        WHERE user_id = ? AND status = 'created'
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_orders_ready_to_send(limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM orders
        WHERE status = 'ready_to_send'
        ORDER BY id ASC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_order_sent(order_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE orders
        SET status = 'sent'
        WHERE id = ?
    """, (order_id,))
    conn.commit()
    conn.close()
