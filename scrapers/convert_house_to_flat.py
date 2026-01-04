"""
Convert House data from party-separated format to flat format for Quarex.

Quarex House structure (server format):
- Each state is a single JSON file (e.g., alabama.json)
- Each district is a chapter
- All candidates from all parties are mixed together in topics
- Tags are added per chapter

This script converts the house_2026_working.json (party-separated)
to individual state files in the flat format.
"""

import json
import os
import re
from datetime import datetime

# Paths
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRAPERS_DIR)
WORKING_FILE = os.path.join(SCRAPERS_DIR, "house_2026_working.json")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "libraries", "politician-libraries", "us-house-2026-complete", "2026-states")

# State name to slug mapping
def slugify(name):
    """Convert state name to slug."""
    return name.lower().replace(" ", "-")


def convert_to_flat_format():
    """Convert party-separated format to flat format."""
    print("=" * 60)
    print("Converting House data to flat format")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load working file
    if not os.path.exists(WORKING_FILE):
        print(f"ERROR: Working file not found: {WORKING_FILE}")
        return False

    with open(WORKING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded: {WORKING_FILE}")

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Process each state (shelf)
    states_processed = 0
    manifest_entries = []

    for shelf in data.get('shelves', []):
        # Parse state name from shelf name like "Alabama (7 districts)"
        shelf_name = shelf['name']
        state_match = re.match(r'^([A-Za-z ]+) \((\d+)', shelf_name)
        if not state_match:
            print(f"  Skipping invalid shelf: {shelf_name}")
            continue

        state_name = state_match.group(1)
        district_count = int(state_match.group(2))
        state_slug = slugify(state_name)

        # Build flat state structure
        state_data = {
            "book": state_name,
            "chapters": []
        }

        # Process each district (book in party-separated format)
        for book in shelf.get('books', []):
            district_name = book['name']  # e.g., "AL-01"

            # Collect all candidates from all party chapters
            all_candidates = []
            for chapter in book.get('chapters', []):
                topics = chapter.get('topics', [])
                if topics != ["No candidates declared"]:
                    all_candidates.extend(topics)

            # Create flat chapter
            chapter_data = {
                "name": district_name,
                "topics": all_candidates if all_candidates else ["No candidates declared"],
                "tags": ["politics", "elections", "house", state_slug]
            }

            state_data["chapters"].append(chapter_data)

        # Write state file
        output_file = os.path.join(OUTPUT_DIR, f"{state_slug}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2)

        # Add to manifest
        manifest_entries.append({
            "slug": state_slug,
            "name": state_name,
            "chapterCount": len(state_data["chapters"])
        })

        candidate_count = sum(len(ch['topics']) for ch in state_data['chapters']
                             if ch['topics'] != ["No candidates declared"])
        print(f"  Created: {state_slug}.json ({district_count} districts, {candidate_count} candidates)")
        states_processed += 1

    # Write manifest
    manifest_file = os.path.join(OUTPUT_DIR, "_manifest.json")
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest_entries, f, indent=2)
    print(f"\nUpdated manifest: {len(manifest_entries)} states")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Converted {states_processed} states to flat format")
    print(f"Output directory: {OUTPUT_DIR}")

    return True


def merge_with_server_data(server_dir):
    """
    Merge local data with server data, keeping server data for states
    where local scraping failed.

    Args:
        server_dir: Path to downloaded server 2026-states folder
    """
    print("=" * 60)
    print("Merging with server data")
    print("=" * 60)

    if not os.path.exists(server_dir):
        print(f"ERROR: Server directory not found: {server_dir}")
        return False

    # Load working file
    with open(WORKING_FILE, 'r', encoding='utf-8') as f:
        local_data = json.load(f)

    # Build local state data
    local_states = {}
    for shelf in local_data.get('shelves', []):
        state_match = re.match(r'^([A-Za-z ]+) \(', shelf['name'])
        if state_match:
            state_name = state_match.group(1)
            state_slug = slugify(state_name)

            # Count candidates
            total = 0
            for book in shelf.get('books', []):
                for chapter in book.get('chapters', []):
                    topics = chapter.get('topics', [])
                    if topics != ["No candidates declared"]:
                        total += len(topics)

            local_states[state_slug] = {
                'shelf': shelf,
                'candidate_count': total
            }

    # Check server files
    server_files = [f for f in os.listdir(server_dir)
                   if f.endswith('.json') and f != '_manifest.json']

    merged_count = 0
    for filename in sorted(server_files):
        state_slug = filename.replace('.json', '')
        server_path = os.path.join(server_dir, filename)

        with open(server_path, 'r', encoding='utf-8') as f:
            server_data = json.load(f)

        # Count server candidates
        server_total = sum(len(ch.get('topics', [])) for ch in server_data.get('chapters', []))

        # Get local count
        local_info = local_states.get(state_slug)
        local_total = local_info['candidate_count'] if local_info else 0

        # If server has more candidates, use server data
        if server_total > local_total:
            # Copy server file to output
            output_file = os.path.join(OUTPUT_DIR, filename)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(server_data, f, indent=2)
            print(f"  {state_slug}: Using server data ({server_total} > {local_total})")
            merged_count += 1

    print(f"\nMerged {merged_count} states from server data")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert House data to flat format")
    parser.add_argument("--merge", type=str,
                       help="Path to server 2026-states folder to merge with")
    args = parser.parse_args()

    # First convert local data
    convert_to_flat_format()

    # Then merge with server if specified
    if args.merge:
        merge_with_server_data(args.merge)
