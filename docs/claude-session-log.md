# Claude Session Log

**Last Updated**: 2026-01-09
**Current Project**: Quarex book on Decision Making

---

## Session: 2026-01-09

### Goal
Create a Quarex book adapted for decision making

### Context
- User was working with Claude on this before a crash
- The file being created was lost
- Need to recreate from scratch

### Concept: Decision Helper Tool (ask-decision.html + ask-decision.php)

**UI Components:**
1. **Decision Type Dropdown** - ~12+ standard decision categories
2. **Timeframe Dropdown** - When decision needs to be made
3. **Text Input** - User describes their specific decision
4. **Branching Explorer** - Navigate facets of the decision with back button

**Key Features:**
- Quarex methodology applied to decision-making
- Explore every facet of a decision
- Back button to revisit/revise previous facets
- Structured approach to complex choices

### Progress
- [x] Set up session logging system
- [x] Gather requirements for decision-making tool
- [x] Design decision type categories
- [x] Create ask-decision.html (Quarex-styled)
- [x] Create ask-decision.php (Gemini-powered)
- [x] Add dynamic AI-generated follow-up questions
- [x] Add exploration history sidebar
- [x] Add custom question text input
- [x] Add homepage link (Decision Helper button)
- [x] Adjust AI tone to be direct and analytical (less touchy-feely)
- [x] Add mixed follow-ups (decision choices + exploration questions)
- [x] Add Political/Policy decision type with governance-specific facets
- [ ] User testing

### Files Created/Modified
1. `ask-decision/ask-decision.html` - Frontend with Quarex styling
2. `api/ask-decision.php` - Backend API using Gemini
3. `index.html` - Added Decision Helper button

### Decision Types Implemented
- Career / Job
- Financial / Investment
- Relationship / Family
- Health / Medical
- Education / Learning
- Housing / Relocation
- Business / Entrepreneurship
- Legal / Contracts
- Technology / Purchases
- Lifestyle / Habits
- Ethical / Moral Dilemma
- Creative / Project Direction
- Other

### Timeframes Implemented
- Immediate (today)
- This week
- This month
- This quarter
- This year
- Long-term (1+ years)
- No deadline

### Facet Structure
Initial facets: Pros, Cons, Risks, Alternatives, Values, Stakeholders
Each facet branches into sub-facets (e.g., Pros → Short-term, Long-term, Hidden, Best Case)

### Key Decisions
- Matched Quarex.org visual style (Playfair Display headings, Inter body, blue gradients, iceberg background)
- Used branching facet system for deep exploration
- Breadcrumb navigation for history tracking
- Back button to revisit previous facets
- Dynamic follow-ups: AI generates 5 contextual questions after each response
- Sidebar preserves ALL unexplored questions from every step
- Custom question input lets users ask their own follow-ups
- Tool helps explore decisions, does NOT make them for the user
- AI tone: Direct and analytical, avoids emotional language and platitudes

### Final Feature Set
1. **Setup Form**: Decision type dropdown, timeframe dropdown, description textarea
2. **Explorer Panel**: AI analysis with clickable follow-up buttons
3. **History Sidebar**: Shows all steps with explored/unexplored questions
4. **Custom Input**: Text box for user's own questions
5. **Navigation**: Back button, breadcrumbs, Start Over

### Files to Upload to Server
- `index.html`
- `ask-decision/ask-decision.html`
- `api/ask-decision.php`

---

## Session: 2026-01-09 (Part 2) - Weekly Candidate Scraper Run

### Goal
Run weekly candidate scrapers for Governor, Senate, and House races

### Context
- Weekly scraper maintenance task
- Python HTML scraper unreliable for ~16 states
- Switched to AI-based WebFetch scraping for all 50 states

### Progress
- [x] Ran Governor scraper (369 candidates, 39 states)
- [x] Ran Senate scraper (291 candidates, 33 states)
- [x] Ran House Python scraper (5 batches, 16 states skipped due to bad data)
- [x] Identified Python scraper too brittle for HTML parsing
- [x] Created CLAUDE_HOUSE_SCRAPER.md workflow doc for AI-based scraping
- [x] Ran WebFetch AI scraper for all 50 states
- [x] Updated state JSON files with fresh data
- [x] Rebuilt discovery index (3,158 chapters, 363 tags)

### Key Updates Made
| State | Changes |
|-------|---------|
| Arkansas | Fixed AR-02 and AR-04 (added actual candidates) |
| Rhode Island | Reordered candidates |
| California | Added CA-16 Jotham Stein (I), CA-37 Steve Hill (I), CA-49 Julian Arellano (I), fixed CA-41 |
| Florida | Added FL-03 third party candidates, FL-04 independents, FL-11 Libertarian, FL-18 NPA |
| Arizona | Added AZ-01 Victor Weintraub (D), AZ-05 Mike Gross (R), AZ-06 Carter Weeks (D) |
| Georgia | Added GA-02 Brandon Daley (Communist) |
| Maryland | Added MD-01 Victor Guidice (D), fixed MD-05 (removed Steny Hoyer, added Walter Kirkland) |
| Minnesota | Removed MN-01 Andy Smith, fixed MN-02, removed MN-08 Chad McKenna |
| North Carolina | Verified 83+ candidates across 14 districts |
| Vermont | Verified Becca Balint (D), Mark Coester (R), Andrew Giusto (Unity) |

### Key Decision
- **Python scraper deprecated** for House races
- **AI WebFetch scraper** (CLAUDE_HOUSE_SCRAPER.md) is now the standard approach
- URL pattern: `https://ballotpedia.org/United_States_House_of_Representatives_elections_in_<STATE>,_2026`

### Files Created
- `scrapers/CLAUDE_HOUSE_SCRAPER.md` - New AI scraper workflow

### Files to Upload to Server
- `libraries/politician-libraries/us-house-2026-complete/2026-states/*.json` (all modified state files)
- `libraries/discovery-index.json`
- `scrapers/CLAUDE_HOUSE_SCRAPER.md`

---

## How to Use This Log
If Claude crashes, just say: "Read docs/claude-session-log.md and continue where we left off"
