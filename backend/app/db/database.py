"""SQLite database connection and schema management."""

from __future__ import annotations

import aiosqlite

from app.config import settings

_DB_PATH = str(settings.DB_PATH)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    source_image TEXT,
    parse_result_json TEXT,
    current_params_json TEXT NOT NULL,
    customization_json TEXT NOT NULL,
    latest_build_id TEXT,
    budget_result_json TEXT,
    validation_result_json TEXT
);

CREATE TABLE IF NOT EXISTS builds (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    params_json TEXT NOT NULL,
    validation_json TEXT,
    stl_path TEXT,
    glb_path TEXT
);
"""


async def get_db() -> aiosqlite.Connection:
    """Get an aiosqlite connection."""
    db = await aiosqlite.connect(_DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    """Initialize database schema."""
    db = await aiosqlite.connect(_DB_PATH)
    await db.executescript(SCHEMA_SQL)
    await db.commit()
    await db.close()
