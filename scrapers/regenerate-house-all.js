#!/usr/bin/env node
/**
 * MASTER SCRIPT: Regenerate ALL House candidate files
 *
 * Run this after updating states-*.json files to regenerate everything:
 *   node regenerate-house-all.js
 *
 * This creates/updates:
 *   1. Individual district files (435 + 5 territories): 2026-states/{state}/{district}.json
 *   2. State manifests (50 + 5): 2026-states/{state}/_manifest.json
 *   3. Consolidated state books (50 + 5): 2026-states/{state}.json
 *   4. Discovery index: libraries/discovery-index.json
 *
 * Batch 11 = Non-voting territories (DC, GU, AS, VI, MP)
 */

const { execSync } = require('child_process');
const path = require('path');

const SCRAPER_DIR = __dirname;
const ROOT_DIR = path.join(__dirname, '..');

console.log('='.repeat(60));
console.log('REGENERATING ALL HOUSE CANDIDATE FILES');
console.log('='.repeat(60));

// Step 1: Generate individual district files + manifests
console.log('\n[1/3] Generating individual district files...\n');
for (let batch = 1; batch <= 11; batch++) {
  const label = batch === 11 ? 'Batch 11 (Territories)...' : `Batch ${batch}...`;
  console.log(`  ${label}`);
  execSync(`node generate-house-districts.js ${batch}`, {
    cwd: SCRAPER_DIR,
    stdio: 'inherit'
  });
}

// Step 2: Generate consolidated state book files
console.log('\n[2/3] Generating consolidated state book files...\n');
execSync('node generate-state-books.js', {
  cwd: SCRAPER_DIR,
  stdio: 'inherit'
});

// Step 3: Rebuild discovery index
console.log('\n[3/3] Rebuilding discovery index...\n');
execSync('node libraries/_utils/build-discovery-index-v2.js', {
  cwd: ROOT_DIR,
  stdio: 'inherit'
});

console.log('\n' + '='.repeat(60));
console.log('COMPLETE! Files to upload:');
console.log('='.repeat(60));
console.log(`
  libraries/politician-libraries/us-house-2026-complete/2026-states/
    - 50 state folders + 5 territory folders with district files
    - 55 consolidated state/territory books ({state}.json)
    - 55 state/territory manifests (_manifest.json)

  libraries/discovery-index.json
`);
