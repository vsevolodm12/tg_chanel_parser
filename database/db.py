import os
import sqlite3
import json
from typing import Optional, Any, Dict, List


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
    # Таблица для хранения пользователей бота
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bot_users (
            chat_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
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


def get_last_events(limit: int = 5) -> list:
    """Получить последние N событий (постов где is_event = 1)"""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT channel_username, post_id, post_text, extracted_data, post_date
        FROM processed_posts
        WHERE is_event = 1 AND sent_to_bot = 1
        ORDER BY processed_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    
    events = []
    for row in rows:
        extracted_data = json.loads(row["extracted_data"]) if row["extracted_data"] else {}
        
        # Пропускаем события без полезных данных (дайджесты и т.д.)
        has_useful_data = any([
            extracted_data.get("title"),
            extracted_data.get("date"),
            extracted_data.get("place"),
            extracted_data.get("link"),
            extracted_data.get("description")
        ])
        
        if not has_useful_data:
            continue
        
        events.append({
            "channel": row["channel_username"],
            "post_id": row["post_id"],
            "title": extracted_data.get("title") or "Без названия",
            "text": row["post_text"],
            "data": extracted_data,
            "date": row["post_date"],
        })
    return events


def add_bot_user(chat_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> None:
    """Добавить пользователя бота в БД"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO bot_users (chat_id, username, first_name)
        VALUES (?, ?, ?)
        """,
        (chat_id, username, first_name),
    )
    conn.commit()
    conn.close()


def get_all_bot_users() -> List[Dict[str, Any]]:
    """Получить список всех пользователей бота"""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM bot_users")
    rows = cur.fetchall()
    conn.close()
    return [{"chat_id": row["chat_id"]} for row in rows]

