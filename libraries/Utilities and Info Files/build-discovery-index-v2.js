/**
 * Build discovery index for folder-based library structure
 *
 * Scans: migrated/{library-type}/{library}/{shelf}/{book}.json
 * Creates: discovery-index.json for tag-based chapter discovery
 *
 * Usage: node build-discovery-index-v2.js
 */

const fs = require('fs');
const path = require('path');

const MIGRATED_DIR = path.join(__dirname, '..');

// Library type configurations
// Abbreviations MUST match index.html typeAbbreviations (pr, pe, not p, v)
const LIBRARY_TYPES = {
    'knowledge-libraries': { abbrev: 'k', name: 'Knowledge' },
    'practical-libraries': { abbrev: 'pr', name: 'Practical Skills' },
    'event-libraries': { abbrev: 'e', name: 'Events' },
    'perspectives-libraries': { abbrev: 'pe', name: 'Perspectives' },
    'candidate-libraries': { abbrev: 'c', name: 'Candidates' },
    'geography-libraries': { abbrev: 'g', name: 'Geography' },
    'infrastructure-libraries': { abbrev: 'i', name: 'Infrastructure' }
    // 'questions-libraries' excluded - not content libraries
};

// Convert slug to display name
function slugToName(slug) {
    if (!slug) return '';
    return slug
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Convert name to URL-safe slug
function toSlug(str) {
    if (!str) return '';
    return str.toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/(^-|-$)/g, '');
}

// Get display name from _meta.json or convert slug
function getDisplayName(dirPath, slug) {
    const metaPath = path.join(dirPath, '_meta.json');
    if (fs.existsSync(metaPath)) {
        try {
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            if (meta.name) return meta.name;
        } catch (e) {}
    }
    return slugToName(slug);
}

// Get directories in a path
function getDirectories(dirPath) {
    if (!fs.existsSync(dirPath)) return [];
    return fs.readdirSync(dirPath, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith('.'))
        .map(d => d.name)
        .sort();
}

// Get JSON files (excluding _meta.json and _manifest.json)
function getJsonFiles(dirPath) {
    if (!fs.existsSync(dirPath)) return [];
    return fs.readdirSync(dirPath)
        .filter(f => f.endsWith('.json') && !f.startsWith('_'))
        .sort();
}

// Main processing
const chapters = [];
const byTag = {};

// Process each library type
for (const [typeSlug, typeConfig] of Object.entries(LIBRARY_TYPES)) {
    const typePath = path.join(MIGRATED_DIR, typeSlug);
    if (!fs.existsSync(typePath)) {
        console.log(`Skipping ${typeSlug} - folder not found`);
        continue;
    }

    console.log(`\nProcessing ${typeConfig.name}...`);

    // Process each library
    const libraries = getDirectories(typePath);
    for (const librarySlug of libraries) {
        const libraryPath = path.join(typePath, librarySlug);
        const libraryName = getDisplayName(libraryPath, librarySlug);

        // Process each shelf
        const shelves = getDirectories(libraryPath);
        for (const shelfSlug of shelves) {
            const shelfPath = path.join(libraryPath, shelfSlug);
            const shelfName = getDisplayName(shelfPath, shelfSlug);

            // Process each book
            const bookFiles = getJsonFiles(shelfPath);
            for (const bookFile of bookFiles) {
                const bookSlug = bookFile.replace('.json', '');
                const bookPath = path.join(shelfPath, bookFile);

                try {
                    const bookData = JSON.parse(fs.readFileSync(bookPath, 'utf8'));
                    const bookName = bookData.name || slugToName(bookSlug);

                    if (!bookData.chapters) continue;

                    // Process each chapter
                    for (const chapter of bookData.chapters) {
                        const chapterName = typeof chapter === 'string' ? chapter : chapter.name;
                        if (!chapterName) continue;

                        // Skip chapters without tags
                        const tags = chapter.tags || [];
                        if (tags.length === 0) continue;

                        const chapterIndex = chapters.length;
                        const chapterSlug = chapter.slug || toSlug(chapterName);

                        // Build the chapter entry
                        const entry = {
                            name: chapterName,
                            path: `${libraryName} → ${shelfName} → ${bookName}`,
                            libraryType: typeConfig.name,
                            typeAbbrev: typeConfig.abbrev,
                            folder: typeSlug,
                            library: libraryName,
                            librarySlug: librarySlug,
                            shelf: shelfName,
                            shelfSlug: shelfSlug,
                            book: bookName,
                            bookSlug: bookSlug,
                            chapterSlug: chapterSlug,
                            tags: tags,
                            topicCount: chapter.topics ? chapter.topics.length : 0
                        };

                        chapters.push(entry);

                        // Index by tag
                        for (const tag of tags) {
                            if (!byTag[tag]) byTag[tag] = [];
                            byTag[tag].push(chapterIndex);
                        }
                    }
                } catch (e) {
                    console.error(`  Error processing ${bookFile}:`, e.message);
                }
            }
        }
    }

    console.log(`  Processed ${libraries.length} libraries`);
}

// Build the final index
const index = {
    meta: {
        version: '2.0',
        structure: 'folder-based',
        generated: new Date().toISOString(),
        totalChapters: chapters.length,
        totalTags: Object.keys(byTag).length
    },
    chapters,
    byTag
};

// Write the index
const outputPath = path.join(__dirname, '..', 'discovery-index.json');
fs.writeFileSync(outputPath, JSON.stringify(index, null, 2), 'utf8');

console.log('\n=== DISCOVERY INDEX BUILT ===');
console.log('Chapters indexed:', chapters.length);
console.log('Tags indexed:', Object.keys(byTag).length);
console.log('Output:', outputPath);

// Show top tags by chapter count
console.log('\n=== TOP TAGS ===');
const sortedTags = Object.entries(byTag)
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 15);

sortedTags.forEach(([tag, indices]) => {
    console.log(`  ${tag}: ${indices.length} chapters`);
});
