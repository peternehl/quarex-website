/**
 * Build Book Index for Quarex
 * Generates a searchable index of all books with names and paths
 * Run: node libraries/_utils/build-book-index.js
 */

const fs = require('fs');
const path = require('path');

const LIBRARIES_ROOT = path.join(__dirname, '..');
const OUTPUT_FILE = path.join(LIBRARIES_ROOT, 'book-index.json');

// Library type mappings (folder name -> URL prefix)
// Must match typeAbbreviations in libraries/index.html
const LIBRARY_TYPES = {
  'knowledge-libraries': 'k',
  'practical-libraries': 'pr',
  'event-libraries': 'e',
  'perspectives-libraries': 'pe',
  'politician-libraries': 'c',
  'geography-libraries': 'g',
  'infrastructure-libraries': 'i'
};

function getBooks() {
  const books = [];

  // Iterate through each library type folder
  for (const [libraryTypeFolder, urlPrefix] of Object.entries(LIBRARY_TYPES)) {
    const libraryTypePath = path.join(LIBRARIES_ROOT, libraryTypeFolder);

    if (!fs.existsSync(libraryTypePath)) continue;

    // Get all libraries in this type
    const libraries = fs.readdirSync(libraryTypePath, { withFileTypes: true })
      .filter(d => d.isDirectory() && !d.name.startsWith('_'));

    for (const library of libraries) {
      const libraryPath = path.join(libraryTypePath, library.name);

      // Get all shelves in this library
      const shelves = fs.readdirSync(libraryPath, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith('_'));

      for (const shelf of shelves) {
        const shelfPath = path.join(libraryPath, shelf.name);

        // Get all book JSON files in this shelf
        const bookFiles = fs.readdirSync(shelfPath)
          .filter(f => f.endsWith('.json') && !f.startsWith('_'));

        for (const bookFile of bookFiles) {
          const bookPath = path.join(shelfPath, bookFile);

          try {
            const bookData = JSON.parse(fs.readFileSync(bookPath, 'utf8'));
            const slug = bookFile.replace('.json', '');

            // Handle different book structures
            const bookName = bookData.name || bookData.book || slug;
            const chapterCount = bookData.chapters ? bookData.chapters.length : 0;

            books.push({
              name: bookName,
              path: `${urlPrefix}/${library.name}/${shelf.name}/${slug}`,
              library: library.name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
              shelf: shelf.name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
              chapters: chapterCount
            });
          } catch (err) {
            console.error(`Error reading ${bookPath}: ${err.message}`);
          }
        }
      }
    }
  }

  // Sort alphabetically by name
  books.sort((a, b) => a.name.localeCompare(b.name));

  return books;
}

function main() {
  console.log('Building book index...\n');

  const books = getBooks();

  const index = {
    generated: new Date().toISOString().split('T')[0],
    count: books.length,
    books: books
  };

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(index, null, 2));

  console.log(`=== BOOK INDEX BUILT ===`);
  console.log(`Books indexed: ${books.length}`);
  console.log(`Output: ${OUTPUT_FILE}`);
}

main();
