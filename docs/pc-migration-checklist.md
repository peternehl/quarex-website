# PC Migration Checklist

**Old PC**: Current development machine
**New PC**: Arriving December 20, 2025
**Strategy**: Parallel operation - old PC stays active until migration complete

---

## Phase 1: Pre-Migration Inventory (Do on Old PC)

### Code Projects
- [ ] **Quarex** - `c:\laragon\www\Quarex` - Git repo ✓
- [ ] **TruthAngel** - `C:\Users\peter\projects\websites\TruthAngel` - Git repo ✓
- [ ] **TABA Website** - `H:\My Drive\TABA` - Google Drive synced ✓
- [ ] **WebSite Development** - `H:\My Drive\WebSite Development` - Google Drive synced ✓
- [ ] **API Keys folder** - `C:\Users\peter\projects\websites\API Keys` - CRITICAL
- [ ] **ArchAngel** - `C:\Users\peter\projects\ArchAngel` - Review/migrate?
- [ ] **Conversations** - `C:\Users\peter\projects\Conversations` - Claude logs?
- [ ] **quarex-files** - `C:\Users\peter\projects\quarex-files` - Review/migrate?
- [ ] **Book Ideas** - `C:\Users\peter\projects\websites\Book Ideas`
- [ ] **Marketing and Promotion** - `C:\Users\peter\projects\websites\Marketing and Promotion`
- [ ] **Trademarks** - `C:\Users\peter\projects\websites\Trademarks`
- [ ] **Misc docs** - `to do list.docx`, `Data Center.docx`, etc.

### Credentials & Secrets (CRITICAL)
- [ ] GoDaddy cPanel credentials
- [ ] Gemini API key
- [ ] Google Analytics credentials
- [ ] Cloudflare account credentials
- [ ] GitHub credentials / SSH keys (`C:\Users\peter\.ssh\`)
- [ ] Any `.env` files in projects
- [ ] `scrapers/config.py` with cPanel credentials
- [ ] Browser saved passwords - export from Chrome/Firefox

### Development Tools
- [ ] **Laragon** - Note version, settings, virtual hosts config
- [ ] **Python** - Note version, check `pip list` for installed packages
- [ ] **Node.js** - Note version, check global npm packages
- [ ] **Git** - Note config (`git config --global --list`)
- [ ] **VS Code** - Extensions list, settings sync enabled?
- [ ] **Claude Code** - Check if settings need migration

### Databases (check if any)
- [ ] Check Laragon for MySQL databases: `c:\laragon\data\mysql`
- [ ] Check for SQLite files (`.db`, `.sqlite`) in projects
- [ ] Export any databases found

### Other Files
- [ ] Documents folder - anything work-related?
- [ ] Downloads folder - any installers to keep?
- [ ] Desktop files
- [ ] Browser bookmarks - export

---

## Phase 2: Backup (Do on Old PC)

### Git Repos
- [ ] Push all uncommitted changes to GitHub
  ```
  cd c:\laragon\www\Quarex && git status && git push
  cd C:\Users\peter\projects\websites\TruthAngel && git status && git push
  ```

### Non-Git Files
- [ ] Copy entire `c:\laragon\www\` to external drive or cloud
- [ ] Copy `C:\Users\peter\projects\` to external drive or cloud
- [ ] Copy `C:\Users\peter\.ssh\` folder (SSH keys)
- [ ] Export browser bookmarks
- [ ] Export browser saved passwords

### Config Files
- [ ] Copy Laragon config files
- [ ] Copy VS Code settings (if not synced)
- [ ] Screenshot or export any app-specific settings

---

## Phase 3: New PC Setup

### Install Development Tools
- [ ] **Laragon** - Download from laragon.org
- [ ] **Python 3.12+** - Download from python.org
- [ ] **Node.js LTS** - Download from nodejs.org
- [ ] **Git** - Download from git-scm.com
- [ ] **VS Code** - Download from code.visualstudio.com
- [ ] **Claude Code** - `npm install -g @anthropic-ai/claude-code`

### Configure Git
```bash
git config --global user.name "Peter Nehl"
git config --global user.email "your-email@example.com"
```

### Clone Repos
```bash
cd c:\laragon\www
git clone https://github.com/YOUR_USERNAME/Quarex.git
git clone https://github.com/YOUR_USERNAME/TruthAngel.git
```

### Restore Credentials
- [ ] Copy `.ssh` folder to `C:\Users\peter\.ssh\`
- [ ] Restore `scrapers/config.py` with credentials
- [ ] Restore any `.env` files
- [ ] Log into GitHub, GoDaddy, Cloudflare, Google Analytics

### Install Python Dependencies
```bash
cd c:\laragon\www\Quarex\scrapers
pip install requests beautifulsoup4 lxml
```

### Verify Everything Works
- [ ] Start Laragon, verify sites load locally
- [ ] Run scrapers, verify they work
- [ ] Test Git push/pull
- [ ] Verify VS Code extensions installed

---

## Phase 4: Verification

- [ ] Compare old and new PC file counts/sizes
- [ ] Test all critical workflows
- [ ] Verify can deploy to live server
- [ ] Run Quarex locally, test all features

---

## Phase 5: Cleanup (After Confident)

- [ ] Revoke any API keys that were on old PC (if concerned)
- [ ] Decide fate of old PC (keep as backup, repurpose, etc.)

---

## Notes

- Old PC stays active during entire process
- Don't rush - verify each step
- When in doubt, copy more rather than less

---

## Google Drive Folders (H: drive)
- [ ] Install **Google Drive for Desktop** on new PC
- [ ] Sign into Google account
- [ ] Verify drive mounts (may be different letter than H:)
- [ ] Folders that will sync automatically:
  - `H:\My Drive\TABA`
  - `H:\My Drive\WebSite Development`
- [ ] Test TABA site works after sync

