import os
import sqlite3
import json
from typing import Optional, Any, Dict


def _db_path() -> str:
    return os.getenv("DATABASE_PATH", "database.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_username TEXT NOT NULL,
            post_id INTEGER NOT NULL,
            post_date TEXT NOT NULL,
            post_text TEXT,
            is_event INTEGER DEFAULT 0,
            extracted_data TEXT,
            processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            sent_to_bot INTEGER DEFAULT 0,
            UNIQUE(channel_username, post_id)
        );
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_processed_posts_channel_post
        ON processed_posts(channel_username, post_id);
        """
    )
    conn.commit()
    conn.close()


def is_post_processed(channel_username: str, post_id: int) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM processed_posts WHERE channel_username = ? AND post_id = ?",
        (channel_username, post_id),
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_processed_post(
    channel_username: str,
    post_id: int,
    post_date: str,
    post_text: str,
    is_event: bool,
    extracted_data: Optional[Dict[str, Any]] = None,
) -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO processed_posts (
            channel_username, post_id, post_date, post_text, is_event, extracted_data, sent_to_bot
        ) VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (
            channel_username,
            post_id,
            post_date,
            post_text,
            1 if is_event else 0,
            json.dumps(extracted_data or {}, ensure_ascii=False),
        ),
    )
    conn.commit()
    conn.close()


def mark_as_sent(channel_username: str, post_id: int) -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE processed_posts SET sent_to_bot = 1 WHERE channel_username = ? AND post_id = ?",
        (channel_username, post_id),
    )
    conn.commit()
    conn.close()

