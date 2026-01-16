// Build ZIP-to-CD JSON lookup from Census CSV data
// Run: node build-zip-lookup.js

const fs = require('fs');

const csv = fs.readFileSync('zccd.csv', 'utf8');
const lines = csv.trim().split('\n');

// Skip header: state_fips,state_abbr,zcta,cd
const lookup = {};

for (let i = 1; i < lines.length; i++) {
    const parts = lines[i].split(',');
    if (parts.length < 4) continue;

    const stateAbbr = parts[1];
    const zip = parts[2];
    const cd = parseInt(parts[3]);

    // Format: "NY-12" style
    const district = `${stateAbbr}-${cd.toString().padStart(2, '0')}`;

    if (!lookup[zip]) {
        lookup[zip] = [];
    }
    if (!lookup[zip].includes(district)) {
        lookup[zip].push(district);
    }
}

// Sort districts within each zip
for (const zip in lookup) {
    lookup[zip].sort();
}

// Write compact JSON
fs.writeFileSync('zip-to-cd.json', JSON.stringify(lookup));

// Stats
const totalZips = Object.keys(lookup).length;
const multiDistrict = Object.values(lookup).filter(d => d.length > 1).length;
console.log(`Total ZIPs: ${totalZips}`);
console.log(`Multi-district ZIPs: ${multiDistrict} (${(multiDistrict/totalZips*100).toFixed(1)}%)`);
console.log(`File size: ${(fs.statSync('zip-to-cd.json').size / 1024).toFixed(1)} KB`);
