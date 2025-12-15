const fs = require('fs');
const path = require('path');

const perspectivesBase = path.join(__dirname, 'perspectives-libraries');

console.log('=== PERSPECTIVES-LIBRARIES TAXONOMY ===\n');
console.log('LIBRARY TYPE: Perspectives Libraries');
console.log('│');

const categories = fs.readdirSync(perspectivesBase, { withFileTypes: true })
  .filter(d => d.isDirectory() && !d.name.startsWith('_'))
  .map(d => d.name);

categories.forEach((cat, catIdx) => {
  const catPath = path.join(perspectivesBase, cat);
  const isLastCat = catIdx === categories.length - 1;
  const catPrefix = isLastCat ? '└──' : '├──';
  const catContinue = isLastCat ? '    ' : '│   ';

  console.log(`${catPrefix} 📁 CATEGORY: ${cat}`);

  // Get items in category
  const items = fs.readdirSync(catPath, { withFileTypes: true })
    .filter(d => !d.name.startsWith('_'));

  const books = items.filter(d => d.isFile() && d.name.endsWith('.json'));
  const libraries = items.filter(d => d.isDirectory());

  const allItems = [...books.map(b => ({ type: 'book', name: b.name })),
                    ...libraries.map(l => ({ type: 'library', name: l.name }))];

  allItems.forEach((item, itemIdx) => {
    const isLastItem = itemIdx === allItems.length - 1;
    const itemPrefix = isLastItem ? '└──' : '├──';
    const itemContinue = isLastItem ? '    ' : '│   ';

    if (item.type === 'book') {
      const bookPath = path.join(catPath, item.name);
      const data = JSON.parse(fs.readFileSync(bookPath, 'utf8'));
      const chapters = data.chapters ? data.chapters.length : 0;
      const topics = data.chapters ? data.chapters.reduce((sum, ch) => sum + (ch.topics ? ch.topics.length : 0), 0) : 0;
      const bookName = item.name.replace('.json', '');
      console.log(`${catContinue}${itemPrefix} 📖 BOOK: ${bookName}`);
      console.log(`${catContinue}${itemContinue}     (${chapters} chapters, ${topics} topics)`);
    } else {
      const libPath = path.join(catPath, item.name);
      console.log(`${catContinue}${itemPrefix} 📚 LIBRARY: ${item.name}`);

      // Get shelves
      const shelves = fs.readdirSync(libPath, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith('_'));

      shelves.forEach((shelf, shelfIdx) => {
        const isLastShelf = shelfIdx === shelves.length - 1;
        const shelfPrefix = isLastShelf ? '└──' : '├──';
        const shelfContinue = isLastShelf ? '    ' : '│   ';

        const shelfPath = path.join(libPath, shelf.name);
        const bookFiles = fs.readdirSync(shelfPath)
          .filter(f => f.endsWith('.json') && !f.startsWith('_'));

        console.log(`${catContinue}${itemContinue}    ${shelfPrefix} 📂 SHELF: ${shelf.name}`);

        bookFiles.forEach((bookFile, bookIdx) => {
          const isLastBook = bookIdx === bookFiles.length - 1;
          const bookPrefix = isLastBook ? '└──' : '├──';

          const bookPath = path.join(shelfPath, bookFile);
          const data = JSON.parse(fs.readFileSync(bookPath, 'utf8'));
          const chapters = data.chapters ? data.chapters.length : 0;
          const topics = data.chapters ? data.chapters.reduce((sum, ch) => sum + (ch.topics ? ch.topics.length : 0), 0) : 0;
          const bookName = bookFile.replace('.json', '');

          console.log(`${catContinue}${itemContinue}    ${shelfContinue}   ${bookPrefix} 📖 BOOK: ${bookName}`);
          console.log(`${catContinue}${itemContinue}    ${shelfContinue}        (${chapters} chapters, ${topics} topics)`);
        });
      });
    }
  });

  console.log('│');
});
