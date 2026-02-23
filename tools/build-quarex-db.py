#!/usr/bin/env python3
"""
Quarex Catalog Database Builder
Scans all Quarex JSON files and builds a normalized SQLite database.

Usage:
    python build-quarex-db.py

Output:
    database/quarex-catalog.db
"""

import json
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Configuration
BASE_PATH = Path(r"E:\projects\websites\Quarex")
DB_PATH = BASE_PATH / "database" / "quarex-catalog.db"
TAG_VOCAB_PATH = BASE_PATH / "libraries" / "_utils" / "tag-vocabulary.json"
CURRICULUM_PATH = BASE_PATH / "publicstudies" / "curriculum-index.json"

LIBRARY_PATHS = [
    BASE_PATH / "libraries" / "event-libraries",
    BASE_PATH / "libraries" / "geography-libraries",
    BASE_PATH / "libraries" / "infrastructure-libraries",
    BASE_PATH / "libraries" / "knowledge-libraries",
    BASE_PATH / "libraries" / "perspectives-libraries",
    BASE_PATH / "libraries" / "politician-libraries",
    BASE_PATH / "libraries" / "practical-libraries",
    BASE_PATH / "libraries" / "questions-libraries",
]

# Stats tracking
stats = {
    "files_processed": 0,
    "files_skipped": 0,
    "library_types": 0,
    "libraries": 0,
    "shelves": 0,
    "books": 0,
    "chapters": 0,
    "tags": 0,
    "chapter_tags": 0,
    "curricula": 0,
    "errors": []
}


def create_database(conn):
    """Create database schema with tables, indexes, and views."""
    cursor = conn.cursor()

    # Drop existing tables (for clean rebuild)
    tables = ['chapter_tags', 'chapters', 'books', 'shelves', 'libraries',
              'library_types', 'tags', 'curricula', 'curriculum_courses']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # Create tables
    cursor.execute("""
        CREATE TABLE library_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE libraries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            library_type_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT,
            description TEXT,
            FOREIGN KEY (library_type_id) REFERENCES library_types(id),
            UNIQUE(library_type_id, name)
        )
    """)

    cursor.execute("""
        CREATE TABLE shelves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            library_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            slug TEXT,
            FOREIGN KEY (library_id) REFERENCES libraries(id),
            UNIQUE(library_id, name)
        )
    """)

    cursor.execute("""
        CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shelf_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_by TEXT,
            file_path TEXT,
            file_modified TEXT,
            file_size_bytes INTEGER,
            FOREIGN KEY (shelf_id) REFERENCES shelves(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            label TEXT,
            tier TEXT,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE chapter_tags (
            chapter_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (chapter_id, tag_id),
            FOREIGN KEY (chapter_id) REFERENCES chapters(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE curricula (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curriculum_id TEXT UNIQUE NOT NULL,
            school TEXT,
            title TEXT NOT NULL,
            icon TEXT,
            description TEXT,
            lang TEXT DEFAULT 'en',
            status TEXT,
            syllabus TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE curriculum_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            curriculum_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            link TEXT,
            sort_order INTEGER,
            FOREIGN KEY (curriculum_id) REFERENCES curricula(id)
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX idx_tags_slug ON tags(slug)")
    cursor.execute("CREATE INDEX idx_chapter_tags_chapter ON chapter_tags(chapter_id)")
    cursor.execute("CREATE INDEX idx_chapter_tags_tag ON chapter_tags(tag_id)")
    cursor.execute("CREATE INDEX idx_books_shelf ON books(shelf_id)")
    cursor.execute("CREATE INDEX idx_chapters_book ON chapters(book_id)")
    cursor.execute("CREATE INDEX idx_libraries_type ON libraries(library_type_id)")
    cursor.execute("CREATE INDEX idx_shelves_library ON shelves(library_id)")

    # Create full-text search
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS books_fts USING fts5(
            name,
            content='books',
            content_rowid='id'
        )
    """)

    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chapters_fts USING fts5(
            name,
            content='chapters',
            content_rowid='id'
        )
    """)

    # Create views
    cursor.execute("""
        CREATE VIEW v_book_summary AS
        SELECT
            b.id as book_id,
            b.name as book_name,
            lt.name as library_type,
            l.name as library,
            s.name as shelf,
            COUNT(c.id) as chapter_count
        FROM books b
        JOIN shelves s ON b.shelf_id = s.id
        JOIN libraries l ON s.library_id = l.id
        JOIN library_types lt ON l.library_type_id = lt.id
        LEFT JOIN chapters c ON c.book_id = b.id
        GROUP BY b.id
    """)

    cursor.execute("""
        CREATE VIEW v_tag_usage AS
        SELECT
            t.slug,
            t.label,
            t.tier,
            COUNT(ct.chapter_id) as usage_count
        FROM tags t
        LEFT JOIN chapter_tags ct ON t.id = ct.tag_id
        GROUP BY t.id
        ORDER BY usage_count DESC
    """)

    cursor.execute("""
        CREATE VIEW v_library_stats AS
        SELECT
            lt.name as library_type,
            l.name as library,
            COUNT(DISTINCT b.id) as book_count,
            COUNT(c.id) as chapter_count
        FROM library_types lt
        JOIN libraries l ON l.library_type_id = lt.id
        LEFT JOIN shelves s ON s.library_id = l.id
        LEFT JOIN books b ON b.shelf_id = s.id
        LEFT JOIN chapters c ON c.book_id = b.id
        GROUP BY lt.id, l.id
        ORDER BY lt.name, l.name
    """)

    conn.commit()
    print("Database schema created.")


def load_tags(conn):
    """Load tags from tag-vocabulary.json."""
    cursor = conn.cursor()

    if not TAG_VOCAB_PATH.exists():
        print(f"Warning: Tag vocabulary not found at {TAG_VOCAB_PATH}")
        return {}

    with open(TAG_VOCAB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tag_map = {}  # slug -> id

    for tier, tags_list in data.get('tags', {}).items():
        for tag in tags_list:
            slug = tag.get('id', '')
            label = tag.get('label', '')
            description = tag.get('description', '')

            if slug:
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (slug, label, tier, description)
                    VALUES (?, ?, ?, ?)
                """, (slug, label, tier, description))

                cursor.execute("SELECT id FROM tags WHERE slug = ?", (slug,))
                tag_map[slug] = cursor.fetchone()[0]
                stats["tags"] += 1

    conn.commit()
    print(f"Loaded {stats['tags']} tags from vocabulary.")
    return tag_map


def get_or_create_library_type(conn, name):
    """Get or create a library type."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM library_types WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("INSERT INTO library_types (name) VALUES (?)", (name,))
    conn.commit()
    stats["library_types"] += 1
    return cursor.lastrowid


def get_or_create_library(conn, library_type_id, name, slug=None, description=None):
    """Get or create a library."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM libraries
        WHERE library_type_id = ? AND name = ?
    """, (library_type_id, name))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO libraries (library_type_id, name, slug, description)
        VALUES (?, ?, ?, ?)
    """, (library_type_id, name, slug, description))
    conn.commit()
    stats["libraries"] += 1
    return cursor.lastrowid


def get_or_create_shelf(conn, library_id, name, slug=None):
    """Get or create a shelf."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM shelves
        WHERE library_id = ? AND name = ?
    """, (library_id, name))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("""
        INSERT INTO shelves (library_id, name, slug)
        VALUES (?, ?, ?)
    """, (library_id, name, slug))
    conn.commit()
    stats["shelves"] += 1
    return cursor.lastrowid


def name_to_slug(name):
    """Convert a name to a slug."""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def process_book_file(conn, file_path, library_type_name, library_name, shelf_name, tag_map):
    """Process a single book JSON file."""
    cursor = conn.cursor()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        stats["errors"].append(f"JSON error in {file_path}: {e}")
        stats["files_skipped"] += 1
        return
    except Exception as e:
        stats["errors"].append(f"Error reading {file_path}: {e}")
        stats["files_skipped"] += 1
        return

    # Skip manifest and meta files
    filename = file_path.name
    if filename.startswith('_') or filename in ['_manifest.json', '_meta.json']:
        return

    # Get book data
    book_name = data.get('name', filename.replace('.json', '').replace('-', ' ').title())
    created_by = data.get('created_by', None)
    chapters = data.get('chapters', [])

    # Skip if no chapters (not a book file)
    if not chapters and 'shelves' not in data:
        return

    # Handle older format with nested shelves
    if 'shelves' in data:
        # This is an older format - skip for now or process differently
        return

    # Get file stats
    file_stat = file_path.stat()
    file_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
    file_size = file_stat.st_size

    # Get or create hierarchy
    library_type_id = get_or_create_library_type(conn, library_type_name)
    library_id = get_or_create_library(conn, library_type_id, library_name,
                                        name_to_slug(library_name))
    shelf_id = get_or_create_shelf(conn, library_id, shelf_name,
                                    name_to_slug(shelf_name))

    # Insert book
    cursor.execute("""
        INSERT INTO books (shelf_id, name, created_by, file_path, file_modified, file_size_bytes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (shelf_id, book_name, created_by, str(file_path), file_modified, file_size))
    book_id = cursor.lastrowid
    stats["books"] += 1

    # Insert into FTS
    cursor.execute("INSERT INTO books_fts (rowid, name) VALUES (?, ?)", (book_id, book_name))

    # Insert chapters
    for i, chapter in enumerate(chapters):
        if isinstance(chapter, dict):
            chapter_name = chapter.get('name', f'Chapter {i+1}')
            chapter_tags = chapter.get('tags', [])
        else:
            chapter_name = str(chapter)
            chapter_tags = []

        cursor.execute("""
            INSERT INTO chapters (book_id, name, sort_order)
            VALUES (?, ?, ?)
        """, (book_id, chapter_name, i))
        chapter_id = cursor.lastrowid
        stats["chapters"] += 1

        # Insert into FTS
        cursor.execute("INSERT INTO chapters_fts (rowid, name) VALUES (?, ?)",
                      (chapter_id, chapter_name))

        # Insert chapter tags
        for tag_slug in chapter_tags:
            tag_slug_normalized = tag_slug.lower().replace(' ', '-')
            if tag_slug_normalized in tag_map:
                tag_id = tag_map[tag_slug_normalized]
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO chapter_tags (chapter_id, tag_id)
                        VALUES (?, ?)
                    """, (chapter_id, tag_id))
                    stats["chapter_tags"] += 1
                except:
                    pass
            else:
                # Create tag if not in vocabulary
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (slug, label, tier)
                    VALUES (?, ?, 'unknown')
                """, (tag_slug_normalized, tag_slug))
                cursor.execute("SELECT id FROM tags WHERE slug = ?", (tag_slug_normalized,))
                row = cursor.fetchone()
                if row:
                    tag_map[tag_slug_normalized] = row[0]
                    cursor.execute("""
                        INSERT OR IGNORE INTO chapter_tags (chapter_id, tag_id)
                        VALUES (?, ?)
                    """, (chapter_id, row[0]))
                    stats["chapter_tags"] += 1

    conn.commit()
    stats["files_processed"] += 1


def scan_libraries(conn, tag_map):
    """Scan all library directories for book files."""
    for lib_path in LIBRARY_PATHS:
        if not lib_path.exists():
            print(f"Warning: Library path not found: {lib_path}")
            continue

        library_type_name = lib_path.name.replace('-libraries', '').replace('-', ' ').title()
        print(f"Scanning {library_type_name}...")

        # Walk the directory structure
        for library_dir in lib_path.iterdir():
            if not library_dir.is_dir() or library_dir.name.startswith('_'):
                continue

            library_name = library_dir.name.replace('-', ' ').title()

            for shelf_dir in library_dir.iterdir():
                if not shelf_dir.is_dir() or shelf_dir.name.startswith('_'):
                    continue

                shelf_name = shelf_dir.name.replace('-', ' ').title()

                # Process book files in shelf
                for book_file in shelf_dir.glob('*.json'):
                    if book_file.name.startswith('_'):
                        continue
                    process_book_file(conn, book_file, library_type_name,
                                     library_name, shelf_name, tag_map)

        # Also handle questions-libraries specially (flat structure)
        if 'questions' in lib_path.name:
            for book_file in lib_path.glob('*.json'):
                if book_file.name.startswith('_'):
                    continue
                process_book_file(conn, book_file, "Questions",
                                 "Questions", "General", tag_map)


def load_curricula(conn):
    """Load curricula from curriculum-index.json."""
    cursor = conn.cursor()

    if not CURRICULUM_PATH.exists():
        print(f"Warning: Curriculum file not found at {CURRICULUM_PATH}")
        return

    try:
        with open(CURRICULUM_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading curricula: {e}")
        return

    disciplines = data.get('disciplines', [])

    for disc in disciplines:
        curriculum_id = disc.get('id', '')
        school = disc.get('school', '')
        title = disc.get('title', '')
        icon = disc.get('icon', '')
        description = disc.get('description', '')
        lang = disc.get('lang', 'en')
        status = disc.get('status', '')
        syllabus = disc.get('syllabus', '')

        cursor.execute("""
            INSERT INTO curricula (curriculum_id, school, title, icon, description, lang, status, syllabus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (curriculum_id, school, title, icon, description, lang, status, syllabus))

        db_curriculum_id = cursor.lastrowid
        stats["curricula"] += 1

        # Insert courses
        courses = disc.get('courses', [])
        for i, course in enumerate(courses):
            course_title = course.get('title', '')
            course_link = course.get('link', '')

            cursor.execute("""
                INSERT INTO curriculum_courses (curriculum_id, title, link, sort_order)
                VALUES (?, ?, ?, ?)
            """, (db_curriculum_id, course_title, course_link, i))

    conn.commit()
    print(f"Loaded {stats['curricula']} curricula.")


def print_summary():
    """Print a summary of the database build."""
    print("\n" + "="*50)
    print("QUAREX DATABASE BUILD SUMMARY")
    print("="*50)
    print(f"Files processed:  {stats['files_processed']}")
    print(f"Files skipped:    {stats['files_skipped']}")
    print(f"Library types:    {stats['library_types']}")
    print(f"Libraries:        {stats['libraries']}")
    print(f"Shelves:          {stats['shelves']}")
    print(f"Books:            {stats['books']}")
    print(f"Chapters:         {stats['chapters']}")
    print(f"Tags:             {stats['tags']}")
    print(f"Chapter-tag links:{stats['chapter_tags']}")
    print(f"Curricula:        {stats['curricula']}")
    print("="*50)

    if stats["errors"]:
        print("\nErrors:")
        for error in stats["errors"][:10]:
            print(f"  - {error}")
        if len(stats["errors"]) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more errors")

    print(f"\nDatabase saved to: {DB_PATH}")


def main():
    """Main entry point."""
    print("Quarex Catalog Database Builder")
    print("-" * 40)

    # Ensure database directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database.")

    # Connect and build
    conn = sqlite3.connect(str(DB_PATH))

    try:
        create_database(conn)
        tag_map = load_tags(conn)
        scan_libraries(conn, tag_map)
        load_curricula(conn)
        print_summary()
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
