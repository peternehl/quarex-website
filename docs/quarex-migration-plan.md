# Quarex Migration Plan

## Timeline
- **Target launch:** January 1, 2026
- **Slip date:** January 15, 2026

## Overview
Replicate TruthAngel.org fully to Quarex.org, rebrand, test, then roll out.
TruthAngel.org stays live throughout the process.

---

## Architectural Decisions (DECIDED)

### URL Structure
- `Quarex.org` → Landing page (combines marketing + "What is Quarex?" explanation)
- `Quarex.org/libraries/` → Library browser (renamed from `/unlimited/`)
- `Quarex.org/ask/` → Q&A interface
- `Quarex.org/spec/` → Specification
- `Quarex.org/schema/` → JSON Schema

### Rationale
- "Unlimited" was TruthAngel-specific branding; `/libraries/` is clearer
- Landing page merges best of current `index.html` + `/quarex/index.html`
- Cleaner information architecture from the start

---

## Phase 1: Infrastructure Setup ✅ COMPLETE
- [x] Verify quarex.org DNS is pointing to GoDaddy hosting
- [x] Create folder structure on server for quarex.org
- [x] Set up SSL certificate for quarex.org (Let's Encrypt)
- [x] Configure .htaccess for quarex.org (libraries/.htaccess for SPA routing)

## Phase 2: Content Replication ✅ COMPLETE
- [x] Copy all files from TruthAngel.org to quarex.org
  - [x] /unlimited → /libraries/ (renamed)
  - [x] /ask (Q&A interface)
  - [x] /api (PHP backend)
  - [x] /Assets → /assets/ (lowercase for consistency)
  - [x] /quarex/spec/ → /spec/
  - [x] /quarex/schema/ → /schema/
  - [x] Landing page (merge index.html + quarex/index.html)
  - [x] /ethics, /help, /privacy pages
- [x] Verify all file permissions are correct
- [x] Test that the unbranded copy works at quarex.org

## Phase 3: Branding Updates ✅ MAIN FILES COMPLETE
- [x] Update all "TruthAngel" text references to "Quarex" (main user-facing pages)
  - [x] index.html (landing page) - fully rebranded
  - [x] libraries/index.html - fully rebranded
  - [x] libraries/library-tree.html - fully rebranded
  - [x] ask/ask.html - fully rebranded
  - [x] ethics/index.html - fully rebranded (renamed from ethics.html)
  - [x] help/index.html - fully rebranded
  - [x] help/quarex-download.html - fully rebranded (renamed from TruthAngelCreator.html)
  - [x] privacy.html - fully rebranded
  - [x] spec/index.html - fully rebranded
  - [ ] API responses (if any branding there) - BACK BURNER
- [x] Replace logo/wordmark images
  - [x] Identify all logo files (angel.jpg, etc.)
  - [x] Create/add Quarex logo files → `quarex-hero-round-500pixels.png`
  - [x] Update all image references in main pages
- [x] Update page titles and meta tags
- [x] Update favicon references
- [x] Update email references → peter@quarex.org
- [x] Update footer credits/copyright
- [x] Update manifest.json for PWA

## Phase 4: Technical Updates ✅ COMPLETE (deferred items noted)
- [x] Update API endpoints if hardcoded URLs exist
- [x] Update any absolute URLs (TruthAngel.org → quarex.org)
- [ ] Update Google Analytics tracking ID (if different) → moved to Phase 6
- [x] Check for hardcoded domain references in JavaScript (fixed /unlimited/ → /libraries/)
- [x] Update CORS settings if applicable (added quarex.org to ask.php)
- [x] Update any API keys that are domain-restricted (N/A - Gemini not domain-restricted)
- [x] **SECURITY:** Rotate Gemini API key ✅ (new key deployed to both sites, old key deleted 2024-12-16)

## Phase 5: Testing ✅ COMPLETE
- [x] Test landing page
- [x] Test /libraries/ navigation
- [x] Test book loading and chapter display
- [x] Test ask.html Q&A functionality
- [x] Test related topics cross-linking
- [x] Test on mobile devices
- [x] Test all external links
- [x] Run dead link checker (manual verification - all OK)
- [x] Test API responses

## Phase 6: Monitoring & Analytics ✅ COMPLETE (deferred items noted)
- [x] Set up Google Analytics for quarex.org (reusing G-TMVLTZ6BB5 from TruthAngel)
- [x] Set up Google Search Console for quarex.org
  - [x] Verify domain ownership
  - [x] Submit sitemap (sitemap.xml created and submitted)
- [ ] Set up uptime monitoring → deferred to post-launch
- [ ] Set up error logging → deferred to post-launch
- [ ] Create test Gmail/social accounts if needed → deferred to post-launch

## Phase 7: Soft Launch
- [x] Share quarex.org with small test group (Core Group?) - sent 2024-12-16
- [ ] Collect feedback on branding
- [ ] Fix any issues found
- [ ] Iterate on design if needed

## Phase 8: Official Rollout
- [ ] Announce Quarex launch
- [ ] Update Buffer/social media profiles
- [ ] Update email signatures
- [ ] Consider: Redirect TruthAngel.org → quarex.org (or keep both?)
- [ ] Submit to search engines
- [ ] Update any external listings/links

---

## Files to Search for "TruthAngel" References
Run this to find all occurrences:
```bash
grep -r "TruthAngel" --include="*.html" --include="*.js" --include="*.php" --include="*.css" --include="*.json"
```

## Decision Points
1. ~~**URL structure**: /unlimited/ vs /libraries/~~ → **DECIDED: /libraries/**
2. ~~**Domain strategy**~~ → **DECIDED: 3-phase approach**
   - Phase A: Keep TruthAngel.org live during Quarex.org testing
   - Phase B: After Quarex.org launch, redirect TruthAngel.org → Quarex.org (duration determined by exigent circumstances)
   - Phase C: Repurpose TruthAngel.org (keep domain forever)
3. ~~**Extension name**~~ → **CANCELLED** (Browser extension dropped from roadmap)
4. ~~**Tagline**~~ → **DECIDED: "The Curiosity Engine"**
5. ~~**Color scheme**~~ → **DECIDED: Keep the dark theme** (#0A0A0A background, #F7F7F7 text)

---

## Notes
- Keep TruthAngel.org fully operational throughout
- Quarex.org is the test/staging environment until ready
- Can roll back at any time since TruthAngel.org is untouched

---

## Back Burner Items
Files with remaining TruthAngel references (not user-facing or lower priority):

### To Be Remade (content-specific)
- [ ] `libraries/meta-knowledge/*.json` - Will be recreated with new content

### Tablet Mode (on hold)
- [ ] `tablet/senior/index.html`
- [ ] `tablet/corporate/index.html`
- [ ] `tablet/education/index.html`
- [ ] `tablet/consumer/index.html`
- [ ] `tablet/tablet-config.js`
- [ ] `tablet/tablet-setup-info.txt`

### Utility Scripts
- [ ] `libraries/Utilities and Info Files/*`

### API Files
- [ ] `api/ask.php`
- [ ] `api/citation.php`
- [ ] `api/citation.py`
- [ ] `api/blocked_patterns.txt`

### Help Files
- [ ] `help/quarex-universal.html` (offline desktop version)
- [ ] `help/living-book-editor.html`

### Schema/Docs
- [ ] `schema/v1/index.html`

### Review/Possible Removal
- [ ] `assets/ta-linkify.js` - Had problems, may not be in use

### Data Files
- [x] `libraries/download-seed-creator.php` → moved to `tools/download-seed-creator.php`
- [ ] `libraries/discovery-index.json`
- [ ] `libraries/questions-libraries/question-taxonomy.json`
- [ ] `libraries/Seed Quarex/*.json` files

---

## New Architecture: /tools/ Folder
Created `/tools/` folder for creator/developer tools:
- `tools/index.html` - Tools hub page
- `tools/seed-creator.html` - Interactive form (moved from help/)
- `tools/seed-instructions.html` - Guide for using seeds with LLMs
- `tools/download-seed-creator.php` - PHP generator for offline tool
- `tools/templates/` - JSON templates
