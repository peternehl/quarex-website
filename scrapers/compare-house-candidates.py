#!/usr/bin/env python3
"""
Compare two House candidate JSON files to find added/removed candidates.

Usage: python compare-house-candidates.py [old_file] [new_file]

Defaults to comparing Feb 12 backup vs current file.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Default file paths
OLD_FILE = Path(r"E:\projects\websites\Quarex\libraries\politician-libraries as of 2-12-26\us-house-2026-complete\us_house_2026_complete.json")
NEW_FILE = Path(r"E:\projects\websites\Quarex\libraries\politician-libraries\us-house-2026-complete\us_house_2026_complete.json")


def extract_candidates(data):
    """Extract all candidates as a dict: {district: {party: set(candidates)}}"""
    candidates = defaultdict(lambda: defaultdict(set))

    for shelf in data.get('shelves', []):
        for book in shelf.get('books', []):
            district = book['name']
            for chapter in book.get('chapters', []):
                party = chapter['name']
                for candidate in chapter.get('topics', []):
                    candidates[district][party].add(candidate)

    return candidates


def compare_candidates(old_data, new_data):
    """Compare two candidate datasets and return added/removed."""
    old_candidates = extract_candidates(old_data)
    new_candidates = extract_candidates(new_data)

    # Get all districts from both
    all_districts = set(old_candidates.keys()) | set(new_candidates.keys())

    added = defaultdict(list)
    removed = defaultdict(list)

    for district in sorted(all_districts):
        old_parties = old_candidates.get(district, {})
        new_parties = new_candidates.get(district, {})

        all_parties = set(old_parties.keys()) | set(new_parties.keys())

        for party in all_parties:
            old_names = old_parties.get(party, set())
            new_names = new_parties.get(party, set())

            # Find added candidates
            for name in new_names - old_names:
                added[district].append(f"{name} [{party}]")

            # Find removed candidates
            for name in old_names - new_names:
                removed[district].append(f"{name} [{party}]")

    return added, removed


def main():
    # Allow command line override of files
    old_file = Path(sys.argv[1]) if len(sys.argv) > 1 else OLD_FILE
    new_file = Path(sys.argv[2]) if len(sys.argv) > 2 else NEW_FILE

    print("=" * 70)
    print("HOUSE CANDIDATE COMPARISON")
    print("=" * 70)
    print(f"OLD: {old_file.name}")
    print(f"NEW: {new_file.name}")
    print()

    # Load files
    with open(old_file, 'r', encoding='utf-8') as f:
        old_data = json.load(f)

    with open(new_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    # Compare
    added, removed = compare_candidates(old_data, new_data)

    # Report added
    print("-" * 70)
    print("CANDIDATES ADDED")
    print("-" * 70)
    if added:
        total_added = 0
        for district in sorted(added.keys()):
            for candidate in added[district]:
                print(f"  {district}: + {candidate}")
                total_added += 1
        print(f"\nTotal added: {total_added}")
    else:
        print("  (none)")

    print()

    # Report removed
    print("-" * 70)
    print("CANDIDATES REMOVED")
    print("-" * 70)
    if removed:
        total_removed = 0
        for district in sorted(removed.keys()):
            for candidate in removed[district]:
                print(f"  {district}: - {candidate}")
                total_removed += 1
        print(f"\nTotal removed: {total_removed}")
    else:
        print("  (none)")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
