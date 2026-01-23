/**
 * Generate individual state book files from Governor and Senate library JSONs
 */

const fs = require('fs');
const path = require('path');

const baseDir = path.join(__dirname, '..', 'libraries', 'politician-libraries');

function slugify(name) {
  return name.toLowerCase().replace(/ /g, '-');
}

function generateStateBooks(libraryFile, outputDir) {
  console.log(`\nProcessing: ${libraryFile}`);

  const libraryPath = path.join(baseDir, libraryFile);
  const outPath = path.join(baseDir, outputDir);

  if (!fs.existsSync(libraryPath)) {
    console.log(`  ERROR: Library file not found: ${libraryPath}`);
    return;
  }

  const library = JSON.parse(fs.readFileSync(libraryPath, 'utf8'));

  // Ensure output directory exists
  if (!fs.existsSync(outPath)) {
    fs.mkdirSync(outPath, { recursive: true });
  }

  let count = 0;

  // Process each shelf
  for (const shelf of library.shelves) {
    for (const book of shelf.books) {
      const stateBook = {
        book: book.name,
        chapters: book.chapters
      };

      const filename = slugify(book.name) + '.json';
      const filepath = path.join(outPath, filename);

      fs.writeFileSync(filepath, JSON.stringify(stateBook, null, 2));
      count++;
    }
  }

  console.log(`  Generated ${count} state files in ${outputDir}`);
}

// Generate Governor state books
generateStateBooks(
  'us-governors-2026/us_governors_2026.json',
  'us-governors-2026/2026-gubernatorial-races'
);

// Generate Senate state books
generateStateBooks(
  'us-senate-2026-complete/us_senate_2026_complete.json',
  'us-senate-2026-complete/class-2-regular-elections'
);

console.log('\nDone!');
