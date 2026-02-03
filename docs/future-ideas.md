# Future Project Ideas

## AI-Managed YubiKey Assistant
**Date noted:** 2026-01-26

An AI layer that sits on top of hardware security keys to make them actually usable for normal people.

**Core concept:**
- Hardware (YubiKey) handles cryptography and key storage
- AI handles UX, guidance, and proactive recommendations

**Features:**
- Browser extension that detects when sites support WebAuthn/passkeys
- Local database tracking which sites you've registered your key with
- AI assistant for guidance ("How do I add my key to Chase?")
- Dashboard showing security status across accounts
- Proactive notifications: "You haven't set up your YubiKey for this bank yet"
- Reminders to test backup keys
- Site-specific registration walkthroughs

**Technical components:**
1. Chrome extension (start with one browser)
2. Local SQLite or JSON database for registration tracking
3. Claude API for AI guidance
4. Desktop tray app or browser popup for dashboard

**Why this matters:**
- Hardware keys exist but most people don't know about them
- Setup is confusing - each site does it differently
- No tool currently tracks your security posture holistically
- The gap is UX and integration, not cryptography

**MVP scope:**
- Chrome extension only
- Manual + auto-detection of key registrations
- AI chat for setup guidance
- Simple dashboard: "Sites with key" vs "Sites that could use your key"

---

## Quarex Topic Discovery Improvements
**Date noted:** 2026-01-26

Thinking about how to surface useful topics without requiring 5-6 clicks through the hierarchy.

**Options to explore:**
1. Topic-level search (not just book search)
2. Tag-based browsing across all libraries
3. "Start Here" / Featured Topics page
4. Flat topic browser (bypass hierarchy entirely)
5. Question-type filters ("Show all 'Why...' questions")
6. Random/discovery mode

**Status:** Thinking about it - no action yet
