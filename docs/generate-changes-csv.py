import subprocess
import re
import csv
import sys

# Get git diff
result = subprocess.run(
    ['git', 'diff', 'libraries/politician-libraries/us-house-2026-complete/2026-states/'],
    capture_output=True,
    text=True,
    cwd=r'E:\projects\websites\Quarex'
)

lines = result.stdout.split('\n')

changes = []
current_state = ''
current_district = ''

for line in lines:
    # Match file path
    m = re.search(r'2026-states/([^/]+)/([^.]+)\.json', line)
    if m:
        current_state = m.group(1).replace('-', ' ').title()
        current_district = m.group(2).upper()
        continue

    # Skip diff headers
    if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
        continue

    # Match removed candidates (lines starting with -)
    if line.startswith('-'):
        m = re.search(r'"([^"]+)\s*\(([RDILG])\)"', line)
        if m:
            name = m.group(1).strip()
            party = m.group(2)
            if 'No candidates' not in name:
                changes.append({
                    'State': current_state,
                    'District': current_district,
                    'Change': 'Removed',
                    'Candidate': f'{name} ({party})',
                    'Party': party
                })

    # Match added candidates (lines starting with +)
    elif line.startswith('+'):
        m = re.search(r'"([^"]+)\s*\(([RDILG])\)"', line)
        if m:
            name = m.group(1).strip()
            party = m.group(2)
            if 'No candidates' not in name:
                changes.append({
                    'State': current_state,
                    'District': current_district,
                    'Change': 'Added',
                    'Candidate': f'{name} ({party})',
                    'Party': party
                })

# Write CSV
output_path = r'E:\projects\websites\Quarex\docs\house-candidate-changes-2026-01-17.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['State', 'District', 'Change', 'Candidate', 'Party'])
    writer.writeheader()
    writer.writerows(changes)

print(f'Wrote {len(changes)} changes to {output_path}')
