/**
 * Retag script for Women's Studies curriculum books
 * Adds feminism, womens-history, and reproductive-rights tags
 * Run: node libraries/_utils/retag-womens-studies.js
 */

const fs = require('fs');
const path = require('path');

// Tags that can be replaced when adding more specific tags
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
        console.log(`  ${path.basename(filePath)} / Ch${idx + 1}: ${oldTag} -> ${newTag}`);
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

function processSingleBook(bookPath, newTag, description) {
  console.log(`\n=== Processing ${description} ===`);
  console.log(`Adding tag: ${newTag}\n`);

  const result = processBook(bookPath, newTag, description);
  if (result.changed) {
    console.log(`\nSummary: 1 book modified, ${result.changeCount} chapter tags updated`);
  } else {
    console.log(`\nNo changes needed.`);
  }
  return result;
}

// Main
const baseDir = path.join(__dirname, '..');

// 1. Feminism-and-equality shelf -> add 'feminism' tag
const feminismPath = path.join(baseDir, 'perspectives-libraries', 'cultural-and-identity', 'feminism-and-equality');

// 2. Abortion shelf -> add 'reproductive-rights' tag
const abortionPath = path.join(baseDir, 'perspectives-libraries', 'cultural-and-identity', 'abortion');

// 3. Women's Rights history book -> add 'womens-history' tag
const womensRightsBook = path.join(baseDir, 'knowledge-libraries', 'the-sciences', 'history-and-anthropology', 'womens-rights-centuries-of-struggle.json');

// 4. RBG biography -> add 'womens-history' tag
const rbgBook = path.join(baseDir, 'knowledge-libraries', 'biographies', 'political-biographies', 'ruth-bader-ginsburg-a-biography.json');

let grandTotal = { books: 0, changes: 0 };

// Process feminism-and-equality shelf
if (fs.existsSync(feminismPath)) {
  const r = processShelf(feminismPath, 'feminism', 'Feminism and Equality');
  grandTotal.books += r.booksChanged;
  grandTotal.changes += r.totalChanges;
}

// Process abortion shelf
if (fs.existsSync(abortionPath)) {
  const r = processShelf(abortionPath, 'reproductive-rights', 'Abortion');
  grandTotal.books += r.booksChanged;
  grandTotal.changes += r.totalChanges;
}

// Process Women's Rights history book
if (fs.existsSync(womensRightsBook)) {
  const r = processSingleBook(womensRightsBook, 'womens-history', 'Women\'s Rights: Centuries of Struggle');
  if (r.changed) {
    grandTotal.books += 1;
    grandTotal.changes += r.changeCount;
  }
}

// Process RBG biography
if (fs.existsSync(rbgBook)) {
  const r = processSingleBook(rbgBook, 'womens-history', 'Ruth Bader Ginsburg Biography');
  if (r.changed) {
    grandTotal.books += 1;
    grandTotal.changes += r.changeCount;
  }
}

console.log(`\n=== GRAND TOTAL ===`);
console.log(`Books modified: ${grandTotal.books}`);
console.log(`Chapter tags updated: ${grandTotal.changes}`);
console.log(`\nDon't forget to rebuild discovery index: node libraries/_utils/build-discovery-index-v2.js`);
