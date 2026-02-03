#!/usr/bin/env node
/**
 * Add a Quarex book to a PublicStudies curriculum.
 *
 * Usage:
 *   node add-to-curriculum.js <discipline-id> <book-title> <quarex-url>
 *
 * Examples:
 *   node add-to-curriculum.js black-studies "A History of Racism in the Americas" "https://quarex.org/libraries/?t=pe&l=historical-narratives&s=racism&b=a-history-of-racism-in-the-americas"
 *
 *   node add-to-curriculum.js womens-studies "The Suffrage Movement" "https://quarex.org/libraries/?t=k&l=the-sciences&s=history-and-anthropology&b=the-suffrage-movement"
 *
 * Options:
 *   --list          List all disciplines and their courses
 *   --remove        Remove a course by title from a discipline
 *
 * The script will:
 *   - Add the course to the discipline's courses array
 *   - Set the discipline status to "live" if it was "coming-soon"
 *   - Sort courses alphabetically
 *   - Save the updated curriculum-index.json
 */

const fs = require('fs');
const path = require('path');

const INDEX_PATH = path.join(__dirname, 'curriculum-index.json');

function loadIndex() {
  return JSON.parse(fs.readFileSync(INDEX_PATH, 'utf8'));
}

function saveIndex(data) {
  fs.writeFileSync(INDEX_PATH, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

function listAll() {
  const data = loadIndex();
  console.log('\nPublicStudies Curriculum Index\n');
  data.disciplines.forEach(d => {
    const status = d.status === 'live' ? '[LIVE]' : '[coming-soon]';
    const lang = d.lang === 'es' ? ' (Spanish)' : '';
    console.log(`  ${d.id} ${status}${lang}`);
    if (d.courses.length === 0) {
      console.log('    (no courses yet)');
    } else {
      d.courses
        .sort((a, b) => a.title.localeCompare(b.title))
        .forEach(c => {
          console.log(`    - ${c.title}`);
          console.log(`      ${c.link}`);
        });
    }
    console.log('');
  });
}

function addCourse(disciplineId, title, link) {
  const data = loadIndex();
  const discipline = data.disciplines.find(d => d.id === disciplineId);

  if (!discipline) {
    console.error(`\nError: Discipline "${disciplineId}" not found.`);
    console.error('Available disciplines:');
    data.disciplines.forEach(d => console.error(`  - ${d.id}`));
    process.exit(1);
  }

  // Check for duplicate
  const existing = discipline.courses.find(c =>
    c.title.toLowerCase() === title.toLowerCase() || c.link === link
  );
  if (existing) {
    console.error(`\nError: Course already exists in ${disciplineId}:`);
    console.error(`  "${existing.title}"`);
    console.error(`  ${existing.link}`);
    process.exit(1);
  }

  // Add and sort
  discipline.courses.push({ title, link });
  discipline.courses.sort((a, b) => a.title.localeCompare(b.title));

  // Set live if it was coming-soon
  if (discipline.status === 'coming-soon') {
    discipline.status = 'live';
    console.log(`  Status changed to "live" for ${disciplineId}`);
  }

  saveIndex(data);
  console.log(`\nAdded to ${disciplineId}:`);
  console.log(`  "${title}"`);
  console.log(`  ${link}`);
  console.log(`\n  Total courses in ${discipline.title}: ${discipline.courses.length}`);
  console.log('\nRemember to upload curriculum-index.json to the server.');
}

function removeCourse(disciplineId, title) {
  const data = loadIndex();
  const discipline = data.disciplines.find(d => d.id === disciplineId);

  if (!discipline) {
    console.error(`\nError: Discipline "${disciplineId}" not found.`);
    process.exit(1);
  }

  const idx = discipline.courses.findIndex(c =>
    c.title.toLowerCase() === title.toLowerCase()
  );

  if (idx === -1) {
    console.error(`\nError: Course "${title}" not found in ${disciplineId}.`);
    console.error('Available courses:');
    discipline.courses.forEach(c => console.error(`  - ${c.title}`));
    process.exit(1);
  }

  const removed = discipline.courses.splice(idx, 1)[0];

  // Set back to coming-soon if no courses left
  if (discipline.courses.length === 0) {
    discipline.status = 'coming-soon';
    console.log(`  Status changed to "coming-soon" for ${disciplineId} (no courses left)`);
  }

  saveIndex(data);
  console.log(`\nRemoved from ${disciplineId}:`);
  console.log(`  "${removed.title}"`);
  console.log(`\n  Remaining courses: ${discipline.courses.length}`);
}

// --- CLI ---
const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
  console.log(`
Usage:
  node add-to-curriculum.js <discipline-id> <title> <quarex-url>
  node add-to-curriculum.js --list
  node add-to-curriculum.js --remove <discipline-id> <title>

Examples:
  node add-to-curriculum.js black-studies "The Civil Rights Movement" "https://quarex.org/libraries/?t=k&l=the-sciences&s=history-and-anthropology&b=the-civil-rights-movement"
  node add-to-curriculum.js --list
  node add-to-curriculum.js --remove black-studies "The Civil Rights Movement"
`);
  process.exit(0);
}

if (args[0] === '--list') {
  listAll();
} else if (args[0] === '--remove') {
  if (args.length < 3) {
    console.error('Usage: node add-to-curriculum.js --remove <discipline-id> <title>');
    process.exit(1);
  }
  removeCourse(args[1], args[2]);
} else {
  if (args.length < 3) {
    console.error('Usage: node add-to-curriculum.js <discipline-id> <title> <quarex-url>');
    process.exit(1);
  }
  addCourse(args[0], args[1], args[2]);
}
