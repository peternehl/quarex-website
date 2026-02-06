#!/usr/bin/env python3
"""
Compare Senate candidate data between server and local versions.
Generates an HTML report showing additions, removals, and changes.
"""

import json
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(r"E:\projects\websites\Quarex")
OLD_DIR = Path(r"C:\Users\peter\Downloads\class-2-regular-elections")  # Server version
NEW_DIR = BASE_DIR / "libraries" / "politician-libraries" / "us-senate-2026-complete" / "class-2-regular-elections"
OUTPUT_FILE = BASE_DIR / "reports" / "election" / "senate-results.html"


def load_state_file(filepath):
    """Load a state JSON file and return normalized candidate data."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        candidates = {}
        for chapter in data.get('chapters', []):
            party = chapter.get('name', 'Unknown')
            topics = chapter.get('topics', [])
            candidates[party] = [t for t in topics if t != "No candidates declared"]

        return candidates
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}


def get_all_candidates(candidates_dict):
    """Flatten all candidates into a single set."""
    all_cands = set()
    for party, names in candidates_dict.items():
        for name in names:
            all_cands.add(name)
    return all_cands


def compare_states(old_data, new_data):
    """Compare two state candidate dicts and return differences."""
    old_all = get_all_candidates(old_data)
    new_all = get_all_candidates(new_data)

    added = new_all - old_all
    removed = old_all - new_all
    unchanged = old_all & new_all

    return {
        'added': sorted(added),
        'removed': sorted(removed),
        'unchanged': sorted(unchanged),
        'old_count': len(old_all),
        'new_count': len(new_all)
    }


def get_party_class(name):
    """Return CSS class based on party indicator in name."""
    if '(R)' in name:
        return 'party-R'
    elif '(D)' in name:
        return 'party-D'
    elif '(I)' in name or '(G)' in name or '(L)' in name:
        return 'party-I'
    return ''


def generate_html_report(results):
    """Generate the HTML comparison report."""

    total_added = sum(len(r['added']) for r in results.values())
    total_removed = sum(len(r['removed']) for r in results.values())
    states_with_changes = sum(1 for r in results.values() if r['added'] or r['removed'])
    total_states = len(results)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Senate Candidate Comparison Report</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1100px;
            margin: 0 auto;
            padding: 2rem;
            background: #f5f5f5;
        }}
        header {{
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }}
        h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .subtitle {{ opacity: 0.9; font-size: 0.95rem; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: white;
            padding: 1.25rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-number {{ font-size: 2rem; font-weight: bold; }}
        .stat-number.green {{ color: #38a169; }}
        .stat-number.red {{ color: #c53030; }}
        .stat-number.blue {{ color: #3182ce; }}
        .stat-label {{ font-size: 0.8rem; color: #666; margin-top: 0.25rem; }}
        h2 {{
            background: #1a365d;
            color: white;
            padding: 1rem 1.5rem;
            margin: 2rem 0 0 0;
            border-radius: 8px 8px 0 0;
            font-size: 1.1rem;
        }}
        .section {{
            background: white;
            border-radius: 0 0 8px 8px;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .state-row {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e2e8f0;
            display: grid;
            grid-template-columns: 120px 1fr 1fr 80px 80px;
            gap: 1rem;
            align-items: start;
        }}
        .state-row:last-child {{ border-bottom: none; }}
        .state-row.no-change {{ background: #f7fafc; }}
        .state-row.has-change {{ background: #fffaf0; }}
        .state-name {{
            font-weight: 600;
            color: #1a365d;
        }}
        .candidates {{
            font-size: 0.85rem;
        }}
        .added {{ color: #22543d; }}
        .removed {{ color: #742a2a; }}
        .count {{
            text-align: center;
            font-size: 0.9rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.1rem 0.4rem;
            border-radius: 3px;
            font-size: 0.7rem;
            font-weight: 600;
        }}
        .badge-add {{ background: #c6f6d5; color: #22543d; }}
        .badge-remove {{ background: #fed7d7; color: #742a2a; }}
        .party-R {{ color: #c53030; }}
        .party-D {{ color: #2b6cb0; }}
        .party-I {{ color: #805ad5; }}
        .table-header {{
            background: #edf2f7;
            padding: 0.75rem 1.5rem;
            display: grid;
            grid-template-columns: 120px 1fr 1fr 80px 80px;
            gap: 1rem;
            font-weight: 600;
            font-size: 0.85rem;
            color: #4a5568;
            border-bottom: 2px solid #cbd5e0;
        }}
        .note {{
            background: #ebf8ff;
            border-left: 4px solid #3182ce;
            padding: 1rem;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.85rem;
        }}
        .legend {{
            display: flex;
            gap: 2rem;
            margin: 1rem 0;
            font-size: 0.85rem;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 0.5rem; }}
    </style>
</head>
<body>
    <header>
        <h1>U.S. Senate Candidate Comparison Report</h1>
        <div class="subtitle">Comparing: Server (quarex.org) vs Local (updated Feb 6, 2026)</div>
        <div class="subtitle">Class 2 Regular Elections (33 Races) | Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}</div>
    </header>

    <div class="summary">
        <div class="stat-card">
            <div class="stat-number blue">{total_states}</div>
            <div class="stat-label">Total Senate Races</div>
        </div>
        <div class="stat-card">
            <div class="stat-number" style="color:#805ad5;">{states_with_changes}</div>
            <div class="stat-label">States with Changes</div>
        </div>
        <div class="stat-card">
            <div class="stat-number green">+{total_added}</div>
            <div class="stat-label">Candidates Added</div>
        </div>
        <div class="stat-card">
            <div class="stat-number red">-{total_removed}</div>
            <div class="stat-label">Candidates Removed</div>
        </div>
    </div>

    <div class="note">
        <strong>Comparison Details:</strong><br>
        <strong>SERVER:</strong> <code>C:/Users/peter/Downloads/class-2-regular-elections/</code> (from quarex.org)<br>
        <strong>LOCAL:</strong> <code>libraries/politician-libraries/us-senate-2026-complete/class-2-regular-elections/</code> (updated Feb 6)
    </div>

    <div class="legend">
        <div class="legend-item"><span class="badge badge-add">+Added</span> New candidate in local version</div>
        <div class="legend-item"><span class="badge badge-remove">-Removed</span> Candidate removed/withdrew</div>
    </div>

    <h2>All States Comparison</h2>
    <div class="section">
        <div class="table-header">
            <div>State</div>
            <div>Added (in local)</div>
            <div>Removed (from server)</div>
            <div>Old</div>
            <div>New</div>
        </div>
'''

    for state in sorted(results.keys()):
        data = results[state]
        has_change = data['added'] or data['removed']
        row_class = 'has-change' if has_change else 'no-change'

        added_html = ''
        if data['added']:
            added_items = []
            for c in data['added']:
                party_class = get_party_class(c)
                added_items.append(f'<span class="{party_class}">{c}</span>')
            added_html = ', '.join(added_items)
        else:
            added_html = '<span style="color:#a0aec0;">—</span>'

        removed_html = ''
        if data['removed']:
            removed_items = []
            for c in data['removed']:
                party_class = get_party_class(c)
                removed_items.append(f'<span class="{party_class}">{c}</span>')
            removed_html = ', '.join(removed_items)
        else:
            removed_html = '<span style="color:#a0aec0;">—</span>'

        html += f'''        <div class="state-row {row_class}">
            <div class="state-name">{state}</div>
            <div class="candidates added">{added_html}</div>
            <div class="candidates removed">{removed_html}</div>
            <div class="count">{data['old_count']}</div>
            <div class="count">{data['new_count']}</div>
        </div>
'''

    html += '''    </div>

    <footer>
        Generated by Quarex Election Comparison Tool | quarex.org
    </footer>
</body>
</html>
'''

    return html


def main():
    print("Senate Candidate Comparison Tool")
    print("=" * 50)
    print(f"OLD: {OLD_DIR}")
    print(f"NEW: {NEW_DIR}")
    print()

    results = {}

    old_files = list(OLD_DIR.glob("*.json"))
    old_files = [f for f in old_files if not f.name.startswith('_')]

    print(f"Found {len(old_files)} state files to compare")
    print()

    for old_file in sorted(old_files):
        state_name = old_file.stem.replace('-', ' ').title()
        new_file = NEW_DIR / old_file.name

        old_data = load_state_file(old_file)

        if new_file.exists():
            new_data = load_state_file(new_file)
        else:
            print(f"  WARNING: {old_file.name} not found in new directory")
            new_data = {}

        comparison = compare_states(old_data, new_data)
        results[state_name] = comparison

        if comparison['added'] or comparison['removed']:
            print(f"{state_name}:")
            if comparison['added']:
                print(f"  + Added: {', '.join(comparison['added'])}")
            if comparison['removed']:
                print(f"  - Removed: {', '.join(comparison['removed'])}")

    html = generate_html_report(results)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print()
    print(f"Report generated: {OUTPUT_FILE}")

    total_added = sum(len(r['added']) for r in results.values())
    total_removed = sum(len(r['removed']) for r in results.values())
    states_with_changes = sum(1 for r in results.values() if r['added'] or r['removed'])

    print()
    print("Summary:")
    print(f"  States compared: {len(results)}")
    print(f"  States with changes: {states_with_changes}")
    print(f"  Total candidates added: {total_added}")
    print(f"  Total candidates removed: {total_removed}")


if __name__ == "__main__":
    main()
