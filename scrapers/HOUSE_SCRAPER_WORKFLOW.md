# House Scraper Weekly Workflow

## Overview
The House scraper is more complex than Senate/Governor because Ballotpedia doesn't have a master candidate list. Each state page must be scraped individually.

## Quick Weekly Update

### Step 1: Run the scraper in batches (10 states each)
```bash
cd E:/projects/websites/Quarex/scrapers
python house_scraper.py --batch 1
python house_scraper.py --batch 2
python house_scraper.py --batch 3
python house_scraper.py --batch 4
python house_scraper.py --batch 5
```

Batches:
- Batch 1: Alabama - Georgia (states 1-10)
- Batch 2: Hawaii - Maryland (states 11-20)
- Batch 3: Massachusetts - New Jersey (states 21-30)
- Batch 4: New Mexico - South Carolina (states 31-40)
- Batch 5: South Dakota - Wyoming (states 41-50)

The scraper will:
- Load existing data from `house_2026_working.json`
- Only update states where new data looks valid (has R and D candidates)
- Skip states where scraping fails (keeps existing data)
- Save updated working file

### Step 2: Convert to flat format for server
```bash
python convert_house_to_flat.py
```

This creates individual state JSON files in the server format at:
`libraries/politician-libraries/us-house-2026-complete/2026-states/`

### Step 3: (Optional) Merge with server data
If server has better data for some states:
```bash
python convert_house_to_flat.py --merge "C:/Users/peter/Downloads/2026-states"
```

### Step 4: Rebuild discovery index
```bash
cd E:/projects/websites/Quarex
node libraries/_utils/build-discovery-index-v2.js
```

### Step 5: Upload to server
Upload these folders/files:
- `libraries/politician-libraries/us-house-2026-complete/2026-states/*.json`
- `libraries/discovery-index.json`

## File Structure

### Local (scraper working format)
```
scrapers/house_2026_working.json    <- Party-separated format (R/D/I chapters)
```

### Server (flat format)
```
libraries/politician-libraries/us-house-2026-complete/
├── 2026-states/
│   ├── _manifest.json
│   ├── alabama.json      <- Each state is a book
│   ├── alaska.json       <- Districts are chapters
│   └── ...               <- All candidates mixed (not by party)
└── _manifest.json
```

## Known Issues

States that often fail to scrape (keep server data):
- Texas (320 candidates)
- North Carolina (83 candidates)
- Ohio (49 candidates)
- Illinois, Kentucky, Maryland, Tennessee, West Virginia (variable)

These states have different page structures on Ballotpedia that the scraper doesn't handle well.

## Troubleshooting

If scraper gets bad data (wrong party assignments):
1. Check the Ballotpedia page structure changed
2. Restore working file: `git checkout scrapers/house_2026_working.json`
3. Re-run with merge from server data

## Senate & Governor (simpler)

These have master candidate lists and are much easier:
```bash
cd E:/projects/websites/Quarex/scrapers
python senate_scraper.py
python governor_scraper.py
python convert_to_individual.py --senate --governor
```
