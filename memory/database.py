"""Simple SQLite-backed memory for BORO BHAI."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

DEFAULT_DB_PATH = os.path.join("data", "boro_bhai.db")


def _ensure_parent_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def initialize_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create the SQLite database and required table if missing."""
    _ensure_parent_dir(db_path)
    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            agent_response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def save_memory(user_input: str, agent_response: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """Persist a user input and agent response in SQLite."""
    if not user_input or not agent_response:
        raise ValueError("Both user_input and agent_response are required.")

    connection = initialize_db(db_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    cursor = connection.execute(
        "INSERT INTO interactions (user_input, agent_response, timestamp) VALUES (?, ?, ?)",
        (user_input, agent_response, timestamp),
    )
    connection.commit()
    connection.close()
    return int(cursor.lastrowid)


def get_recent_memories(limit: int = 5, db_path: str = DEFAULT_DB_PATH):
    """Return recent interactions in reverse chronological order."""
    if limit <= 0:
        return []

    connection = initialize_db(db_path)
    rows = connection.execute(
        "SELECT user_input, agent_response, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    connection.close()

    memories = []
    for user_input, agent_response, timestamp in rows:
        memories.append(
            {
                "user_input": user_input,
                "agent_response": agent_response,
                "timestamp": timestamp,
            }
        )
    return memories
