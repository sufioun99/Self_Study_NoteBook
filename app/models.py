import sqlite3
from datetime import datetime
from .database import get_db


def create_material(title, material_type="note", topic_summary=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO materials (title, material_type, topic_summary) VALUES (?, ?, ?)",
        (title, material_type, topic_summary),
    )
    db.commit()
    material_id = cursor.lastrowid
    db.close()
    return get_material(material_id)


def get_material(material_id):
    db = get_db()
    row = db.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def list_materials(limit=50, offset=0):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM materials ORDER BY updated_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def update_material(material_id, **kwargs):
    db = get_db()
    sets = []
    vals = []
    for key in ("title", "material_type", "topic_summary", "status", "current_version_id"):
        if key in kwargs and kwargs[key] is not None:
            sets.append(f"{key} = ?")
            vals.append(kwargs[key])
    if sets:
        sets.append("updated_at = datetime('now')")
        vals.append(material_id)
        db.execute(f"UPDATE materials SET {', '.join(sets)} WHERE id = ?", vals)
        db.commit()
    db.close()
    return get_material(material_id)


def delete_material(material_id):
    db = get_db()
    db.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    db.commit()
    db.close()


def create_version(material_id, parent_version_id=None, version_number=1,
                   language=None, change_note=None, test_status="untested"):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO material_versions
           (material_id, parent_version_id, version_number, language, change_note, test_status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (material_id, parent_version_id, version_number, language, change_note, test_status),
    )
    db.commit()
    version_id = cursor.lastrowid
    # Update material's current_version_id
    db.execute(
        "UPDATE materials SET current_version_id = ?, updated_at = datetime('now') WHERE id = ?",
        (version_id, material_id),
    )
    db.commit()
    db.close()
    return get_version(version_id)


def get_version(version_id):
    db = get_db()
    row = db.execute("SELECT * FROM material_versions WHERE id = ?", (version_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def list_versions(material_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM material_versions WHERE material_id = ? ORDER BY version_number ASC",
        (material_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_version_chain(material_id):
    db = get_db()
    rows = db.execute(
        """SELECT * FROM material_versions
           WHERE material_id = ?
           ORDER BY version_number ASC""",
        (material_id,),
    ).fetchall()
    db.close()
    chain = []
    for row in rows:
        v = dict(row)
        v["blocks"] = list_blocks(v["id"])
        chain.append(v)
    return chain


def create_block(version_id, block_order=0, block_type="text", language=None,
                 text_content=None, code_content=None, alt_text=None, source_ref=None):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO material_blocks
           (version_id, block_order, block_type, language, text_content, code_content, alt_text, source_ref)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (version_id, block_order, block_type, language, text_content, code_content, alt_text, source_ref),
    )
    db.commit()
    block_id = cursor.lastrowid

    # Update the material's searchable_text FTS column
    version = get_version(version_id)
    if version:
        material_id = version["material_id"]
        # Rebuild searchable_text from all blocks across all versions
        all_blocks = db.execute(
            """SELECT b.text_content, b.code_content, b.alt_text
               FROM material_blocks b
               JOIN material_versions v ON b.version_id = v.id
               WHERE v.material_id = ?""",
            (material_id,),
        ).fetchall()
        searchable = " ".join(
            (b["text_content"] or "") + " " + (b["code_content"] or "") + " " + (b["alt_text"] or "")
            for b in all_blocks
        ).strip()
        db.execute(
            "UPDATE materials SET searchable_text = ? WHERE id = ?",
            (searchable, material_id),
        )
        # Rebuild FTS entry
        material = db.execute("SELECT title, topic_summary FROM materials WHERE id = ?", (material_id,)).fetchone()
        db.execute(
            "INSERT INTO materials_fts(materials_fts, rowid, title, topic_summary, searchable_text) VALUES ('delete', ?, ?, ?, ?)",
            (material_id, material["title"], material["topic_summary"], ""),
        )
        db.execute(
            "INSERT INTO materials_fts(rowid, title, topic_summary, searchable_text) VALUES (?, ?, ?, ?)",
            (material_id, material["title"], material["topic_summary"], searchable),
        )
        db.commit()

    db.close()
    return get_block(block_id)


def get_block(block_id):
    db = get_db()
    row = db.execute("SELECT * FROM material_blocks WHERE id = ?", (block_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def list_blocks(version_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM material_blocks WHERE version_id = ? ORDER BY block_order ASC",
        (version_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def create_tag(name, slug=None, tag_type="topic"):
    db = get_db()
    if slug is None:
        slug = name.lower().replace(" ", "-")
    try:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO tags (name, slug, tag_type) VALUES (?, ?, ?)",
            (name, slug, tag_type),
        )
        db.commit()
        tag_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        row = db.execute("SELECT id FROM tags WHERE slug = ?", (slug,)).fetchone()
        tag_id = row["id"] if row else None
    db.close()
    return get_tag(tag_id) if tag_id else None


def get_tag(tag_id):
    db = get_db()
    row = db.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
    db.close()
    return dict(row) if row else None


def list_tags():
    db = get_db()
    rows = db.execute("SELECT * FROM tags ORDER BY name ASC").fetchall()
    db.close()
    return [dict(r) for r in rows]


def tag_material(material_id, tag_id, version_id=None):
    db = get_db()
    try:
        db.execute(
            "INSERT OR IGNORE INTO material_tags (material_id, tag_id, version_id) VALUES (?, ?, ?)",
            (material_id, tag_id, version_id),
        )
        db.commit()
    finally:
        db.close()


def untag_material(material_id, tag_id):
    db = get_db()
    db.execute(
        "DELETE FROM material_tags WHERE material_id = ? AND tag_id = ?",
        (material_id, tag_id),
    )
    db.commit()
    db.close()


def get_material_tags(material_id):
    db = get_db()
    rows = db.execute(
        """SELECT t.* FROM tags t
           JOIN material_tags mt ON t.id = mt.tag_id
           WHERE mt.material_id = ?""",
        (material_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def create_relation(from_material_id, to_material_id, relation_type="related", note=None, strength=1.0):
    db = get_db()
    try:
        db.execute(
            """INSERT INTO material_relations
               (from_material_id, to_material_id, relation_type, note, strength)
               VALUES (?, ?, ?, ?, ?)""",
            (from_material_id, to_material_id, relation_type, note, strength),
        )
        db.commit()
    except sqlite3.IntegrityError:
        pass
    db.close()


def get_relations(material_id):
    db = get_db()
    rows = db.execute(
        """SELECT m.id, m.title, m.material_type, mr.relation_type, mr.note, mr.strength
           FROM material_relations mr
           JOIN materials m ON mr.to_material_id = m.id
           WHERE mr.from_material_id = ?
           ORDER BY mr.strength DESC""",
        (material_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def search_materials(query, limit=20, offset=0):
    db = get_db()
    rows = db.execute(
        """SELECT m.*, rank
           FROM materials_fts fts
           JOIN materials m ON fts.rowid = m.id
           WHERE materials_fts MATCH ?
           ORDER BY rank
           LIMIT ? OFFSET ?""",
        (query, limit, offset),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def search_suggestions(query, limit=10):
    db = get_db()
    rows = db.execute(
        """SELECT m.id, m.title, m.topic_summary, rank
           FROM materials_fts fts
           JOIN materials m ON fts.rowid = m.id
           WHERE materials_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (query, limit),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def rebuild_fts_index():
    """Rebuild the entire FTS index from scratch."""
    db = get_db()
    db.execute("DELETE FROM materials_fts")
    materials = db.execute("SELECT id, title, topic_summary, searchable_text FROM materials").fetchall()
    for m in materials:
        db.execute(
            "INSERT INTO materials_fts(rowid, title, topic_summary, searchable_text) VALUES (?, ?, ?, ?)",
            (m["id"], m["title"], m["topic_summary"] or "", m["searchable_text"] or ""),
        )
    db.commit()
    db.close()


def log_search_event(query, clicked_material_id=None, no_result=False):
    db = get_db()
    db.execute(
        "INSERT INTO search_events (query, clicked_material_id, no_result_flag) VALUES (?, ?, ?)",
        (query, clicked_material_id, 1 if no_result else 0),
    )
    db.commit()
    db.close()


def get_recent_materials(limit=10):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM materials ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def get_related_materials(material_id, limit=5):
    db = get_db()
    rows = db.execute(
        """SELECT m.* FROM materials m
           JOIN material_tags mt ON m.id = mt.material_id
           JOIN material_tags mt2 ON mt.tag_id = mt2.tag_id
           WHERE mt2.material_id = ? AND m.id != ?
           GROUP BY m.id
           ORDER BY COUNT(*) DESC
           LIMIT ?""",
        (material_id, material_id, limit),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]
