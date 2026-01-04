"""
Quarex House Candidate Scraper (2026)
Scrapes Ballotpedia for all 2026 House races by state.

Unlike Senate/Governor which have master candidate lists, House requires
scraping each state's page individually.

Usage:
    python house_scraper.py                    # Scrape all states
    python house_scraper.py --states TX CA    # Scrape specific states
    python house_scraper.py --batch 1         # Scrape states 1-10
    python house_scraper.py --batch 2         # Scrape states 11-20
    python house_scraper.py --batch 3         # Scrape states 21-30
    python house_scraper.py --batch 4         # Scrape states 31-40
    python house_scraper.py --batch 5         # Scrape states 41-50
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
from datetime import datetime
import config

# All 50 states in order
ALL_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

# State abbreviations
STATE_ABBREVS = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

# Districts per state (2020 census)
DISTRICTS_PER_STATE = {
    "Alabama": 7, "Alaska": 1, "Arizona": 9, "Arkansas": 4, "California": 52,
    "Colorado": 8, "Connecticut": 5, "Delaware": 1, "Florida": 28, "Georgia": 14,
    "Hawaii": 2, "Idaho": 2, "Illinois": 17, "Indiana": 9, "Iowa": 4,
    "Kansas": 4, "Kentucky": 6, "Louisiana": 6, "Maine": 2, "Maryland": 8,
    "Massachusetts": 9, "Michigan": 13, "Minnesota": 8, "Mississippi": 4, "Missouri": 8,
    "Montana": 2, "Nebraska": 3, "Nevada": 4, "New Hampshire": 2, "New Jersey": 12,
    "New Mexico": 3, "New York": 26, "North Carolina": 14, "North Dakota": 1, "Ohio": 15,
    "Oklahoma": 5, "Oregon": 6, "Pennsylvania": 17, "Rhode Island": 2, "South Carolina": 7,
    "South Dakota": 1, "Tennessee": 9, "Texas": 38, "Utah": 4, "Vermont": 1,
    "Virginia": 11, "Washington": 10, "West Virginia": 2, "Wisconsin": 8, "Wyoming": 1
}


def get_state_url(state):
    """Get Ballotpedia URL for a state's House elections."""
    state_formatted = state.replace(" ", "_")
    return f"https://ballotpedia.org/United_States_House_of_Representatives_elections_in_{state_formatted},_2026"


def scrape_state(state):
    """
    Scrape all House districts for a state.

    Returns:
        dict: {district: {'republican': [], 'democratic': [], 'other': []}}
    """
    url = get_state_url(state)
    abbrev = STATE_ABBREVS[state]
    num_districts = DISTRICTS_PER_STATE[state]

    print(f"  Fetching {state} ({num_districts} districts)...")

    headers = {"User-Agent": config.USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"    ERROR: Failed to fetch {state}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'lxml')

    districts = {}

    # For at-large states (1 district)
    if num_districts == 1:
        district_name = f"{abbrev}-AL"
        districts[district_name] = {'republican': [], 'democratic': [], 'other': []}

        # Parse candidates from page
        candidates = parse_candidates_from_page(soup, state, is_at_large=True)
        if candidates:
            districts[district_name] = candidates

        return districts

    # For multi-district states
    for district_num in range(1, num_districts + 1):
        district_name = f"{abbrev}-{district_num:02d}"
        districts[district_name] = {'republican': [], 'democratic': [], 'other': []}

    # Parse all candidates and assign to districts
    parse_multi_district_candidates(soup, state, abbrev, districts)

    return districts


def parse_candidates_from_page(soup, state, is_at_large=False):
    """Parse candidates from a state page for at-large districts."""
    candidates = {'republican': [], 'democratic': [], 'other': []}

    # Look for candidate tables or lists
    # Try finding the elections-listofcandidates div first
    candidates_panel = soup.find('div', id=re.compile(r'elections-listofcandidates'))

    if candidates_panel:
        for row in candidates_panel.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            name_cell = cells[0]
            name_link = name_cell.find('a')
            if not name_link:
                continue

            name = name_link.get_text(strip=True)

            # Skip withdrawn candidates
            status_text = row.get_text(strip=True).lower()
            if 'withdrew' in status_text or 'lost' in status_text:
                continue

            # Determine party
            party = determine_party(row)

            if party == 'R':
                candidates['republican'].append(f'{name} (R)')
            elif party == 'D':
                candidates['democratic'].append(f'{name} (D)')
            else:
                candidates['other'].append(f'{name} (I)')

    # If no panel found, try parsing from content
    if not any(candidates.values()):
        candidates = parse_from_content(soup, state)

    return candidates


def parse_multi_district_candidates(soup, state, abbrev, districts):
    """Parse candidates for multi-district states."""

    # Get all text content
    content = soup.find('div', {'id': 'mw-content-text'}) or soup.find('div', class_='mw-parser-output')
    if not content:
        return

    current_district = None

    # Look for district headers and candidate lists
    for element in content.find_all(['h2', 'h3', 'h4', 'table', 'ul', 'p', 'span']):
        text = element.get_text(strip=True)

        # Check for district header
        district_match = re.search(r'District\s*(\d+)', text, re.IGNORECASE)
        if district_match and element.name in ['h2', 'h3', 'h4']:
            district_num = int(district_match.group(1))
            current_district = f"{abbrev}-{district_num:02d}"
            continue

        # If we're in a district section, look for candidates
        if current_district and current_district in districts:
            # Look for links that might be candidate names
            if element.name == 'ul':
                for li in element.find_all('li'):
                    link = li.find('a')
                    if link:
                        name = link.get_text(strip=True)
                        if is_valid_candidate_name(name):
                            party = determine_party_from_context(li)
                            add_candidate(districts[current_district], name, party)

            # Also check tables
            elif element.name == 'table':
                for row in element.find_all('tr'):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 1:
                        for cell in cells:
                            link = cell.find('a')
                            if link:
                                name = link.get_text(strip=True)
                                if is_valid_candidate_name(name):
                                    party = determine_party_from_context(row)
                                    add_candidate(districts[current_district], name, party)


def parse_from_content(soup, state):
    """Fallback parser that looks for candidate patterns in content."""
    candidates = {'republican': [], 'democratic': [], 'other': []}

    content = soup.find('div', {'id': 'mw-content-text'}) or soup.find('div', class_='mw-parser-output')
    if not content:
        return candidates

    # Look for typical candidate list patterns
    for ul in content.find_all('ul'):
        for li in ul.find_all('li'):
            link = li.find('a')
            if link:
                name = link.get_text(strip=True)
                if is_valid_candidate_name(name):
                    party = determine_party_from_context(li)
                    add_candidate(candidates, name, party)

    return candidates


def is_valid_candidate_name(name):
    """Check if a string looks like a candidate name."""
    if not name or len(name) < 3:
        return False

    # Skip common non-name strings
    skip_patterns = [
        'district', 'election', 'primary', 'general', 'candidate',
        'republican', 'democratic', 'independent', 'ballotpedia',
        'edit', 'source', 'citation', 'reference', 'wikipedia',
        'incumbent', 'withdrew', 'lost', 'see also', 'external',
        'united states', 'house of representatives'
    ]

    name_lower = name.lower()
    for pattern in skip_patterns:
        if pattern in name_lower:
            return False

    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False

    # Should look like a name (has spaces or is a single word)
    # Typical names are 2-4 words
    words = name.split()
    if len(words) > 5:
        return False

    return True


def determine_party(element):
    """Determine party from element classes or content."""
    classes = element.get('class', [])
    if isinstance(classes, str):
        classes = [classes]

    text = element.get_text(strip=True).lower()

    # Check for party dots
    for cls in classes:
        if 'Republican' in cls or 'republican' in cls:
            return 'R'
        if 'Democratic' in cls or 'democrat' in cls:
            return 'D'

    # Check content
    if 'republican' in text or '(r)' in text:
        return 'R'
    if 'democrat' in text or '(d)' in text:
        return 'D'

    # Check for party affiliation spans
    party_span = element.find('span', class_=re.compile(r'party'))
    if party_span:
        span_text = party_span.get_text(strip=True).lower()
        if 'republican' in span_text:
            return 'R'
        if 'democrat' in span_text:
            return 'D'

    return 'I'


def determine_party_from_context(element):
    """Determine party from the immediate text context of the element."""
    # Get the text of this element only (not parents)
    text = element.get_text(strip=True).lower()

    # Look for explicit party markers in the immediate text
    if '(republican party)' in text or '(republican)' in text or '(r)' in text:
        return 'R'
    if '(democratic party)' in text or '(democratic)' in text or '(democrat)' in text or '(d)' in text:
        return 'D'
    if '(independent)' in text or '(libertarian)' in text or '(green)' in text:
        return 'I'

    # Check sibling text nodes for party info
    if element.next_sibling:
        sibling_text = str(element.next_sibling).lower()
        if 'republican' in sibling_text:
            return 'R'
        if 'democrat' in sibling_text:
            return 'D'

    # Unknown party
    return None


def add_candidate(district_dict, name, party):
    """Add a candidate to the appropriate party list."""
    # Skip if party unknown
    if party is None:
        return

    if party == 'R':
        formatted = f'{name} (R)'
        if formatted not in district_dict['republican']:
            district_dict['republican'].append(formatted)
    elif party == 'D':
        formatted = f'{name} (D)'
        if formatted not in district_dict['democratic']:
            district_dict['democratic'].append(formatted)
    else:
        formatted = f'{name} (I)'
        if formatted not in district_dict['other']:
            district_dict['other'].append(formatted)


def build_library_json(all_states_data):
    """
    Build the library JSON structure from scraped candidates.

    Args:
        all_states_data: dict {state: {district: {party: [candidates]}}}

    Returns:
        dict: Library JSON structure
    """
    library = {
        "library": "us-house-2026-complete",
        "library_type": "candidates",
        "description": "All 435 House districts with declared 2026 candidates. Auto-generated from Ballotpedia.",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "source": "Ballotpedia",
        "shelves": []
    }

    for state in ALL_STATES:
        if state not in all_states_data:
            continue

        state_data = all_states_data[state]
        num_districts = DISTRICTS_PER_STATE[state]

        shelf = {
            "name": f"{state} ({num_districts} {'district' if num_districts == 1 else 'districts'})",
            "books": []
        }

        # Sort districts
        for district_name in sorted(state_data.keys()):
            district_data = state_data[district_name]

            book = {
                "name": district_name,
                "chapters": [
                    {"name": "Republican", "topics": district_data['republican'] or ["No candidates declared"]},
                    {"name": "Democratic", "topics": district_data['democratic'] or ["No candidates declared"]}
                ]
            }

            if district_data['other']:
                book["chapters"].append({"name": "Independent/Other", "topics": district_data['other']})

            shelf["books"].append(book)

        library["shelves"].append(shelf)

    return library


def load_existing_data():
    """Load existing house data if available."""
    # Prefer the scrapers working file (manually verified)
    working_file = os.path.join(os.path.dirname(__file__), "house_2026_working.json")
    output_file = os.path.join(config.LOCAL_CANDIDATE_DIR, "us-house-2026-complete", "us_house_2026_complete.json")

    for filepath in [working_file, output_file]:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"  Loaded existing data from: {filepath}")
                    return data
            except Exception as e:
                print(f"  Warning: Could not load {filepath}: {e}")

    return None


def convert_library_to_working_format(library_data):
    """Convert library JSON format to working dict format."""
    all_states_data = {}

    for shelf in library_data.get('shelves', []):
        state_match = re.match(r'^([A-Za-z ]+) \(', shelf['name'])
        if not state_match:
            continue

        state_name = state_match.group(1)
        all_states_data[state_name] = {}

        for book in shelf.get('books', []):
            district_name = book['name']
            all_states_data[state_name][district_name] = {
                'republican': [],
                'democratic': [],
                'other': []
            }

            for chapter in book.get('chapters', []):
                topics = chapter.get('topics', [])
                if topics == ["No candidates declared"]:
                    continue

                if chapter['name'] == 'Republican':
                    all_states_data[state_name][district_name]['republican'] = topics
                elif chapter['name'] == 'Democratic':
                    all_states_data[state_name][district_name]['democratic'] = topics
                elif chapter['name'] == 'Independent/Other':
                    all_states_data[state_name][district_name]['other'] = topics

    return all_states_data


def run_scraper(states_to_scrape=None, batch=None):
    """
    Run the House candidate scraper.

    Args:
        states_to_scrape: List of state names to scrape, or None for all
        batch: Batch number (1-5) to scrape 10 states at a time
    """
    print("\n" + "=" * 60)
    print("Quarex House Candidate Scraper (2026)")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Determine which states to scrape
    if batch:
        batch = int(batch)
        start_idx = (batch - 1) * 10
        end_idx = min(batch * 10, len(ALL_STATES))
        states_to_scrape = ALL_STATES[start_idx:end_idx]
        print(f"Batch {batch}: States {start_idx + 1} to {end_idx}")
    elif states_to_scrape is None:
        states_to_scrape = ALL_STATES

    print(f"Scraping {len(states_to_scrape)} states: {', '.join(states_to_scrape)}")

    # Load existing data to merge with
    existing = load_existing_data()
    all_states_data = {}

    if existing:
        all_states_data = convert_library_to_working_format(existing)
        print(f"  Loaded {len(all_states_data)} states from existing data")

    # Scrape each state
    for state in states_to_scrape:
        state_data = scrape_state(state)

        if state_data:
            # Count candidates
            total_r = sum(len(d['republican']) for d in state_data.values())
            total_d = sum(len(d['democratic']) for d in state_data.values())
            total_i = sum(len(d['other']) for d in state_data.values())
            total = total_r + total_d + total_i

            print(f"    Scraped: R={total_r} D={total_d} I={total_i} (total={total})")

            # Validate: should have candidates from both parties in most cases
            # Only update if we got reasonable data (at least some candidates)
            if total > 0 and (total_r > 0 or total_d > 0):
                # Check existing data for comparison
                existing_state = all_states_data.get(state, {})
                existing_r = sum(len(d.get('republican', [])) for d in existing_state.values())
                existing_d = sum(len(d.get('democratic', [])) for d in existing_state.values())

                # Only update if new data looks better or similar
                if total >= (existing_r + existing_d) * 0.5:  # At least 50% of previous
                    all_states_data[state] = state_data
                    print(f"    [OK] Updated {state}")
                else:
                    print(f"    [SKIP] Keeping existing data (new data looks incomplete)")
            else:
                print(f"    [SKIP] No valid candidates found")

        # Be polite to Ballotpedia
        time.sleep(config.REQUEST_DELAY)

    # Build and save library JSON
    output_dir = os.path.join(config.LOCAL_CANDIDATE_DIR, "us-house-2026-complete")
    os.makedirs(output_dir, exist_ok=True)

    library = build_library_json(all_states_data)

    # Save to working file in scrapers dir
    working_file = os.path.join(os.path.dirname(__file__), "house_2026_working.json")
    with open(working_file, 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=2)
    print(f"\nSaved working file: {working_file}")

    # Also save to library location
    output_file = os.path.join(output_dir, "us_house_2026_complete.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=2)
    print(f"Saved library file: {output_file}")

    # Print summary
    print(f"\nSummary:")
    print(f"  States scraped: {len(states_to_scrape)}")
    total_districts = sum(DISTRICTS_PER_STATE[s] for s in states_to_scrape if s in all_states_data)
    print(f"  Districts covered: {total_districts}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape 2026 House candidates from Ballotpedia")
    parser.add_argument("--states", nargs='+', help="Specific states to scrape (e.g., TX CA NY)")
    parser.add_argument("--batch", type=int, choices=[1, 2, 3, 4, 5],
                        help="Batch number (1-5) to scrape 10 states at a time")
    parser.add_argument("--all", action="store_true", help="Scrape all 50 states")

    args = parser.parse_args()

    if args.states:
        # Convert abbreviations to full names if needed
        states = []
        abbrev_to_state = {v: k for k, v in STATE_ABBREVS.items()}
        for s in args.states:
            if s.upper() in abbrev_to_state:
                states.append(abbrev_to_state[s.upper()])
            elif s in ALL_STATES:
                states.append(s)
            else:
                print(f"Unknown state: {s}")
        run_scraper(states_to_scrape=states)
    elif args.batch:
        run_scraper(batch=args.batch)
    elif args.all:
        run_scraper()
    else:
        parser.print_help()
