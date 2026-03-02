"""Database CRUD operations for projects and builds."""

from __future__ import annotations

import json
from typing import Optional

import aiosqlite

from .database import get_db


async def create_project(
    project_id: str,
    source_image: Optional[str],
    parse_result_json: Optional[str],
    current_params_json: str,
    customization_json: str,
) -> None:
    """Insert a new project."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO projects (id, source_image, parse_result_json, current_params_json, customization_json)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, source_image, parse_result_json, current_params_json, customization_json),
        )
        await db.commit()
    finally:
        await db.close()


async def get_project(project_id: str) -> Optional[dict]:
    """Fetch a project by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        await db.close()


async def update_project(project_id: str, **fields) -> None:
    """Update specific fields on a project."""
    db = await get_db()
    try:
        set_clauses = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [project_id]
        await db.execute(f"UPDATE projects SET {set_clauses} WHERE id = ?", values)
        await db.commit()
    finally:
        await db.close()


async def create_build(
    build_id: str,
    project_id: str,
    params_json: str,
    validation_json: Optional[str] = None,
    stl_path: Optional[str] = None,
    glb_path: Optional[str] = None,
) -> None:
    """Insert a new build record."""
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO builds (id, project_id, params_json, validation_json, stl_path, glb_path)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (build_id, project_id, params_json, validation_json, stl_path, glb_path),
        )
        await db.commit()
    finally:
        await db.close()


async def get_build(build_id: str) -> Optional[dict]:
    """Fetch a build by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM builds WHERE id = ?", (build_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        await db.close()
