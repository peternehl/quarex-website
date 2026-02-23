#!/usr/bin/env python3
"""
Generate senate library files from the backup JSON.
Reads us_senate_2026_backup.json and creates individual state files
in libraries/politician-libraries/us-senate-2026-complete/class-2-regular-elections/
"""

import json
from pathlib import Path

# Paths
BASE_DIR = Path(r"E:\projects\websites\Quarex")
BACKUP_FILE = BASE_DIR / "scrapers" / "us_senate_2026_backup.json"
OUTPUT_DIR = BASE_DIR / "libraries" / "politician-libraries" / "us-senate-2026-complete" / "class-2-regular-elections"


def state_to_filename(state_name):
    """Convert state name to filename (e.g., 'New York' -> 'new-york.json')"""
    return state_name.lower().replace(' ', '-') + '.json'


def main():
    print("Generating Senate Library Files")
    print("=" * 50)
    print(f"Source: {BACKUP_FILE}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    # Load backup
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        backup = json.load(f)

    # Get books from first shelf (Class 2 Regular Elections)
    books = backup['shelves'][0]['books']
    print(f"Found {len(books)} states")
    print()

    updated_count = 0

    for book in books:
        state_name = book['name']
        chapters = book['chapters']

        # Create the library file content
        library_file = {
            "book": state_name,
            "chapters": chapters
        }

        # Determine output filename
        filename = state_to_filename(state_name)
        output_path = OUTPUT_DIR / filename

        # Check if file exists and compare
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)

            # Compare (simple JSON comparison)
            if json.dumps(existing, sort_keys=True) == json.dumps(library_file, sort_keys=True):
                print(f"  {state_name}: No changes")
                continue

        # Write the file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(library_file, f, indent=2)

        print(f"  {state_name}: UPDATED -> {filename}")
        updated_count += 1

    print()
    print(f"Complete: {updated_count} files updated, {len(books) - updated_count} unchanged")


if __name__ == "__main__":
    main()
