/**
 * Correctly collapse a consolidated library file into a single book
 *
 * Original structure: Library > Shelf > Book > Chapter (chapter name = topic)
 * Collapsed structure: Book > Chapter (from Shelf) > Topics (from all chapter names)
 */

const fs = require('fs');
const path = require('path');

const inputFile = process.argv[2];
if (!inputFile) {
  console.log('Usage: node collapse-one.js <input-file.json>');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

if (!data.shelves) {
  console.log('This file does not have shelves - not a consolidated format');
  process.exit(1);
}

console.log(`\nCollapsing: ${data.library || 'Unknown'}`);
console.log(`Description: ${data.description || 'None'}`);
console.log(`Shelves: ${data.shelves.length}`);

const collapsedBook = {
  name: data.library,
  description: data.description,
  chapters: []
};

data.shelves.forEach(shelf => {
  console.log(`\n  Shelf: ${shelf.name}`);

  // Each shelf becomes a chapter
  const chapter = {
    name: shelf.name,
    topics: [],
    tags: new Set()
  };

  // Collect all chapter names from all books as topics
  if (shelf.books) {
    shelf.books.forEach(book => {
      console.log(`    Book: ${book.name} (${book.chapters ? book.chapters.length : 0} chapters)`);

      if (book.chapters) {
        book.chapters.forEach(ch => {
          // Chapter name becomes a topic
          chapter.topics.push(ch.name);

          // Collect tags
          if (ch.tags) {
            ch.tags.forEach(t => chapter.tags.add(t));
          }
        });
      }
    });
  }

  // Convert tags Set to Array
  chapter.tags = Array.from(chapter.tags);

  console.log(`    → Chapter "${shelf.name}": ${chapter.topics.length} topics, ${chapter.tags.length} tags`);

  collapsedBook.chapters.push(chapter);
});

// Summary
const totalTopics = collapsedBook.chapters.reduce((sum, ch) => sum + ch.topics.length, 0);
console.log(`\n=== RESULT ===`);
console.log(`Book: ${collapsedBook.name}`);
console.log(`Chapters: ${collapsedBook.chapters.length}`);
console.log(`Total topics: ${totalTopics}`);

// Show preview
console.log('\n=== PREVIEW ===');
collapsedBook.chapters.forEach(ch => {
  console.log(`\nChapter: ${ch.name}`);
  console.log(`  Topics (${ch.topics.length}):`);
  ch.topics.slice(0, 5).forEach(t => console.log(`    - ${t}`));
  if (ch.topics.length > 5) console.log(`    ... and ${ch.topics.length - 5} more`);
});

// Write output
const outputFile = inputFile.replace('.json', '-collapsed.json');
fs.writeFileSync(outputFile, JSON.stringify(collapsedBook, null, 2));
console.log(`\nWritten to: ${outputFile}`);
