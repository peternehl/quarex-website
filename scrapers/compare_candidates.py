import json
from datetime import datetime

def load_candidates(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    candidates = {}

    if 'shelves' in data:
        for shelf in data['shelves']:
            for book in shelf.get('books', []):
                state = book['name']
                candidates[state] = set()
                for chapter in book.get('chapters', []):
                    for topic in chapter.get('topics', []):
                        candidates[state].add(topic)
    elif 'chapters' in data:
        for chapter in data['chapters']:
            state = chapter['name']
            candidates[state] = set()
            for topic in chapter.get('topics', []):
                candidates[state].add(topic)

    return candidates

def compare_files(old_file, new_file):
    old = load_candidates(old_file)
    new = load_candidates(new_file)

    added = []
    removed = []

    all_states = set(old.keys()) | set(new.keys())

    for state in sorted(all_states):
        old_cands = old.get(state, set())
        new_cands = new.get(state, set())

        for c in sorted(new_cands - old_cands):
            added.append((state, c))
        for c in sorted(old_cands - new_cands):
            removed.append((state, c))

    return added, removed

def main():
    gov_added, gov_removed = compare_files('us_governors_2026_backup.json', '../libraries/politician-libraries/us-governors-2026/us_governors_2026.json')
    sen_added, sen_removed = compare_files('us_senate_2026_backup.json', '../libraries/politician-libraries/us-senate-2026-complete/us_senate_2026_complete.json')
    house_added, house_removed = compare_files('us_house_2026_backup.json', '../libraries/politician-libraries/us-house-2026-complete/us_house_2026_complete.json')

    lines = []
    lines.append('2026 Candidate Changes - Week of January 16, 2026')
    lines.append('')
    lines.append('This week\'s update to the Quarex candidate database includes the following changes:')
    lines.append('')
    lines.append('=' * 80)
    lines.append('GOVERNOR RACES')
    lines.append('=' * 80)
    lines.append('')
    lines.append('NEW CANDIDATES (' + str(len(gov_added)) + '):')

    if gov_added:
        current_state = None
        for state, cand in gov_added:
            if state != current_state:
                lines.append('')
                lines.append(state + ':')
                current_state = state
            lines.append('  + ' + cand)
    else:
        lines.append('None')

    lines.append('')
    lines.append('WITHDRAWN/REMOVED (' + str(len(gov_removed)) + '):')

    if gov_removed:
        current_state = None
        for state, cand in gov_removed:
            if state != current_state:
                lines.append('')
                lines.append(state + ':')
                current_state = state
            lines.append('  - ' + cand)
    else:
        lines.append('None')

    lines.append('')
    lines.append('=' * 80)
    lines.append('SENATE RACES')
    lines.append('=' * 80)
    lines.append('')
    lines.append('NEW CANDIDATES (' + str(len(sen_added)) + '):')

    if sen_added:
        current_state = None
        for state, cand in sen_added:
            if state != current_state:
                lines.append('')
                lines.append(state + ':')
                current_state = state
            lines.append('  + ' + cand)
    else:
        lines.append('None')

    lines.append('')
    lines.append('WITHDRAWN/REMOVED (' + str(len(sen_removed)) + '):')

    if sen_removed:
        current_state = None
        for state, cand in sen_removed:
            if state != current_state:
                lines.append('')
                lines.append(state + ':')
                current_state = state
            lines.append('  - ' + cand)
    else:
        lines.append('None')

    lines.append('')
    lines.append('=' * 80)
    lines.append('HOUSE RACES')
    lines.append('=' * 80)
    lines.append('')
    lines.append('NEW CANDIDATES (' + str(len(house_added)) + '):')

    if house_added:
        current_state = None
        for state, cand in house_added:
            if state != current_state:
                lines.append('')
                lines.append(state + ':')
                current_state = state
            lines.append('  + ' + cand)
    else:
        lines.append('None')

    lines.append('')
    lines.append('WITHDRAWN/REMOVED (' + str(len(house_removed)) + '):')

    if house_removed:
        current_state = None
        for state, cand in house_removed:
            if state != current_state:
                lines.append('')
                lines.append(state + ':')
                current_state = state
            lines.append('  - ' + cand)
    else:
        lines.append('None')

    lines.append('')
    lines.append('=' * 80)
    lines.append('SUMMARY')
    lines.append('=' * 80)
    lines.append('')
    lines.append('Total Changes This Week:')
    lines.append('  Governor: +' + str(len(gov_added)) + ' / -' + str(len(gov_removed)))
    lines.append('  Senate:   +' + str(len(sen_added)) + ' / -' + str(len(sen_removed)))
    lines.append('  House:    +' + str(len(house_added)) + ' / -' + str(len(house_removed)))
    lines.append('  ' + '-' * 30)
    total_add = len(gov_added) + len(sen_added) + len(house_added)
    total_rem = len(gov_removed) + len(sen_removed) + len(house_removed)
    lines.append('  Total:    +' + str(total_add) + ' / -' + str(total_rem))
    lines.append('')
    lines.append('Data sourced from Ballotpedia.org')
    lines.append('View all candidates at: https://quarex.org/libraries/c/')
    lines.append('')
    lines.append('=' * 80)

    report = '\n'.join(lines)
    print(report)

    with open('../docs/2026-Candidate-Changes-Week-of-Jan-16.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print('')
    print('Saved to docs/2026-Candidate-Changes-Week-of-Jan-16.txt')

if __name__ == '__main__':
    main()
