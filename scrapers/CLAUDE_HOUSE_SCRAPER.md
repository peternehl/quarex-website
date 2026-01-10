# Claude AI House Scraper Workflow

The Python scraper is unreliable for ~16 states due to HTML parsing issues. Use this Claude-based workflow instead.

## Weekly Command

Just paste this to Claude:

```
Scrape all 50 states for House 2026 candidates using WebFetch on these URLs:
https://ballotpedia.org/United_States_House_of_Representatives_elections_in_<STATE>,_2026

For each state, extract candidates by district in format: "Name (R)", "Name (D)", "Name (L)", "Name (I)"

Update the JSON files in libraries/politician-libraries/us-house-2026-complete/2026-states/

Then rebuild the discovery index.
```

## States List (for reference)

Alabama, Alaska, Arizona, Arkansas, California, Colorado, Connecticut, Delaware, Florida, Georgia, Hawaii, Idaho, Illinois, Indiana, Iowa, Kansas, Kentucky, Louisiana, Maine, Maryland, Massachusetts, Michigan, Minnesota, Mississippi, Missouri, Montana, Nebraska, Nevada, New Hampshire, New Jersey, New Mexico, New York, North Carolina, North Dakota, Ohio, Oklahoma, Oregon, Pennsylvania, Rhode Island, South Carolina, South Dakota, Tennessee, Texas, Utah, Vermont, Virginia, Washington, West Virginia, Wisconsin, Wyoming

## URL Pattern

Replace spaces with underscores:
- `New_York` not `New York`
- `North_Carolina` not `North Carolina`
- `West_Virginia` not `West Virginia`

## Output Format

Each state JSON should have:
```json
{
  "book": "State Name",
  "chapters": [
    {
      "name": "XX-01",
      "topics": [
        "Candidate Name (R)",
        "Candidate Name (D)",
        "Candidate Name (L)",
        "Candidate Name (I)"
      ],
      "tags": ["politics", "elections", "house", "state-slug"]
    }
  ]
}
```

## Party Codes
- (R) = Republican
- (D) = Democrat
- (L) = Libertarian
- (G) = Green
- (I) = Independent
- (C) = Constitution
- Other third parties: use full name or abbreviation

## After Scraping

1. Rebuild discovery index:
   ```
   node libraries/_utils/build-discovery-index-v2.js
   ```

2. Upload to server:
   - `libraries/politician-libraries/us-house-2026-complete/2026-states/*.json`
   - `libraries/discovery-index.json`
