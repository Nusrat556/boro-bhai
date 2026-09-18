"""Simple SQLite-backed memory for BORO BHAI."""

from __future__ import annotations

import os
import re
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
            session_id TEXT NOT NULL DEFAULT 'default',
            user_input TEXT NOT NULL,
            agent_response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )

    columns = connection.execute("PRAGMA table_info(interactions)").fetchall()
    has_session_id = any(column[1] == "session_id" for column in columns)
    if not has_session_id:
        connection.execute("ALTER TABLE interactions ADD COLUMN session_id TEXT NOT NULL DEFAULT 'default'")

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_interactions_session_id ON interactions (session_id)"
    )
    connection.commit()
    return connection


def _normalize_session_id(session_id: str | None) -> str:
    value = (session_id or "default").strip()
    return value or "default"


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip().lower()


def save_memory(user_input: str, agent_response: str, db_path: str = DEFAULT_DB_PATH, session_id: str | None = None) -> int:
    """Persist a user input and agent response in SQLite."""
    if not user_input or not agent_response:
        raise ValueError("Both user_input and agent_response are required.")

    normalized_session_id = _normalize_session_id(session_id)
    connection = initialize_db(db_path)
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        cursor = connection.execute(
            "INSERT INTO interactions (session_id, user_input, agent_response, timestamp) VALUES (?, ?, ?, ?)",
            (normalized_session_id, user_input, agent_response, timestamp),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_recent_memories(limit: int = 5, db_path: str = DEFAULT_DB_PATH, session_id: str | None = None):
    """Return recent interactions in reverse chronological order."""
    if limit <= 0:
        return []

    session_key = _normalize_session_id(session_id)
    connection = initialize_db(db_path)
    try:
        if session_id is not None:
            rows = connection.execute(
                "SELECT user_input, agent_response, timestamp FROM interactions WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_key, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT user_input, agent_response, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    finally:
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


def get_relevant_context(query: str, limit: int = 5, db_path: str = DEFAULT_DB_PATH, session_id: str | None = None):
    """Return recent memories that are most relevant to the current task."""
    if not query or not query.strip() or limit <= 0:
        return []

    memories = get_recent_memories(limit=max(limit, 5), db_path=db_path, session_id=session_id)
    if not memories:
        return []

    normalized_query = set(re.findall(r"[A-Za-z0-9]+", _normalize_text(query)))
    if not normalized_query:
        return memories[:limit]

    scored_memories = []
    for memory in memories:
        combined_text = f"{memory['user_input']} {memory['agent_response']}"
        tokens = set(re.findall(r"[A-Za-z0-9]+", _normalize_text(combined_text)))
        score = len(normalized_query & tokens)
        if score > 0:
            scored_memories.append((score, memory))

    if scored_memories:
        scored_memories.sort(key=lambda item: (-item[0], item[1]["timestamp"]), reverse=True)
        return [memory for _, memory in scored_memories[:limit]]

    return memories[:limit]
