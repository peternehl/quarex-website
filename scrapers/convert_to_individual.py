"""
Quarex Candidate Converter

Converts compendium JSON files (one big file with all states) into
individual state JSON files that Quarex expects.

Usage:
    python convert_to_individual.py --senate
    python convert_to_individual.py --governor
    python convert_to_individual.py --house
    python convert_to_individual.py --all
"""

import json
import os
import re
from datetime import datetime

# Paths
CANDIDATE_DIR = os.path.join(os.path.dirname(__file__), "..", "libraries", "politician-libraries")

def slugify(name):
    """Convert name to slug format (lowercase, hyphens)"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug

def convert_senate():
    """Convert Senate compendium to individual state files"""
    print("\n" + "=" * 50)
    print("Converting Senate 2026")
    print("=" * 50)

    compendium_path = os.path.join(CANDIDATE_DIR, "us-senate-2026-complete", "us_senate_2026_complete.json")
    output_dir = os.path.join(CANDIDATE_DIR, "us-senate-2026-complete", "class-2-regular-elections")

    if not os.path.exists(compendium_path):
        print(f"ERROR: Compendium file not found: {compendium_path}")
        return False

    with open(compendium_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    # Process each shelf (Class 2 Regular Elections, Special Elections)
    states_processed = 0
    for shelf in data.get("shelves", []):
        shelf_name = shelf.get("name", "")
        shelf_slug = slugify(shelf_name)

        # Determine output directory based on shelf
        if "special" in shelf_name.lower():
            shelf_output_dir = os.path.join(CANDIDATE_DIR, "us-senate-2026-complete", "special-elections")
        else:
            shelf_output_dir = output_dir

        os.makedirs(shelf_output_dir, exist_ok=True)

        for book in shelf.get("books", []):
            state_name = book.get("name")
            state_slug = slugify(state_name)

            # Create individual state file
            state_data = {
                "book": state_name,
                "chapters": book.get("chapters", [])
            }

            state_file = os.path.join(shelf_output_dir, f"{state_slug}.json")
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2)

            states_processed += 1
            print(f"  Created: {state_slug}.json")

    # Update manifest
    update_manifest(os.path.join(CANDIDATE_DIR, "us-senate-2026-complete", "class-2-regular-elections"))

    print(f"\nConverted {states_processed} states")
    return True

def convert_governor():
    """Convert Governor compendium to individual state files"""
    print("\n" + "=" * 50)
    print("Converting Governors 2026")
    print("=" * 50)

    compendium_path = os.path.join(CANDIDATE_DIR, "us-governors-2026", "us_governors_2026.json")
    output_dir = os.path.join(CANDIDATE_DIR, "us-governors-2026", "2026-gubernatorial-races")

    if not os.path.exists(compendium_path):
        print(f"ERROR: Compendium file not found: {compendium_path}")
        return False

    with open(compendium_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)

    states_processed = 0
    for shelf in data.get("shelves", []):
        for book in shelf.get("books", []):
            state_name = book.get("name")
            state_slug = slugify(state_name)

            # Create individual state file
            state_data = {
                "book": state_name,
                "chapters": book.get("chapters", [])
            }

            state_file = os.path.join(output_dir, f"{state_slug}.json")
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2)

            states_processed += 1
            print(f"  Created: {state_slug}.json")

    # Update manifest
    update_manifest(output_dir)

    print(f"\nConverted {states_processed} states")
    return True

def convert_house():
    """Convert House compendium to individual district files organized by state"""
    print("\n" + "=" * 50)
    print("Converting House 2026")
    print("=" * 50)

    # House uses the working file from scrapers directory
    compendium_path = os.path.join(os.path.dirname(__file__), "house_2026_working.json")
    states_dir = os.path.join(CANDIDATE_DIR, "us-house-2026-complete", "2026-states")

    if not os.path.exists(compendium_path):
        print(f"ERROR: Compendium file not found: {compendium_path}")
        return False

    with open(compendium_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    os.makedirs(states_dir, exist_ok=True)

    # For House, each shelf is a state containing multiple district books
    # We create a folder per state, with individual district files inside
    states_processed = 0
    total_districts = 0
    state_info = []

    for shelf in data.get("shelves", []):
        state_name = shelf.get("name", "")
        # Extract just the state name (remove district count)
        state_name_clean = state_name.split(" (")[0] if " (" in state_name else state_name
        state_slug = slugify(state_name_clean)

        # Create state folder
        state_dir = os.path.join(states_dir, state_slug)
        os.makedirs(state_dir, exist_ok=True)

        district_count = 0
        district_manifest = []

        # Create individual district files
        for book in shelf.get("books", []):
            district_name = book.get("name", "")
            district_slug = slugify(district_name)

            # Create district file with book structure
            district_data = {
                "book": district_name,
                "chapters": book.get("chapters", [])
            }

            district_file = os.path.join(state_dir, f"{district_slug}.json")
            with open(district_file, 'w', encoding='utf-8') as f:
                json.dump(district_data, f, indent=2)

            # Count chapters for manifest
            chapter_count = len(book.get("chapters", []))
            district_manifest.append({
                "slug": district_slug,
                "name": district_name,
                "chapterCount": chapter_count
            })

            district_count += 1
            total_districts += 1

        # Write state manifest
        state_manifest_path = os.path.join(state_dir, "_manifest.json")
        with open(state_manifest_path, 'w', encoding='utf-8') as f:
            json.dump(district_manifest, f, indent=2)

        state_info.append({
            "slug": state_slug,
            "name": state_name,
            "chapterCount": district_count
        })

        states_processed += 1
        print(f"  Created: {state_slug}/ ({district_count} districts)")

    # Write 2026-states manifest (list of states)
    states_manifest_path = os.path.join(states_dir, "_manifest.json")
    with open(states_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(state_info, f, indent=2)
    print(f"  Updated states manifest: {len(state_info)} states")

    # Create library manifest
    create_house_library_manifest(states_processed)

    print(f"\nConverted {states_processed} states, {total_districts} districts")
    return True

def create_house_library_manifest(state_count):
    """Create the library-level _manifest.json for House"""
    library_dir = os.path.join(CANDIDATE_DIR, "us-house-2026-complete")
    manifest_path = os.path.join(library_dir, "_manifest.json")

    manifest = [
        {
            "slug": "2026-states",
            "name": "2026 House States",
            "description": "All House districts with declared 2026 candidates (excludes redistricting states)",
            "bookCount": state_count
        }
    ]

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"  Created library manifest")

def update_manifest(shelf_dir):
    """Update the _manifest.json in a shelf directory"""
    manifest_path = os.path.join(shelf_dir, "_manifest.json")

    # Count JSON files (excluding _manifest.json and _meta.json)
    json_files = [f for f in os.listdir(shelf_dir)
                  if f.endswith('.json') and not f.startswith('_')]

    books = []
    for filename in sorted(json_files):
        filepath = os.path.join(shelf_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        book_name = data.get("book", filename.replace('.json', '').replace('-', ' ').title())
        books.append({
            "slug": filename.replace('.json', ''),
            "name": book_name,
            "chapterCount": len(data.get("chapters", []))
        })

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(books, f, indent=2)

    print(f"  Updated manifest: {len(books)} books")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert candidate compendium files to individual state files")
    parser.add_argument("--senate", action="store_true", help="Convert Senate compendium")
    parser.add_argument("--governor", action="store_true", help="Convert Governor compendium")
    parser.add_argument("--house", action="store_true", help="Convert House compendium")
    parser.add_argument("--all", action="store_true", help="Convert all compendiums")

    args = parser.parse_args()

    if not any([args.senate, args.governor, args.house, args.all]):
        parser.print_help()
        return

    print(f"Quarex Candidate Converter")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.senate or args.all:
        convert_senate()

    if args.governor or args.all:
        convert_governor()

    if args.house or args.all:
        convert_house()

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
