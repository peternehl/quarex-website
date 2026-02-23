#!/usr/bin/env python3
"""
Quarex Database Explorer Server
A simple HTTP server to query the Quarex SQLite database.

Usage:
    python quarex-db-server.py

Then open: http://localhost:8765
"""

import json
import sqlite3
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Configuration
PORT = 8765
BASE_PATH = Path(r"E:\projects\websites\Quarex")
DB_PATH = BASE_PATH / "database" / "quarex-catalog.db"
HTML_PATH = BASE_PATH / "tools" / "quarex-db-explorer.html"


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def dict_from_row(row):
    """Convert a sqlite3.Row to a dict."""
    return dict(zip(row.keys(), row))


class QuarexHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for Quarex database queries."""

    def do_GET(self):
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API endpoints
        if path == '/api/library-types':
            self.send_json(self.get_library_types())
        elif path == '/api/libraries':
            library_type = query.get('type', [None])[0]
            self.send_json(self.get_libraries(library_type))
        elif path == '/api/shelves':
            library_id = query.get('library', [None])[0]
            self.send_json(self.get_shelves(library_id))
        elif path == '/api/tags':
            tier = query.get('tier', [None])[0]
            self.send_json(self.get_tags(tier))
        elif path == '/api/available-tags':
            selected = query.get('selected', [''])[0]
            self.send_json(self.get_available_tags(selected))
        elif path == '/api/search':
            self.send_json(self.search_books(query))
        elif path == '/api/stats':
            self.send_json(self.get_stats())
        elif path == '/api/book':
            book_id = query.get('id', [None])[0]
            self.send_json(self.get_book(book_id))
        elif path == '/' or path == '/index.html':
            self.serve_html()
        else:
            super().do_GET()

    def send_json(self, data):
        """Send a JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def serve_html(self):
        """Serve the HTML explorer page."""
        if HTML_PATH.exists():
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_PATH.read_bytes())
        else:
            self.send_error(404, 'HTML file not found')

    def get_library_types(self):
        """Get all library types."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM library_types ORDER BY name")
        result = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_libraries(self, library_type_id=None):
        """Get libraries, optionally filtered by type."""
        conn = get_db_connection()
        cursor = conn.cursor()
        if library_type_id:
            cursor.execute("""
                SELECT id, name, slug, description
                FROM libraries
                WHERE library_type_id = ?
                ORDER BY name
            """, (library_type_id,))
        else:
            cursor.execute("""
                SELECT l.id, l.name, l.slug, l.description, lt.name as type_name
                FROM libraries l
                JOIN library_types lt ON l.library_type_id = lt.id
                ORDER BY lt.name, l.name
            """)
        result = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_shelves(self, library_id=None):
        """Get shelves, optionally filtered by library."""
        conn = get_db_connection()
        cursor = conn.cursor()
        if library_id:
            cursor.execute("""
                SELECT id, name, slug
                FROM shelves
                WHERE library_id = ?
                ORDER BY name
            """, (library_id,))
        else:
            cursor.execute("""
                SELECT s.id, s.name, s.slug, l.name as library_name
                FROM shelves s
                JOIN libraries l ON s.library_id = l.id
                ORDER BY l.name, s.name
            """)
        result = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_tags(self, tier=None):
        """Get tags, optionally filtered by tier."""
        conn = get_db_connection()
        cursor = conn.cursor()
        if tier:
            cursor.execute("""
                SELECT t.id, t.slug, t.label, t.tier, COUNT(ct.chapter_id) as usage_count
                FROM tags t
                LEFT JOIN chapter_tags ct ON t.id = ct.tag_id
                WHERE t.tier = ?
                GROUP BY t.id
                ORDER BY usage_count DESC, t.label
            """, (tier,))
        else:
            cursor.execute("""
                SELECT t.id, t.slug, t.label, t.tier, COUNT(ct.chapter_id) as usage_count
                FROM tags t
                LEFT JOIN chapter_tags ct ON t.id = ct.tag_id
                GROUP BY t.id
                ORDER BY t.tier, usage_count DESC, t.label
            """)
        result = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_available_tags(self, selected_tags_str):
        """Get tags that would return results given current selections.

        Returns tags that appear on chapters in books that have ALL the selected tags.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            selected_tags = [t.strip() for t in selected_tags_str.split(',') if t.strip()]
            print(f"[DEBUG] get_available_tags called with: {selected_tags}")

            if not selected_tags:
                # No selection - return all tags with counts
                cursor.execute("""
                    SELECT t.id, t.slug, t.label, t.tier, COUNT(DISTINCT ct.chapter_id) as usage_count
                    FROM tags t
                    LEFT JOIN chapter_tags ct ON t.id = ct.tag_id
                    GROUP BY t.id
                    HAVING usage_count > 0
                    ORDER BY t.tier, t.label
                """)
            else:
                # Find books that have ALL selected tags
                placeholders = ','.join(['?' for _ in selected_tags])

                # First, get books that have chapters with ALL selected tags
                cursor.execute(f"""
                    SELECT DISTINCT b.id
                    FROM books b
                    JOIN chapters c ON c.book_id = b.id
                    JOIN chapter_tags ct ON ct.chapter_id = c.id
                    JOIN tags t ON t.id = ct.tag_id
                    WHERE t.slug IN ({placeholders})
                    GROUP BY b.id
                    HAVING COUNT(DISTINCT t.slug) = ?
                """, (*selected_tags, len(selected_tags)))

                matching_book_ids = [row[0] for row in cursor.fetchall()]
                print(f"[DEBUG] Found {len(matching_book_ids)} matching books")

                if not matching_book_ids:
                    conn.close()
                    return []

                # Now get all tags that appear in those books
                book_placeholders = ','.join(['?' for _ in matching_book_ids])
                cursor.execute(f"""
                    SELECT t.id, t.slug, t.label, t.tier, COUNT(DISTINCT ct.chapter_id) as usage_count
                    FROM tags t
                    JOIN chapter_tags ct ON t.id = ct.tag_id
                    JOIN chapters c ON c.id = ct.chapter_id
                    WHERE c.book_id IN ({book_placeholders})
                    GROUP BY t.id
                    ORDER BY t.tier, t.label
                """, matching_book_ids)

            result = [dict_from_row(row) for row in cursor.fetchall()]
            print(f"[DEBUG] Returning {len(result)} tags")
            conn.close()
            return result
        except Exception as e:
            print(f"[ERROR] get_available_tags failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def search_books(self, query):
        """Search books with various filters."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Build query
        sql = """
            SELECT DISTINCT
                b.id,
                b.name as book_name,
                b.created_by,
                b.file_path,
                b.file_modified,
                lt.name as library_type,
                l.name as library,
                s.name as shelf,
                (SELECT COUNT(*) FROM chapters WHERE book_id = b.id) as chapter_count
            FROM books b
            JOIN shelves s ON b.shelf_id = s.id
            JOIN libraries l ON s.library_id = l.id
            JOIN library_types lt ON l.library_type_id = lt.id
        """
        conditions = []
        params = []

        # Text search
        search_text = query.get('q', [''])[0]
        if search_text:
            sql += " JOIN books_fts ON books_fts.rowid = b.id"
            conditions.append("books_fts MATCH ?")
            params.append(f'"{search_text}"*')

        # Library type filter
        library_type = query.get('type', [''])[0]
        if library_type:
            conditions.append("lt.id = ?")
            params.append(library_type)

        # Library filter
        library_id = query.get('library', [''])[0]
        if library_id:
            conditions.append("l.id = ?")
            params.append(library_id)

        # Shelf filter
        shelf_id = query.get('shelf', [''])[0]
        if shelf_id:
            conditions.append("s.id = ?")
            params.append(shelf_id)

        # Tag filter (multi-select with AND logic)
        tags = query.get('tags', [])
        tag_list = []
        if tags and tags[0]:
            tag_list = [t.strip() for t in tags[0].split(',') if t.strip()]

        if tag_list:
            # Use subquery to find books with ALL selected tags
            placeholders = ','.join(['?' for _ in tag_list])
            tag_subquery = f"""
                b.id IN (
                    SELECT b2.id
                    FROM books b2
                    JOIN chapters c2 ON c2.book_id = b2.id
                    JOIN chapter_tags ct2 ON ct2.chapter_id = c2.id
                    JOIN tags t2 ON t2.id = ct2.tag_id
                    WHERE t2.slug IN ({placeholders})
                    GROUP BY b2.id
                    HAVING COUNT(DISTINCT t2.slug) = ?
                )
            """
            conditions.append(tag_subquery)
            params.extend(tag_list)
            params.append(len(tag_list))

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY b.name LIMIT 200"

        cursor.execute(sql, params)
        result = [dict_from_row(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def get_book(self, book_id):
        """Get a single book with its chapters."""
        if not book_id:
            return None

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get book info
        cursor.execute("""
            SELECT
                b.id,
                b.name,
                b.created_by,
                b.file_path,
                lt.name as library_type,
                l.name as library,
                s.name as shelf
            FROM books b
            JOIN shelves s ON b.shelf_id = s.id
            JOIN libraries l ON s.library_id = l.id
            JOIN library_types lt ON l.library_type_id = lt.id
            WHERE b.id = ?
        """, (book_id,))

        book_row = cursor.fetchone()
        if not book_row:
            conn.close()
            return None

        book = dict_from_row(book_row)

        # Get chapters
        cursor.execute("""
            SELECT c.id, c.name, c.sort_order
            FROM chapters c
            WHERE c.book_id = ?
            ORDER BY c.sort_order
        """, (book_id,))
        book['chapters'] = [dict_from_row(row) for row in cursor.fetchall()]

        # Get tags for each chapter
        for chapter in book['chapters']:
            cursor.execute("""
                SELECT t.slug, t.label, t.tier
                FROM tags t
                JOIN chapter_tags ct ON t.id = ct.tag_id
                WHERE ct.chapter_id = ?
            """, (chapter['id'],))
            chapter['tags'] = [dict_from_row(row) for row in cursor.fetchall()]

        conn.close()
        return book

    def get_stats(self):
        """Get database statistics."""
        conn = get_db_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM library_types")
        stats['library_types'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM libraries")
        stats['libraries'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM shelves")
        stats['shelves'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM books")
        stats['books'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chapters")
        stats['chapters'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tags")
        stats['tags'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM curricula")
        stats['curricula'] = cursor.fetchone()[0]

        conn.close()
        return stats


def main():
    """Run the server."""
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        print("Run build-quarex-db.py first to create the database.")
        return 1

    server = HTTPServer(('localhost', PORT), QuarexHandler)
    print(f"Quarex Database Explorer")
    print(f"========================")
    print(f"Database: {DB_PATH}")
    print(f"Server running at: http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

    return 0


if __name__ == "__main__":
    exit(main())
