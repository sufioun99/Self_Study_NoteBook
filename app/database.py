import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "study.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Materials: stable identity for anything the founder wants to resurface
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            material_type TEXT NOT NULL DEFAULT 'note',
            topic_summary TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            current_version_id INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Immutable versions for snippets and mixed-content edits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            parent_version_id INTEGER,
            version_number INTEGER NOT NULL,
            language TEXT,
            change_note TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            created_by TEXT DEFAULT 'founder',
            test_status TEXT DEFAULT 'untested',
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_version_id) REFERENCES material_versions(id)
        )
    """)

    # Mixed content stored in searchable units
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER NOT NULL,
            block_order INTEGER NOT NULL DEFAULT 0,
            block_type TEXT NOT NULL DEFAULT 'text',
            language TEXT,
            text_content TEXT,
            code_content TEXT,
            alt_text TEXT,
            source_ref TEXT,
            FOREIGN KEY (version_id) REFERENCES material_versions(id) ON DELETE CASCADE
        )
    """)

    # Attachments: images, screenshots, and other linked assets
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            version_id INTEGER,
            file_path TEXT NOT NULL,
            mime_type TEXT,
            caption TEXT,
            alt_text TEXT,
            width INTEGER,
            height INTEGER,
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES material_versions(id)
        )
    """)

    # Shared vocabulary for topics and retrieval
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE,
            tag_type TEXT NOT NULL DEFAULT 'topic'
        )
    """)

    # Primary labeling surface for discovery
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_tags (
            material_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            version_id INTEGER,
            PRIMARY KEY (material_id, tag_id),
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
            FOREIGN KEY (version_id) REFERENCES material_versions(id)
        )
    """)

    # Cross-material resurfacing and topic graph
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS material_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_material_id INTEGER NOT NULL,
            to_material_id INTEGER NOT NULL,
            relation_type TEXT NOT NULL DEFAULT 'related',
            note TEXT,
            strength REAL DEFAULT 1.0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (from_material_id) REFERENCES materials(id) ON DELETE CASCADE,
            FOREIGN KEY (to_material_id) REFERENCES materials(id) ON DELETE CASCADE,
            UNIQUE(from_material_id, to_material_id, relation_type)
        )
    """)

    # Reusable discovery entry points
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            query TEXT NOT NULL,
            filters TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Feedback loop for ranking and future improvements
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            clicked_material_id INTEGER,
            no_result_flag INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (clicked_material_id) REFERENCES materials(id)
        )
    """)

    # Add searchable_text column to materials if it doesn't exist
    try:
        cursor.execute("ALTER TABLE materials ADD COLUMN searchable_text TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # FTS5 virtual table for full-text search across materials
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS materials_fts USING fts5(
            title,
            topic_summary,
            searchable_text,
            content='materials',
            content_rowid='id'
        )
    """)

    # Triggers to keep FTS index in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS materials_ai AFTER INSERT ON materials BEGIN
            INSERT INTO materials_fts(rowid, title, topic_summary, searchable_text)
            VALUES (new.id, new.title, new.topic_summary, new.searchable_text);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS materials_ad AFTER DELETE ON materials BEGIN
            INSERT INTO materials_fts(materials_fts, rowid, title, topic_summary, searchable_text)
            VALUES ('delete', old.id, old.title, old.topic_summary, old.searchable_text);
        END
    """)

    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS materials_au AFTER UPDATE ON materials BEGIN
            INSERT INTO materials_fts(materials_fts, rowid, title, topic_summary, searchable_text)
            VALUES ('delete', old.id, old.title, old.topic_summary, old.searchable_text);
            INSERT INTO materials_fts(rowid, title, topic_summary, searchable_text)
            VALUES (new.id, new.title, new.topic_summary, new.searchable_text);
        END
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
