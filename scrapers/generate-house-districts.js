/**
 * Generate House district JSON files from scraped Ballotpedia data
 * Usage: node generate-house-districts.js <batch-number>
 * Example: node generate-house-districts.js 1
 *
 * Processes states-{batch}.json and creates district files in:
 * libraries/politician-libraries/us-house-2026-complete/2026-states/{state}/{district}.json
 */

const fs = require('fs');
const path = require('path');

const batchNum = process.argv[2];

if (!batchNum || isNaN(batchNum) || batchNum < 1 || batchNum > 11) {
  console.log('Usage: node generate-house-districts.js <batch-number>');
  console.log('Batch number must be 1-11 (11 = non-voting territories)');
  process.exit(1);
}

const inputFile = path.join(__dirname, `states-${batchNum}.json`);
const outputBase = path.join(__dirname, '..', 'libraries', 'politician-libraries', 'us-house-2026-complete', '2026-states');

// Read the batch file
console.log(`Reading ${inputFile}...`);
const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

console.log(`Processing batch ${batchNum}: ${data.states.map(s => s.state).join(', ')}`);

let totalDistricts = 0;

for (const state of data.states) {
  const stateSlug = state.state.toLowerCase().replace(/ /g, '-');
  const stateDir = path.join(outputBase, stateSlug);

  // Create state directory if it doesn't exist
  if (!fs.existsSync(stateDir)) {
    fs.mkdirSync(stateDir, { recursive: true });
  }

  console.log(`\n${state.state} (${state.districts.length} districts):`);

  for (const district of state.districts) {
    const districtSlug = district.district.toLowerCase();
    const districtFile = path.join(stateDir, `${districtSlug}.json`);

    // Build chapters from candidates
    const chapters = [];

    if (district.candidates.Republican && district.candidates.Republican.length > 0) {
      chapters.push({
        name: "Republican",
        topics: district.candidates.Republican
      });
    }

    if (district.candidates.Democratic && district.candidates.Democratic.length > 0) {
      chapters.push({
        name: "Democratic",
        topics: district.candidates.Democratic
      });
    }

    // Handle Independent/Other parties
    const otherParties = ['Independent', 'Libertarian', 'Green', 'Other', 'Socialist Labor', 'Communist', 'Working Class'];
    const otherCandidates = [];

    for (const party of otherParties) {
      if (district.candidates[party] && district.candidates[party].length > 0) {
        otherCandidates.push(...district.candidates[party]);
      }
    }

    if (otherCandidates.length > 0) {
      chapters.push({
        name: "Independent/Other",
        topics: otherCandidates
      });
    }

    const districtData = {
      book: district.district,
      chapters: chapters
    };

    fs.writeFileSync(districtFile, JSON.stringify(districtData, null, 2));
    console.log(`  ${district.district} - ${chapters.reduce((sum, c) => sum + c.topics.length, 0)} candidates`);
    totalDistricts++;
  }

  // Update state manifest
  const manifestFile = path.join(stateDir, '_manifest.json');
  const manifest = state.districts.map(d => ({
    slug: d.district.toLowerCase(),
    name: d.district,
    chapterCount: Object.values(d.candidates).flat().length > 0 ?
      (d.candidates.Republican?.length > 0 ? 1 : 0) +
      (d.candidates.Democratic?.length > 0 ? 1 : 0) +
      (['Independent', 'Libertarian', 'Green', 'Other'].some(p => d.candidates[p]?.length > 0) ? 1 : 0)
      : 0
  }));

  fs.writeFileSync(manifestFile, JSON.stringify(manifest, null, 2));
  console.log(`  _manifest.json updated`);
}

console.log(`\n✓ Batch ${batchNum} complete: ${totalDistricts} district files created`);
