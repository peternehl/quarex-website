/**
 * Selective retag script for Hispanic and Black Studies books
 * Adds new specific tags to chapters in cultural studies shelves
 * Run: node libraries/_utils/retag-cultural-books.js
 */

const fs = require('fs');
const path = require('path');

// Tags that can be replaced when adding more specific cultural tags
const REPLACEABLE_TAGS = ['society', 'identity', 'sociology', 'anthropology'];

function processBook(filePath, newTag, shelfName) {
  const content = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  let changed = false;
  let changeCount = 0;

  if (!content.chapters) return { changed: false, changeCount: 0 };

  content.chapters.forEach((chapter, idx) => {
    if (!chapter.tags || chapter.tags.length !== 4) return;

    // Skip if already has the new tag
    if (chapter.tags.includes(newTag)) return;

    // Find a replaceable tag (prefer later positions)
    for (let i = 3; i >= 0; i--) {
      if (REPLACEABLE_TAGS.includes(chapter.tags[i])) {
        const oldTag = chapter.tags[i];
        chapter.tags[i] = newTag;
        changed = true;
        changeCount++;
        console.log(`  ${path.basename(filePath)} / Ch${idx + 1}: ${oldTag} → ${newTag}`);
        break;
      }
    }
  });

  if (changed) {
    fs.writeFileSync(filePath, JSON.stringify(content, null, 2) + '\n');
  }

  return { changed, changeCount };
}

function processShelf(shelfPath, newTag, shelfName) {
  const files = fs.readdirSync(shelfPath).filter(f => f.endsWith('.json') && !f.startsWith('_'));

  console.log(`\n=== Processing ${shelfName} (${files.length} books) ===`);
  console.log(`Adding tag: ${newTag}\n`);

  let totalChanges = 0;
  let booksChanged = 0;

  for (const file of files) {
    const filePath = path.join(shelfPath, file);
    const result = processBook(filePath, newTag, shelfName);
    if (result.changed) {
      booksChanged++;
      totalChanges += result.changeCount;
    }
  }

  console.log(`\nSummary: ${booksChanged} books modified, ${totalChanges} chapter tags updated`);
  return { booksChanged, totalChanges };
}

// Main
const hispanicPath = path.join(__dirname, '..', 'perspectives-libraries', 'cultural-and-identity', 'hispanic-cultures');
const blackStudiesPath = path.join(__dirname, '..', 'perspectives-libraries', 'cultural-and-identity', 'black-studies');

let grandTotal = { books: 0, changes: 0 };

if (fs.existsSync(hispanicPath)) {
  const r = processShelf(hispanicPath, 'hispanic-culture', 'Hispanic Cultures');
  grandTotal.books += r.booksChanged;
  grandTotal.changes += r.totalChanges;
}

if (fs.existsSync(blackStudiesPath)) {
  const r = processShelf(blackStudiesPath, 'black-history', 'Black Studies');
  grandTotal.books += r.booksChanged;
  grandTotal.changes += r.totalChanges;
}

console.log(`\n=== GRAND TOTAL ===`);
console.log(`Books modified: ${grandTotal.books}`);
console.log(`Chapter tags updated: ${grandTotal.changes}`);
console.log(`\nDon't forget to rebuild discovery index: node libraries/_utils/build-discovery-index-v2.js`);
