#!/usr/bin/env python3
"""
Add new books to the Quarex catalog database.
Scans for books not already in the database and adds them.

Usage:
    python add-books-to-db.py [--shelf path/to/shelf]

Examples:
    python add-books-to-db.py
    python add-books-to-db.py --shelf libraries/perspectives-libraries/contested-issues/labor-and-work
"""

import json
import os
import sqlite3
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
BASE_PATH = Path(r"E:\projects\websites\Quarex")
DB_PATH = BASE_PATH / "database" / "quarex-catalog.db"
TAG_VOCAB_PATH = BASE_PATH / "libraries" / "_utils" / "tag-vocabulary.json"

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

stats = {
    "books_added": 0,
    "books_skipped": 0,
    "chapters_added": 0,
    "errors": []
}


def get_existing_books(conn):
    """Get set of file paths already in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT file_path FROM books")
    return {row[0] for row in cursor.fetchall()}


def load_tag_map(conn):
    """Load existing tags from database into a map."""
    cursor = conn.cursor()
    cursor.execute("SELECT slug, id FROM tags")
    return {row[0]: row[1] for row in cursor.fetchall()}


def get_or_create_library_type(conn, name):
    """Get or create a library type."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM library_types WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("INSERT INTO library_types (name) VALUES (?)", (name,))
    conn.commit()
    return cursor.lastrowid


def get_or_create_library(conn, library_type_id, name, slug=None, description=None):
    """Get or create a library."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM libraries WHERE library_type_id = ? AND name = ?
    """, (library_type_id, name))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("""
        INSERT INTO libraries (library_type_id, name, slug, description)
        VALUES (?, ?, ?, ?)
    """, (library_type_id, name, slug, description))
    conn.commit()
    return cursor.lastrowid


def get_or_create_shelf(conn, library_id, name, slug=None):
    """Get or create a shelf."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM shelves WHERE library_id = ? AND name = ?
    """, (library_id, name))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute("""
        INSERT INTO shelves (library_id, name, slug) VALUES (?, ?, ?)
    """, (library_id, name, slug))
    conn.commit()
    return cursor.lastrowid


def name_to_slug(name):
    """Convert a name to a slug."""
    import re
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def add_book(conn, file_path, library_type_name, library_name, shelf_name, tag_map):
    """Add a single book to the database."""
    cursor = conn.cursor()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        stats["errors"].append(f"JSON error in {file_path}: {e}")
        return False
    except Exception as e:
        stats["errors"].append(f"Error reading {file_path}: {e}")
        return False

    # Skip manifest files
    filename = file_path.name
    if filename.startswith('_'):
        return False

    # Get book data
    book_name = data.get('name', filename.replace('.json', '').replace('-', ' ').title())
    created_by = data.get('created_by', None)
    chapters = data.get('chapters', [])

    # Skip if no chapters
    if not chapters:
        return False

    # Skip older nested format
    if 'shelves' in data:
        return False

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
    stats["books_added"] += 1

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
            INSERT INTO chapters (book_id, name, sort_order) VALUES (?, ?, ?)
        """, (book_id, chapter_name, i))
        chapter_id = cursor.lastrowid
        stats["chapters_added"] += 1

        # Insert into FTS
        cursor.execute("INSERT INTO chapters_fts (rowid, name) VALUES (?, ?)",
                      (chapter_id, chapter_name))

        # Insert chapter tags
        for tag_slug in chapter_tags:
            tag_slug_normalized = tag_slug.lower().replace(' ', '-')
            if tag_slug_normalized in tag_map:
                tag_id = tag_map[tag_slug_normalized]
                cursor.execute("""
                    INSERT OR IGNORE INTO chapter_tags (chapter_id, tag_id)
                    VALUES (?, ?)
                """, (chapter_id, tag_id))

    conn.commit()
    print(f"  Added: {book_name} ({len(chapters)} chapters)")
    return True


def scan_for_new_books(conn, existing_books, tag_map, specific_shelf=None):
    """Scan libraries for books not in the database."""

    for lib_path in LIBRARY_PATHS:
        if not lib_path.exists():
            continue

        library_type_name = lib_path.name.replace('-libraries', '').replace('-', ' ').title()

        for library_dir in lib_path.iterdir():
            if not library_dir.is_dir() or library_dir.name.startswith('_'):
                continue

            library_name = library_dir.name.replace('-', ' ').title()

            for shelf_dir in library_dir.iterdir():
                if not shelf_dir.is_dir() or shelf_dir.name.startswith('_'):
                    continue

                # If specific shelf requested, skip others
                if specific_shelf:
                    shelf_rel_path = shelf_dir.relative_to(BASE_PATH)
                    if str(shelf_rel_path).replace('\\', '/') != specific_shelf.replace('\\', '/'):
                        continue

                shelf_name = shelf_dir.name.replace('-', ' ').title()
                found_new = False

                for book_file in shelf_dir.glob('*.json'):
                    if book_file.name.startswith('_'):
                        continue

                    file_path_str = str(book_file)
                    if file_path_str in existing_books:
                        stats["books_skipped"] += 1
                        continue

                    if not found_new:
                        print(f"\n{library_type_name} > {library_name} > {shelf_name}:")
                        found_new = True

                    add_book(conn, book_file, library_type_name,
                            library_name, shelf_name, tag_map)


def main():
    parser = argparse.ArgumentParser(description='Add new books to Quarex database')
    parser.add_argument('--shelf', type=str, help='Specific shelf path to scan')
    args = parser.parse_args()

    print("Quarex Database - Add New Books")
    print("-" * 40)

    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Run build-quarex-db.py first to create the database.")
        return 1

    conn = sqlite3.connect(str(DB_PATH))

    try:
        existing_books = get_existing_books(conn)
        print(f"Existing books in database: {len(existing_books)}")

        tag_map = load_tag_map(conn)
        print(f"Tags loaded: {len(tag_map)}")

        print("\nScanning for new books...")
        scan_for_new_books(conn, existing_books, tag_map, args.shelf)

        print("\n" + "=" * 40)
        print("SUMMARY")
        print("=" * 40)
        print(f"Books added:    {stats['books_added']}")
        print(f"Chapters added: {stats['chapters_added']}")
        print(f"Books skipped:  {stats['books_skipped']} (already in database)")

        if stats["errors"]:
            print("\nErrors:")
            for error in stats["errors"]:
                print(f"  - {error}")

    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
