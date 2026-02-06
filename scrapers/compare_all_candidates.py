#!/usr/bin/env python3
"""
Compare all candidate data (House, Senate, Governor) between server backup and local versions.
Generates a comprehensive HTML report showing additions, removals, and changes.
"""

import json
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(r"E:\projects\websites\Quarex")
BACKUP_DIR = BASE_DIR / "libraries" / "politician-libraries as of 2-6-26"
LOCAL_DIR = BASE_DIR / "libraries" / "politician-libraries"
OUTPUT_FILE = BASE_DIR / "reports" / "election" / "candidate-changes-2026-02-06.html"

# Election type configurations
ELECTIONS = {
    'house': {
        'name': 'U.S. House',
        'old_dir': BACKUP_DIR / "us-house-2026-complete" / "2026-states",
        'new_dir': LOCAL_DIR / "us-house-2026-complete" / "2026-states",
        'extract_candidates': 'house'
    },
    'senate': {
        'name': 'U.S. Senate',
        'old_dir': BACKUP_DIR / "us-senate-2026-complete" / "class-2-regular-elections",
        'new_dir': LOCAL_DIR / "us-senate-2026-complete" / "class-2-regular-elections",
        'extract_candidates': 'party'
    },
    'governor': {
        'name': 'Governor',
        'old_dir': BACKUP_DIR / "us-governors-2026" / "2026-gubernatorial-races",
        'new_dir': LOCAL_DIR / "us-governors-2026" / "2026-gubernatorial-races",
        'extract_candidates': 'party'
    }
}


def load_json_file(filepath):
    """Load a JSON file and return its data."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}


def extract_candidates_party(data):
    """Extract candidates from party-based chapters (Senate/Governor)."""
    candidates = set()
    for chapter in data.get('chapters', []):
        for topic in chapter.get('topics', []):
            if topic != "No candidates declared":
                candidates.add(topic)
    return candidates


def extract_candidates_house(data):
    """Extract candidates from House format (districts as chapters)."""
    candidates = set()
    for chapter in data.get('chapters', []):
        district = chapter.get('name', '')
        for topic in chapter.get('topics', []):
            # Include district info for context
            candidates.add(f"{district}: {topic}")
    return candidates


def compare_files(old_file, new_file, extract_type):
    """Compare two files and return differences."""
    old_data = load_json_file(old_file) if old_file.exists() else {}
    new_data = load_json_file(new_file) if new_file.exists() else {}

    if extract_type == 'house':
        old_candidates = extract_candidates_house(old_data)
        new_candidates = extract_candidates_house(new_data)
    else:
        old_candidates = extract_candidates_party(old_data)
        new_candidates = extract_candidates_party(new_data)

    added = new_candidates - old_candidates
    removed = old_candidates - new_candidates

    return {
        'added': sorted(added),
        'removed': sorted(removed),
        'old_count': len(old_candidates),
        'new_count': len(new_candidates)
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


def process_election_type(config):
    """Process all files for an election type."""
    results = {}
    old_dir = config['old_dir']
    new_dir = config['new_dir']
    extract_type = config['extract_candidates']

    if not old_dir.exists():
        print(f"  Warning: {old_dir} not found")
        return results

    # Get all JSON files (exclude manifests and metadata)
    old_files = [f for f in old_dir.glob("*.json")
                 if not f.name.startswith('_') and f.name != 'us_house_2026_complete.json']

    for old_file in sorted(old_files):
        state_name = old_file.stem.replace('-', ' ').title()
        new_file = new_dir / old_file.name

        comparison = compare_files(old_file, new_file, extract_type)

        if comparison['added'] or comparison['removed']:
            results[state_name] = comparison
            print(f"  {state_name}: +{len(comparison['added'])} -{len(comparison['removed'])}")

    return results


def generate_html_report(all_results):
    """Generate the comprehensive HTML comparison report."""

    # Calculate totals
    totals = {'added': 0, 'removed': 0, 'states_changed': 0}
    for election_type, results in all_results.items():
        for state, data in results.items():
            totals['added'] += len(data['added'])
            totals['removed'] += len(data['removed'])
        totals['states_changed'] += len(results)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2026 Candidate Changes Report - February 6, 2026</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
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
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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
            font-size: 1.2rem;
        }}
        h3 {{
            background: #2c5282;
            color: white;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            border-bottom: 1px solid #1a365d;
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
        }}
        .state-row:last-child {{ border-bottom: none; }}
        .state-name {{
            font-weight: 600;
            color: #1a365d;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }}
        .changes {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }}
        .change-group {{
            font-size: 0.85rem;
        }}
        .change-group h4 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}
        .added h4 {{ color: #22543d; }}
        .removed h4 {{ color: #742a2a; }}
        .candidate-list {{
            padding-left: 1rem;
        }}
        .candidate-list li {{
            margin: 0.15rem 0;
        }}
        .party-R {{ color: #c53030; }}
        .party-D {{ color: #2b6cb0; }}
        .party-I {{ color: #805ad5; }}
        .no-changes {{
            color: #718096;
            font-style: italic;
            padding: 1rem 1.5rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 3px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }}
        .badge-add {{ background: #c6f6d5; color: #22543d; }}
        .badge-remove {{ background: #fed7d7; color: #742a2a; }}
        footer {{
            text-align: center;
            padding: 2rem;
            color: #666;
            font-size: 0.85rem;
        }}
        .note {{
            background: #ebf8ff;
            border-left: 4px solid #3182ce;
            padding: 1rem;
            margin: 1rem 0;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>2026 Candidate Changes Report</h1>
        <div class="subtitle">Comparing: Server (Jan 30, 2026) vs Local (Feb 6, 2026)</div>
        <div class="subtitle">Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}</div>
    </header>

    <div class="summary">
        <div class="stat-card">
            <div class="stat-number blue">{totals['states_changed']}</div>
            <div class="stat-label">States/Races Changed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number green">+{totals['added']}</div>
            <div class="stat-label">Candidates Added</div>
        </div>
        <div class="stat-card">
            <div class="stat-number red">-{totals['removed']}</div>
            <div class="stat-label">Candidates Removed</div>
        </div>
    </div>

    <div class="note">
        <strong>Comparison Details:</strong><br>
        <strong>OLD (Server):</strong> <code>politician-libraries as of 2-6-26/</code><br>
        <strong>NEW (Local):</strong> <code>politician-libraries/</code> (updated Feb 6, 2026)
    </div>
'''

    # Generate sections for each election type
    for election_key, config in ELECTIONS.items():
        results = all_results.get(election_key, {})
        election_name = config['name']

        html += f'''
    <h2>{election_name} Changes</h2>
    <div class="section">
'''

        if not results:
            html += '        <div class="no-changes">No changes detected</div>\n'
        else:
            for state in sorted(results.keys()):
                data = results[state]
                added_count = len(data['added'])
                removed_count = len(data['removed'])

                html += f'''        <div class="state-row">
            <div class="state-name">{state}
                <span class="badge badge-add">+{added_count}</span>
                <span class="badge badge-remove">-{removed_count}</span>
            </div>
            <div class="changes">
'''

                # Added candidates
                html += '                <div class="change-group added">\n'
                html += '                    <h4>Added</h4>\n'
                if data['added']:
                    html += '                    <ul class="candidate-list">\n'
                    for c in data['added']:
                        party_class = get_party_class(c)
                        html += f'                        <li class="{party_class}">{c}</li>\n'
                    html += '                    </ul>\n'
                else:
                    html += '                    <span style="color:#a0aec0;">None</span>\n'
                html += '                </div>\n'

                # Removed candidates
                html += '                <div class="change-group removed">\n'
                html += '                    <h4>Removed</h4>\n'
                if data['removed']:
                    html += '                    <ul class="candidate-list">\n'
                    for c in data['removed']:
                        party_class = get_party_class(c)
                        html += f'                        <li class="{party_class}">{c}</li>\n'
                    html += '                    </ul>\n'
                else:
                    html += '                    <span style="color:#a0aec0;">None</span>\n'
                html += '                </div>\n'

                html += '''            </div>
        </div>
'''

        html += '    </div>\n'

    html += '''
    <footer>
        Generated by Quarex Election Comparison Tool | quarex.org
    </footer>
</body>
</html>
'''

    return html


def main():
    print("=" * 60)
    print("2026 Candidate Comparison Report Generator")
    print("=" * 60)
    print(f"OLD: {BACKUP_DIR}")
    print(f"NEW: {LOCAL_DIR}")
    print()

    all_results = {}

    for election_key, config in ELECTIONS.items():
        print(f"\nProcessing {config['name']}...")
        results = process_election_type(config)
        all_results[election_key] = results
        print(f"  {len(results)} states with changes")

    # Generate HTML report
    html = generate_html_report(all_results)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print()
    print("=" * 60)
    print(f"Report generated: {OUTPUT_FILE}")
    print()

    # Summary
    total_added = sum(len(d['added']) for r in all_results.values() for d in r.values())
    total_removed = sum(len(d['removed']) for r in all_results.values() for d in r.values())
    total_states = sum(len(r) for r in all_results.values())

    print("Summary:")
    print(f"  States/races with changes: {total_states}")
    print(f"  Total candidates added: {total_added}")
    print(f"  Total candidates removed: {total_removed}")


if __name__ == "__main__":
    main()
