/**
 * Generate state-level book JSON files from scraped Ballotpedia data
 * These files list districts as chapters (for shelf navigation)
 *
 * Usage: node generate-state-books.js
 *
 * Creates files like: 2026-states/alabama.json
 * With structure: { book: "Alabama", chapters: [{name: "AL-01", topics: []}, ...] }
 */

const fs = require('fs');
const path = require('path');

const outputBase = path.join(__dirname, '..', 'libraries', 'politician-libraries', 'us-house-2026-complete', '2026-states');

let totalStates = 0;

// Process all 11 batch files (1-10 states, 11 territories)
for (let batchNum = 1; batchNum <= 11; batchNum++) {
  const inputFile = path.join(__dirname, `states-${batchNum}.json`);

  if (!fs.existsSync(inputFile)) {
    console.log(`Skipping batch ${batchNum} - file not found`);
    continue;
  }

  console.log(`Processing batch ${batchNum}...`);
  const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

  for (const state of data.states) {
    const stateSlug = state.state.toLowerCase().replace(/ /g, '-');
    const stateFile = path.join(outputBase, `${stateSlug}.json`);

    // Build chapters from districts - include all candidates as topics
    const chapters = state.districts.map(district => {
      // Combine all candidates from all parties into one topics array
      const allCandidates = [];
      const parties = ['Republican', 'Democratic', 'Independent', 'Libertarian', 'Green', 'Other', 'Socialist Labor', 'Communist', 'Working Class'];
      for (const party of parties) {
        if (district.candidates[party] && district.candidates[party].length > 0) {
          allCandidates.push(...district.candidates[party]);
        }
      }
      return {
        name: district.district,
        topics: allCandidates
      };
    });

    const stateData = {
      book: state.state,
      chapters: chapters
    };

    fs.writeFileSync(stateFile, JSON.stringify(stateData, null, 2));
    console.log(`  ${state.state} - ${chapters.length} districts`);
    totalStates++;
  }
}

console.log(`\n✓ Complete: ${totalStates} state/territory book files created`);
