#!/usr/bin/env python3
"""
Compare House candidate state files between two dates to find added/removed candidates.

Usage: python compare-state-files.py [old_dir] [new_dir]

Compares the actual state files used by the app (e.g., alabama.json, texas.json)
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Default directories
OLD_DIR = Path(r"E:\projects\websites\Quarex\libraries\politician-libraries as of 2-12-26\us-house-2026-complete\2026-states")
NEW_DIR = Path(r"E:\projects\websites\Quarex\libraries\politician-libraries\us-house-2026-complete\2026-states")


def extract_candidates_from_state_file(filepath):
    """Extract candidates from a state file: {district: set(candidates)}"""
    candidates = defaultdict(set)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for chapter in data.get('chapters', []):
            district = chapter['name']
            for candidate in chapter.get('topics', []):
                candidates[district].add(candidate)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    return candidates


def compare_directories(old_dir, new_dir):
    """Compare all state files between two directories."""
    added = defaultdict(list)
    removed = defaultdict(list)

    # Get all state files (exclude folders and manifests)
    old_files = {f.stem: f for f in old_dir.glob('*.json') if f.stem != '_manifest'}
    new_files = {f.stem: f for f in new_dir.glob('*.json') if f.stem != '_manifest'}

    all_states = set(old_files.keys()) | set(new_files.keys())

    for state in sorted(all_states):
        old_file = old_files.get(state)
        new_file = new_files.get(state)

        old_candidates = extract_candidates_from_state_file(old_file) if old_file else {}
        new_candidates = extract_candidates_from_state_file(new_file) if new_file else {}

        all_districts = set(old_candidates.keys()) | set(new_candidates.keys())

        for district in sorted(all_districts):
            old_names = old_candidates.get(district, set())
            new_names = new_candidates.get(district, set())

            # Added candidates
            for name in sorted(new_names - old_names):
                added[district].append(name)

            # Removed candidates
            for name in sorted(old_names - new_names):
                removed[district].append(name)

    return added, removed


def main():
    old_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else OLD_DIR
    new_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else NEW_DIR

    print("=" * 70)
    print("HOUSE CANDIDATE STATE FILE COMPARISON")
    print("=" * 70)
    print(f"OLD: {old_dir}")
    print(f"NEW: {new_dir}")
    print()

    added, removed = compare_directories(old_dir, new_dir)

    # Report added
    print("-" * 70)
    print("CANDIDATES ADDED")
    print("-" * 70)
    if added:
        total = 0
        for district in sorted(added.keys()):
            for candidate in added[district]:
                print(f"  {district}: + {candidate}")
                total += 1
        print(f"\nTotal added: {total}")
    else:
        print("  (none)")

    print()

    # Report removed
    print("-" * 70)
    print("CANDIDATES REMOVED")
    print("-" * 70)
    if removed:
        total = 0
        for district in sorted(removed.keys()):
            for candidate in removed[district]:
                print(f"  {district}: - {candidate}")
                total += 1
        print(f"\nTotal removed: {total}")
    else:
        print("  (none)")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
