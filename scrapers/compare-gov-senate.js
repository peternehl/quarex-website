/**
 * Compare Governor and Senate candidate changes between old and new files
 */

const fs = require('fs');
const path = require('path');

const baseDir = path.join(__dirname, '..', 'libraries', 'politician-libraries');
const oldBaseDir = path.join(__dirname, '..', 'libraries', 'politician-libraries as of 1-16-26');

function extractCandidates(book) {
  const candidates = new Set();
  if (!book.chapters) return candidates;

  for (const chapter of book.chapters) {
    if (chapter.topics && Array.isArray(chapter.topics)) {
      for (const topic of chapter.topics) {
        if (topic !== "No candidates declared") {
          candidates.add(topic);
        }
      }
    }
  }
  return candidates;
}

function compareFiles(oldDir, newDir, label) {
  console.log(`\n=== ${label} ===`);

  const changes = { added: [], removed: [] };

  // Get all state files from new directory
  if (!fs.existsSync(newDir)) {
    console.log(`  New directory not found: ${newDir}`);
    return changes;
  }

  const files = fs.readdirSync(newDir).filter(f => f.endsWith('.json') && !f.startsWith('_'));

  for (const file of files) {
    const oldPath = path.join(oldDir, file);
    const newPath = path.join(newDir, file);

    if (!fs.existsSync(oldPath)) {
      console.log(`  No old file for: ${file}`);
      continue;
    }

    const oldBook = JSON.parse(fs.readFileSync(oldPath, 'utf8'));
    const newBook = JSON.parse(fs.readFileSync(newPath, 'utf8'));

    const state = newBook.book || file.replace('.json', '');
    const oldCandidates = extractCandidates(oldBook);
    const newCandidates = extractCandidates(newBook);

    // Find added
    for (const c of newCandidates) {
      if (!oldCandidates.has(c)) {
        changes.added.push({ state, candidate: c });
      }
    }

    // Find removed
    for (const c of oldCandidates) {
      if (!newCandidates.has(c)) {
        changes.removed.push({ state, candidate: c });
      }
    }
  }

  console.log(`  Added: ${changes.added.length}`);
  console.log(`  Removed: ${changes.removed.length}`);

  return changes;
}

// Compare Governors
const govChanges = compareFiles(
  path.join(oldBaseDir, 'us-governors-2026', '2026-gubernatorial-races'),
  path.join(baseDir, 'us-governors-2026', '2026-gubernatorial-races'),
  'GOVERNORS 2026'
);

// Compare Senate
const senateChanges = compareFiles(
  path.join(oldBaseDir, 'us-senate-2026-complete', 'class-2-regular-elections'),
  path.join(baseDir, 'us-senate-2026-complete', 'class-2-regular-elections'),
  'SENATE 2026'
);

// Generate report
let report = `# Governor & Senate 2026 Candidate Changes\n`;
report += `Comparing 1-16-26 backup to 1-23-26 scrape\n\n`;

report += `## Summary\n`;
report += `### Governors\n`;
report += `- Added: ${govChanges.added.length}\n`;
report += `- Removed: ${govChanges.removed.length}\n\n`;
report += `### Senate\n`;
report += `- Added: ${senateChanges.added.length}\n`;
report += `- Removed: ${senateChanges.removed.length}\n\n`;

if (govChanges.added.length > 0) {
  report += `## Governor Candidates Added\n\n`;
  const byState = {};
  for (const c of govChanges.added) {
    if (!byState[c.state]) byState[c.state] = [];
    byState[c.state].push(c.candidate);
  }
  for (const [state, candidates] of Object.entries(byState).sort()) {
    report += `### ${state}\n`;
    for (const c of candidates) {
      report += `- ${c}\n`;
    }
    report += `\n`;
  }
}

if (govChanges.removed.length > 0) {
  report += `## Governor Candidates Removed\n\n`;
  const byState = {};
  for (const c of govChanges.removed) {
    if (!byState[c.state]) byState[c.state] = [];
    byState[c.state].push(c.candidate);
  }
  for (const [state, candidates] of Object.entries(byState).sort()) {
    report += `### ${state}\n`;
    for (const c of candidates) {
      report += `- ${c}\n`;
    }
    report += `\n`;
  }
}

if (senateChanges.added.length > 0) {
  report += `## Senate Candidates Added\n\n`;
  const byState = {};
  for (const c of senateChanges.added) {
    if (!byState[c.state]) byState[c.state] = [];
    byState[c.state].push(c.candidate);
  }
  for (const [state, candidates] of Object.entries(byState).sort()) {
    report += `### ${state}\n`;
    for (const c of candidates) {
      report += `- ${c}\n`;
    }
    report += `\n`;
  }
}

if (senateChanges.removed.length > 0) {
  report += `## Senate Candidates Removed\n\n`;
  const byState = {};
  for (const c of senateChanges.removed) {
    if (!byState[c.state]) byState[c.state] = [];
    byState[c.state].push(c.candidate);
  }
  for (const [state, candidates] of Object.entries(byState).sort()) {
    report += `### ${state}\n`;
    for (const c of candidates) {
      report += `- ${c}\n`;
    }
    report += `\n`;
  }
}

// Save report
const reportPath = path.join(__dirname, 'gov-senate-changes-2026-01-23.md');
fs.writeFileSync(reportPath, report);
console.log(`\nReport saved to: ${reportPath}`);
