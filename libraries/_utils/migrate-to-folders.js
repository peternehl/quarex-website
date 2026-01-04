/**
 * Migration Script: Convert flat library JSON files to folder-based structure
 *
 * Current structure:
 *   unlimited/knowledge-libraries/the_sciences.json
 *   (contains: library → shelves → books → chapters → topics)
 *
 * New structure:
 *   unlimited/knowledge-libraries/the-sciences/physical-sciences/physics-fundamentals.json
 *   (folder path = library/shelf, file = book with chapters/topics)
 *
 * Usage: node migrate-to-folders.js [--dry-run] [--type knowledge]
 */

const fs = require('fs');
const path = require('path');

// Configuration
const UNLIMITED_DIR = __dirname;
const SOURCE_DIR = process.argv.find(arg => arg.startsWith('--source='))?.split('=')[1]
  || path.join(__dirname, 'downloaded-from-cpanel'); // Default to cPanel download
const OUTPUT_DIR = path.join(__dirname, 'migrated'); // Output to separate folder first

const DRY_RUN = process.argv.includes('--dry-run');
const TYPE_FILTER = process.argv.find(arg => arg.startsWith('--type='))?.split('=')[1];

// Library type configurations
const LIBRARY_TYPES = {
  'knowledge-libraries': { abbrev: 'k', name: 'Knowledge Libraries', icon: '📚' },
  'practical-libraries': { abbrev: 'p', name: 'Practical Libraries', icon: '🔧' },
  'event-libraries': { abbrev: 'e', name: 'Event Libraries', icon: '📅' },
  'perspectives-libraries': { abbrev: 'v', name: 'Perspectives Libraries', icon: '💭' },
  'politician-libraries': { abbrev: 'c', name: 'Politician Libraries', icon: '🗳️' },
  'geography-libraries': { abbrev: 'g', name: 'Geography Libraries', icon: '🌍' },
  'infrastucture-libraries': { abbrev: 'i', name: 'Infrastructure Libraries', icon: '🏗️' },
  'questions-libraries': { abbrev: 'q', name: 'Questions Libraries', icon: '❓' }
};

// Files to skip (not actual library content)
const SKIP_FILES = [
  'inventory.json',
  'get-available-books.js',
  'strip_',
  '-bare.json',
  'taxonomy-test.json'
];

// Utility: Convert string to URL-safe slug
function slugify(str) {
  return str
    .toLowerCase()
    .replace(/['']/g, '')           // Remove apostrophes
    .replace(/[&]/g, 'and')         // Replace & with 'and'
    .replace(/[:]/g, '')            // Remove colons
    .replace(/[^\w\s-]/g, '')       // Remove special chars
    .replace(/[_\s]+/g, '-')        // Underscores and spaces to hyphens
    .replace(/-+/g, '-')            // Collapse multiple hyphens
    .replace(/^-|-$/g, '');         // Trim hyphens from ends
}

// Utility: Create directory recursively
function ensureDir(dirPath) {
  if (DRY_RUN) {
    console.log(`  [DRY-RUN] Would create directory: ${dirPath}`);
    return;
  }
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

// Utility: Write JSON file
function writeJsonFile(filePath, data) {
  if (DRY_RUN) {
    console.log(`  [DRY-RUN] Would write file: ${filePath}`);
    return;
  }
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
}

// Check if file should be skipped
function shouldSkipFile(filename) {
  return SKIP_FILES.some(skip => filename.includes(skip));
}

// Process a single library JSON file
function processLibraryFile(libraryTypeDir, filename) {
  const filePath = path.join(libraryTypeDir, filename);
  const libraryTypeName = path.basename(libraryTypeDir);

  console.log(`\nProcessing: ${filename}`);

  let data;
  try {
    data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (err) {
    console.log(`  ERROR: Could not parse ${filename}: ${err.message}`);
    return { books: 0, chapters: 0, error: true };
  }

  // Get library name
  const libraryName = data.library || data.name;
  if (!libraryName) {
    console.log(`  ERROR: No library name found in ${filename}`);
    return { books: 0, chapters: 0, error: true };
  }

  const librarySlug = slugify(libraryName);
  console.log(`  Library: "${libraryName}" → ${librarySlug}/`);

  // Create library directory
  const libraryDir = path.join(OUTPUT_DIR, libraryTypeName, librarySlug);
  ensureDir(libraryDir);

  // Create library _meta.json if there's a description
  if (data.description) {
    const libraryMeta = {
      name: libraryName,
      description: data.description
    };
    if (data.created_by) libraryMeta.created_by = data.created_by;
    writeJsonFile(path.join(libraryDir, '_meta.json'), libraryMeta);
    console.log(`  Created _meta.json for library`);
  }

  let totalBooks = 0;
  let totalChapters = 0;

  // Process shelves
  const shelves = data.shelves || [];
  if (shelves.length === 0) {
    console.log(`  WARNING: No shelves found in ${filename}`);
    return { books: 0, chapters: 0 };
  }

  shelves.forEach(shelf => {
    const shelfName = shelf.name;
    const shelfSlug = slugify(shelfName);
    console.log(`    Shelf: "${shelfName}" → ${shelfSlug}/`);

    // Create shelf directory
    const shelfDir = path.join(libraryDir, shelfSlug);
    ensureDir(shelfDir);

    // Create shelf _meta.json if there's a description
    if (shelf.description) {
      const shelfMeta = {
        name: shelfName,
        description: shelf.description
      };
      writeJsonFile(path.join(shelfDir, '_meta.json'), shelfMeta);
    }

    // Process books
    const books = shelf.books || [];
    books.forEach(book => {
      // Handle both formats: book as object or book as just having chapters directly in shelf
      const bookName = book.name || book;
      const bookSlug = slugify(bookName);

      // Build book JSON
      const bookData = {
        name: bookName
      };

      // Add optional fields if present
      if (book.description) bookData.description = book.description;
      if (book.tags && book.tags.length > 0) bookData.tags = book.tags;
      if (book.created_by) bookData.created_by = book.created_by;

      // Add chapters
      if (book.chapters && Array.isArray(book.chapters)) {
        bookData.chapters = book.chapters.map(chapter => {
          const chapterData = {
            name: chapter.name,
            topics: chapter.topics || []
          };
          if (chapter.tags && chapter.tags.length > 0) {
            chapterData.tags = chapter.tags;
          }
          totalChapters++;
          return chapterData;
        });
      } else {
        bookData.chapters = [];
        console.log(`      WARNING: No chapters in book "${bookName}"`);
      }

      // Write book file
      const bookFilePath = path.join(shelfDir, `${bookSlug}.json`);
      writeJsonFile(bookFilePath, bookData);
      console.log(`      Book: "${bookName}" → ${bookSlug}.json (${bookData.chapters.length} chapters)`);

      totalBooks++;
    });
  });

  return { books: totalBooks, chapters: totalChapters };
}

// Process a library type directory
function processLibraryType(libraryTypeName) {
  const libraryTypeDir = path.join(SOURCE_DIR, libraryTypeName);

  if (!fs.existsSync(libraryTypeDir)) {
    console.log(`Directory not found: ${libraryTypeDir}`);
    return;
  }

  const typeConfig = LIBRARY_TYPES[libraryTypeName];
  if (!typeConfig) {
    console.log(`Unknown library type: ${libraryTypeName}`);
    return;
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log(`Processing Library Type: ${libraryTypeName}`);
  console.log(`${'='.repeat(60)}`);

  // Create library type directory in output
  const outputTypeDir = path.join(OUTPUT_DIR, libraryTypeName);
  ensureDir(outputTypeDir);

  // Create library type _meta.json
  const typeMeta = {
    abbrev: typeConfig.abbrev,
    name: typeConfig.name,
    icon: typeConfig.icon
  };
  writeJsonFile(path.join(outputTypeDir, '_meta.json'), typeMeta);

  // Find all JSON files in the directory
  const files = fs.readdirSync(libraryTypeDir)
    .filter(f => f.endsWith('.json') && !shouldSkipFile(f));

  let totalBooks = 0;
  let totalChapters = 0;
  let processedFiles = 0;
  let errorFiles = 0;

  files.forEach(file => {
    const result = processLibraryFile(libraryTypeDir, file);
    totalBooks += result.books;
    totalChapters += result.chapters;
    processedFiles++;
    if (result.error) errorFiles++;
  });

  console.log(`\nSummary for ${libraryTypeName}:`);
  console.log(`  Files processed: ${processedFiles}`);
  console.log(`  Errors: ${errorFiles}`);
  console.log(`  Total books: ${totalBooks}`);
  console.log(`  Total chapters: ${totalChapters}`);

  return { files: processedFiles, books: totalBooks, chapters: totalChapters, errors: errorFiles };
}

// Main execution
function main() {
  console.log('TruthAngel Library Migration Script');
  console.log('====================================');
  console.log(`Mode: ${DRY_RUN ? 'DRY RUN (no files will be created)' : 'LIVE'}`);
  console.log(`Source directory: ${SOURCE_DIR}`);
  console.log(`Output directory: ${OUTPUT_DIR}`);

  if (TYPE_FILTER) {
    console.log(`Filtering to type: ${TYPE_FILTER}`);
  }

  // Create output directory
  ensureDir(OUTPUT_DIR);

  const typesToProcess = TYPE_FILTER
    ? [`${TYPE_FILTER}-libraries`]
    : Object.keys(LIBRARY_TYPES);

  let grandTotalBooks = 0;
  let grandTotalChapters = 0;
  let grandTotalErrors = 0;

  typesToProcess.forEach(typeName => {
    const result = processLibraryType(typeName);
    if (result) {
      grandTotalBooks += result.books;
      grandTotalChapters += result.chapters;
      grandTotalErrors += result.errors;
    }
  });

  console.log(`\n${'='.repeat(60)}`);
  console.log('MIGRATION COMPLETE');
  console.log(`${'='.repeat(60)}`);
  console.log(`Total books migrated: ${grandTotalBooks}`);
  console.log(`Total chapters migrated: ${grandTotalChapters}`);
  console.log(`Total errors: ${grandTotalErrors}`);

  if (DRY_RUN) {
    console.log('\nThis was a DRY RUN. No files were created.');
    console.log('Run without --dry-run to perform actual migration.');
  } else {
    console.log(`\nMigrated files are in: ${OUTPUT_DIR}`);
    console.log('Review the output, then move to replace the original structure.');
  }
}

main();
