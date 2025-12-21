"""
Quarex Governor Candidate Scraper (2026)
Scrapes Ballotpedia's master candidate list for all 2026 Gubernatorial races.

This uses the centralized "List of candidates" table on the main 2026 Gubernatorial
elections page, which is more reliable than scraping individual state pages.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
import config

# URL for the master candidate list
GOVERNOR_2026_URL = "https://ballotpedia.org/Gubernatorial_elections,_2026"


def scrape_all_candidates():
    """
    Scrape all 2026 Governor candidates from Ballotpedia's master list.

    Returns:
        dict: {state: {'republican': [], 'democratic': [], 'other': []}}
    """
    print(f"Fetching master candidate list from Ballotpedia...")

    headers = {"User-Agent": config.USER_AGENT}
    response = requests.get(GOVERNOR_2026_URL, headers=headers, timeout=60)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    # Find the "List of candidates" panel
    candidates_panel = soup.find('div', id='elections-listofcandidates-2')

    if not candidates_panel:
        raise Exception("Could not find candidates panel on Ballotpedia page")

    all_candidates = {}

    # Find all state tables within the panel
    for table in candidates_panel.find_all('table', class_='widget-table'):
        caption = table.find('caption')
        if not caption:
            continue

        # Extract state name from caption like "Alabama Governor Candidates - 2026"
        caption_text = caption.get_text(strip=True)
        match = re.match(r'([A-Za-z ]+) Governor Candidates', caption_text)
        if not match:
            continue

        state = match.group(1).strip()
        all_candidates[state] = {'republican': [], 'democratic': [], 'other': []}

        # Parse each row in the table
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) < 4:
                continue

            # Get candidate name from first cell
            name_cell = cells[0]
            name_link = name_cell.find('a')
            if not name_link:
                continue
            name = name_link.get_text(strip=True)

            # Check status - skip withdrawn/lost candidates
            status_cell = cells[3]
            status_text = status_cell.get_text(strip=True).lower()
            if 'withdrew' in status_text or 'lost' in status_text:
                continue

            # Get party from second cell
            party_cell = cells[1]
            party_span = party_cell.find('span', class_='party-affiliation')
            if party_span:
                party_classes = party_span.get('class', [])
                party_text = party_span.get_text(strip=True).lower()

                if 'dot-Republican' in party_classes or 'republican' in party_text:
                    all_candidates[state]['republican'].append(f'{name} (R)')
                elif 'dot-Democratic' in party_classes or 'democrat' in party_text:
                    all_candidates[state]['democratic'].append(f'{name} (D)')
                else:
                    # Independent, Libertarian, Green, etc.
                    all_candidates[state]['other'].append(f'{name} (I)')

    return all_candidates


def build_library_json(all_candidates):
    """
    Build the library JSON structure from scraped candidates.

    Args:
        all_candidates: dict from scrape_all_candidates()

    Returns:
        dict: Library JSON structure
    """
    library = {
        "library": "US Governors 2026",
        "library_type": "candidates",
        "description": "All 2026 gubernatorial races with declared candidates. Auto-generated from Ballotpedia master list.",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "source": "Ballotpedia",
        "shelves": [
            {"name": "2026 Gubernatorial Races", "books": []}
        ]
    }

    # Sort states alphabetically and build books
    for state in sorted(all_candidates.keys()):
        data = all_candidates[state]

        book = {
            "name": state,
            "chapters": [
                {"name": "Republican", "topics": data['republican'] or ["No candidates declared"]},
                {"name": "Democratic", "topics": data['democratic'] or ["No candidates declared"]}
            ]
        }

        # Add Independent/Other chapter if there are any
        if data['other']:
            book["chapters"].append({"name": "Independent/Other", "topics": data['other']})

        library["shelves"][0]["books"].append(book)

    return library


def run_scraper(auto_upload=False):
    """
    Run the Governor candidate scraper.

    Args:
        auto_upload: If True, upload results to server after scraping
    """
    print("\n" + "=" * 60)
    print("Quarex Governor Candidate Scraper (2026)")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    os.makedirs(config.LOCAL_BACKUP_DIR, exist_ok=True)
    output_file = os.path.join(config.LOCAL_CANDIDATE_DIR, "us-governors-2026", "us_governors_2026.json")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Scrape all candidates from master list
    all_candidates = scrape_all_candidates()

    # Print summary
    print(f"\nFound {len(all_candidates)} states/territories:")
    total_r = 0
    total_d = 0
    total_i = 0

    for state in sorted(all_candidates.keys()):
        data = all_candidates[state]
        r = len(data['republican'])
        d = len(data['democratic'])
        i = len(data['other'])
        total_r += r
        total_d += d
        total_i += i
        print(f"  {state}: R={r} D={d} I={i}")

    print(f"\nTotal candidates: {total_r + total_d + total_i}")
    print(f"  Republicans: {total_r}")
    print(f"  Democrats: {total_d}")
    print(f"  Independent/Other: {total_i}")

    # Build and save library JSON
    library = build_library_json(all_candidates)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(library, f, indent=2)
    print(f"\nSaved: {output_file}")

    if auto_upload:
        from uploader import upload_single_file
        upload_single_file("us_governors_2026.json")

    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape 2026 Governor candidates from Ballotpedia")
    parser.add_argument("--upload", action="store_true", help="Upload results to server")
    args = parser.parse_args()
    run_scraper(auto_upload=args.upload)
