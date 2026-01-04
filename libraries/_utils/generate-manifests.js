/**
 * Generate _manifest.json files for the folder-based library structure
 *
 * Creates manifest files at each level:
 * - {library-type}/_manifest.json - lists all libraries
 * - {library-type}/{library}/_manifest.json - lists all shelves
 * - {library-type}/{library}/{shelf}/_manifest.json - lists all books
 *
 * Usage: node generate-manifests.js
 */

const fs = require('fs');
const path = require('path');

const MIGRATED_DIR = path.join(__dirname, 'migrated');

// Convert slug to display name
function slugToName(slug) {
    if (!slug) return '';
    return slug
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
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

// Get description from _meta.json
function getDescription(dirPath) {
    const metaPath = path.join(dirPath, '_meta.json');
    if (fs.existsSync(metaPath)) {
        try {
            const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            return meta.description || null;
        } catch (e) {}
    }
    return null;
}

// Get directories in a path
function getDirectories(dirPath) {
    if (!fs.existsSync(dirPath)) return [];
    return fs.readdirSync(dirPath, { withFileTypes: true })
        .filter(d => d.isDirectory() && !d.name.startsWith('.'))
        .map(d => d.name)
        .sort();
}

// Get JSON files in a path (excluding _meta.json and _manifest.json)
function getJsonFiles(dirPath) {
    if (!fs.existsSync(dirPath)) return [];
    return fs.readdirSync(dirPath)
        .filter(f => f.endsWith('.json') && f !== '_meta.json' && f !== '_manifest.json')
        .sort();
}

// Count items in a directory
function countDirectories(dirPath) {
    return getDirectories(dirPath).length;
}

function countJsonFiles(dirPath) {
    return getJsonFiles(dirPath).length;
}

// Generate manifest for library types
function generateLibraryTypeManifests() {
    console.log('\n=== Generating Library Type Manifests ===\n');

    const libraryTypes = getDirectories(MIGRATED_DIR);

    for (const typeSlug of libraryTypes) {
        const typePath = path.join(MIGRATED_DIR, typeSlug);
        const libraries = getDirectories(typePath);

        const manifest = libraries.map(libSlug => {
            const libPath = path.join(typePath, libSlug);
            return {
                slug: libSlug,
                name: getDisplayName(libPath, libSlug),
                description: getDescription(libPath),
                shelfCount: countDirectories(libPath)
            };
        });

        const manifestPath = path.join(typePath, '_manifest.json');
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
        console.log(`Created: ${typeSlug}/_manifest.json (${manifest.length} libraries)`);

        // Generate manifests for each library
        generateLibraryManifests(typePath, typeSlug);
    }
}

// Generate manifests for libraries (listing shelves)
function generateLibraryManifests(typePath, typeSlug) {
    const libraries = getDirectories(typePath);

    for (const libSlug of libraries) {
        const libPath = path.join(typePath, libSlug);
        const shelves = getDirectories(libPath);

        const manifest = shelves.map(shelfSlug => {
            const shelfPath = path.join(libPath, shelfSlug);
            return {
                slug: shelfSlug,
                name: getDisplayName(shelfPath, shelfSlug),
                description: getDescription(shelfPath),
                bookCount: countJsonFiles(shelfPath)
            };
        });

        const manifestPath = path.join(libPath, '_manifest.json');
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
        console.log(`  Created: ${typeSlug}/${libSlug}/_manifest.json (${manifest.length} shelves)`);

        // Generate manifests for each shelf
        generateShelfManifests(libPath, typeSlug, libSlug);
    }
}

// Generate manifests for shelves (listing books)
function generateShelfManifests(libPath, typeSlug, libSlug) {
    const shelves = getDirectories(libPath);

    for (const shelfSlug of shelves) {
        const shelfPath = path.join(libPath, shelfSlug);
        const bookFiles = getJsonFiles(shelfPath);

        const manifest = bookFiles.map(filename => {
            const bookSlug = filename.replace('.json', '');
            const bookPath = path.join(shelfPath, filename);

            let bookData = {};
            try {
                bookData = JSON.parse(fs.readFileSync(bookPath, 'utf8'));
            } catch (e) {
                console.error(`    Error reading ${filename}:`, e.message);
            }

            return {
                slug: bookSlug,
                name: bookData.name || slugToName(bookSlug),
                description: bookData.description || null,
                chapterCount: bookData.chapters?.length || 0,
                tags: bookData.tags || [],
                created_by: bookData.created_by || null
            };
        });

        const manifestPath = path.join(shelfPath, '_manifest.json');
        fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
        console.log(`    Created: ${typeSlug}/${libSlug}/${shelfSlug}/_manifest.json (${manifest.length} books)`);
    }
}

// Main
function main() {
    console.log('Manifest Generator for TruthAngel Libraries');
    console.log('============================================');
    console.log(`Source: ${MIGRATED_DIR}`);

    if (!fs.existsSync(MIGRATED_DIR)) {
        console.error('Error: migrated directory not found');
        process.exit(1);
    }

    generateLibraryTypeManifests();

    console.log('\n=== Done! ===');
}

main();
