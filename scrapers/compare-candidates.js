const fs = require('fs');
const path = require('path');

const oldDir = path.join(__dirname, '..', 'libraries', 'politician-libraries as of 1-16-26', 'us-house-2026-complete', '2026-states');
const newDir = path.join(__dirname, '..', 'libraries', 'politician-libraries', 'us-house-2026-complete', '2026-states');

const states = [
  'alabama', 'alaska', 'arizona', 'arkansas', 'california',
  'colorado', 'connecticut', 'delaware', 'florida', 'georgia',
  'hawaii', 'idaho', 'illinois', 'indiana', 'iowa',
  'kansas', 'kentucky', 'louisiana', 'maine', 'maryland',
  'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri',
  'montana', 'nebraska', 'nevada', 'new-hampshire', 'new-jersey',
  'new-mexico', 'new-york', 'north-carolina', 'north-dakota', 'ohio',
  'oklahoma', 'oregon', 'pennsylvania', 'rhode-island', 'south-carolina',
  'south-dakota', 'tennessee', 'texas', 'utah', 'vermont',
  'virginia', 'washington', 'west-virginia', 'wisconsin', 'wyoming'
];

const changes = {
  added: [],
  removed: []
};

function extractCandidates(book) {
  const candidates = {};
  if (!book.chapters) return candidates;

  for (const chapter of book.chapters) {
    const district = chapter.name;
    candidates[district] = new Set();

    if (chapter.topics && Array.isArray(chapter.topics)) {
      for (const topic of chapter.topics) {
        candidates[district].add(topic);
      }
    }
  }
  return candidates;
}

function compareState(stateName) {
  const oldPath = path.join(oldDir, `${stateName}.json`);
  const newPath = path.join(newDir, `${stateName}.json`);

  if (!fs.existsSync(oldPath) || !fs.existsSync(newPath)) {
    console.log(`Skipping ${stateName} - file not found`);
    return;
  }

  const oldBook = JSON.parse(fs.readFileSync(oldPath, 'utf8'));
  const newBook = JSON.parse(fs.readFileSync(newPath, 'utf8'));

  const oldCandidates = extractCandidates(oldBook);
  const newCandidates = extractCandidates(newBook);

  // Compare each district
  const allDistricts = new Set([...Object.keys(oldCandidates), ...Object.keys(newCandidates)]);

  for (const district of allDistricts) {
    const oldSet = oldCandidates[district] || new Set();
    const newSet = newCandidates[district] || new Set();

    // Find added candidates
    for (const candidate of newSet) {
      if (!oldSet.has(candidate)) {
        changes.added.push({
          state: stateName,
          district,
          candidate
        });
      }
    }

    // Find removed candidates
    for (const candidate of oldSet) {
      if (!newSet.has(candidate)) {
        changes.removed.push({
          state: stateName,
          district,
          candidate
        });
      }
    }
  }
}

// Process all states
for (const state of states) {
  compareState(state);
}

// Generate report
let report = `# US House 2026 Candidate Changes\n`;
report += `Comparing 1-16-26 backup to 1-23-26 scrape\n\n`;

report += `## Summary\n`;
report += `- Candidates Added: ${changes.added.length}\n`;
report += `- Candidates Removed: ${changes.removed.length}\n\n`;

if (changes.added.length > 0) {
  report += `## Candidates Added\n\n`;
  const byState = {};
  for (const c of changes.added) {
    if (!byState[c.state]) byState[c.state] = [];
    byState[c.state].push(c);
  }
  for (const [state, candidates] of Object.entries(byState).sort()) {
    const displayState = state.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    report += `### ${displayState}\n`;
    for (const c of candidates) {
      report += `- **${c.district}**: ${c.candidate}\n`;
    }
    report += `\n`;
  }
}

if (changes.removed.length > 0) {
  report += `## Candidates Removed\n\n`;
  const byState = {};
  for (const c of changes.removed) {
    if (!byState[c.state]) byState[c.state] = [];
    byState[c.state].push(c);
  }
  for (const [state, candidates] of Object.entries(byState).sort()) {
    const displayState = state.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    report += `### ${displayState}\n`;
    for (const c of candidates) {
      report += `- **${c.district}**: ${c.candidate}\n`;
    }
    report += `\n`;
  }
}

if (changes.added.length === 0 && changes.removed.length === 0) {
  report += `No candidate changes detected.\n`;
}

// Save report
const reportPath = path.join(__dirname, 'candidate-changes-2026-01-23.md');
fs.writeFileSync(reportPath, report);
console.log(`Report saved to: ${reportPath}`);
console.log(`\nSummary:`);
console.log(`- Added: ${changes.added.length}`);
console.log(`- Removed: ${changes.removed.length}`);
