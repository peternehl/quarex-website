/**
 * Generate comprehensive sitemap.xml from book-index.json and politician libraries
 * Run: node libraries/_utils/generate-sitemap.js
 */

const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://quarex.org';

// Helper: convert name to URL slug
function slugify(str) {
  return str
    .toLowerCase()
    .replace(/[()]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// Read book index
const bookIndexPath = path.join(__dirname, '..', 'book-index.json');
const bookIndex = JSON.parse(fs.readFileSync(bookIndexPath, 'utf8'));

// Start building sitemap
let xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- Main pages -->
  <url>
    <loc>${BASE_URL}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>${BASE_URL}/libraries/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>${BASE_URL}/libraries/library-tree.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>${BASE_URL}/ask/ask.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>${BASE_URL}/candidates/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>

  <!-- Info pages -->
  <url>
    <loc>${BASE_URL}/spec/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>${BASE_URL}/schema/v1/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>${BASE_URL}/ethics/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>${BASE_URL}/privacy.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>${BASE_URL}/help/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>

  <!-- Reports -->
  <url>
    <loc>${BASE_URL}/reports/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>

  <!-- Tools -->
  <url>
    <loc>${BASE_URL}/tools/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>${BASE_URL}/tools/zip-lookup.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>

`;

let bookCount = 0;
let candidateCount = 0;

// Add all books from book-index
console.log(`Adding ${bookIndex.books.length} books to sitemap...`);
bookIndex.books.forEach(book => {
  const url = `${BASE_URL}/libraries/${book.path}`;
  xml += `  <url>
    <loc>${url}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
`;
  bookCount++;
});

// Process politician libraries for candidate-level URLs
const politicianLibsPath = path.join(__dirname, '..', 'politician-libraries');

function processDirectory(dirPath, librarySlug, shelfSlug) {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    if (entry.isDirectory()) {
      // Recurse into subdirectories
      const subDir = path.join(dirPath, entry.name);
      // Determine if this is a library or shelf level
      const parentDir = path.basename(dirPath);
      if (parentDir === 'politician-libraries') {
        // This is a library
        processDirectory(subDir, entry.name, null);
      } else if (!shelfSlug) {
        // This is a shelf
        processDirectory(subDir, librarySlug, entry.name);
      } else {
        // This is a state folder (for House)
        processDirectory(subDir, librarySlug, shelfSlug);
      }
    } else if (entry.isFile() && entry.name.endsWith('.json') &&
               !entry.name.startsWith('_') &&
               entry.name !== 'us_house_2026_complete.json' &&
               entry.name !== 'us_senate_2026_complete.json' &&
               entry.name !== 'us_governors_2026.json') {
      // Process JSON file
      const filePath = path.join(dirPath, entry.name);
      try {
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        if (data.book && data.chapters) {
          const bookSlug = slugify(data.book);

          // Determine the base path based on directory structure
          const relativePath = path.relative(politicianLibsPath, dirPath);
          const pathParts = relativePath.split(path.sep);

          // Build the URL path
          let urlPath = `c/${pathParts.join('/')}/${bookSlug}`;

          // Add chapter and topic URLs
          for (const chapter of data.chapters) {
            const chapterSlug = slugify(chapter.name);

            // Add chapter URL
            const chapterUrl = `${BASE_URL}/libraries/${urlPath}/${chapterSlug}`;
            xml += `  <url>
    <loc>${chapterUrl}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
`;

            // Add topic (candidate) URLs
            if (chapter.topics) {
              for (const topic of chapter.topics) {
                const topicSlug = slugify(topic);
                const topicUrl = `${BASE_URL}/libraries/${urlPath}/${chapterSlug}/${topicSlug}`;
                xml += `  <url>
    <loc>${topicUrl}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>
`;
                candidateCount++;
              }
            }
          }
        }
      } catch (err) {
        // Skip files that can't be parsed
      }
    }
  }
}

console.log('Processing politician libraries...');
processDirectory(politicianLibsPath, null, null);

xml += `</urlset>
`;

// Write sitemap
const sitemapPath = path.join(__dirname, '..', '..', 'sitemap.xml');
fs.writeFileSync(sitemapPath, xml);

const staticPages = 14;
const total = staticPages + bookCount + candidateCount;
console.log(`Sitemap generated: ${sitemapPath}`);
console.log(`Total URLs: ${total}`);
console.log(`  - Static pages: ${staticPages}`);
console.log(`  - Books: ${bookCount}`);
console.log(`  - Candidate pages: ${candidateCount}`);
