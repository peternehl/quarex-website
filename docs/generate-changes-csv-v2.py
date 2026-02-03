import subprocess
import json
import os
import csv
from pathlib import Path

base_path = Path(r'E:\projects\websites\Quarex\libraries\politician-libraries\us-house-2026-complete\2026-states')

changes = []

# Get list of all state folders
for state_dir in sorted(base_path.iterdir()):
    if not state_dir.is_dir():
        continue

    state_name = state_dir.name.replace('-', ' ').title()

    for json_file in sorted(state_dir.glob('*.json')):
        if json_file.name == '_manifest.json':
            continue

        district = json_file.stem.upper()

        # Get old version from git
        rel_path = json_file.relative_to(r'E:\projects\websites\Quarex')
        result = subprocess.run(
            ['git', 'show', f'HEAD:{rel_path.as_posix()}'],
            capture_output=True,
            text=True,
            cwd=r'E:\projects\websites\Quarex'
        )

        # Parse old candidates
        old_candidates = set()
        if result.returncode == 0 and result.stdout.strip():
            try:
                old_data = json.loads(result.stdout)
                for chapter in old_data.get('chapters', []):
                    for topic in chapter.get('topics', []):
                        if 'No candidates' not in topic:
                            old_candidates.add(topic)
            except json.JSONDecodeError:
                pass

        # Parse new candidates
        new_candidates = set()
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
                for chapter in new_data.get('chapters', []):
                    for topic in chapter.get('topics', []):
                        if 'No candidates' not in topic:
                            new_candidates.add(topic)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

        # Find true removals (in old but not in new)
        for candidate in sorted(old_candidates - new_candidates):
            party = candidate[-2] if candidate.endswith(')') else ''
            changes.append({
                'State': state_name,
                'District': district,
                'Change': 'Removed',
                'Candidate': candidate,
                'Party': party
            })

        # Find true additions (in new but not in old)
        for candidate in sorted(new_candidates - old_candidates):
            party = candidate[-2] if candidate.endswith(')') else ''
            changes.append({
                'State': state_name,
                'District': district,
                'Change': 'Added',
                'Candidate': candidate,
                'Party': party
            })

# Write CSV
output_path = r'E:\projects\websites\Quarex\docs\house-candidate-changes-v2.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['State', 'District', 'Change', 'Candidate', 'Party'])
    writer.writeheader()
    writer.writerows(changes)

print(f'Wrote {len(changes)} true changes to {output_path}')

# Summary
removed = sum(1 for c in changes if c['Change'] == 'Removed')
added = sum(1 for c in changes if c['Change'] == 'Added')
print(f'  - {removed} candidates removed')
print(f'  - {added} candidates added')
