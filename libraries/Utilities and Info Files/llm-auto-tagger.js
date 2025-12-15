#!/usr/bin/env node
/**
 * TruthAngel LLM Auto-Tagger (Claude Haiku)
 * Uses Claude Haiku to generate semantically accurate tags for chapters
 *
 * Usage:
 *   node llm-auto-tagger.js <book.json>           # Tag a single book
 *   node llm-auto-tagger.js --dry-run <book.json> # Preview without saving
 *   node llm-auto-tagger.js --all                 # Tag all books (careful!)
 *   node llm-auto-tagger.js --test                # Test with one chapter
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// =============================================================================
// CONFIGURATION
// =============================================================================

const SCRIPT_DIR = __dirname;
const SECRETS_PATH = path.join(SCRIPT_DIR, '../../template-files/secrets.js');
const TAG_VOCAB_PATH = path.join(SCRIPT_DIR, 'tag-vocabulary.json');

// Rate limiting - Haiku can handle high throughput
const REQUESTS_PER_MINUTE = 50;  // Conservative, can go higher
const DELAY_MS = Math.ceil(60000 / REQUESTS_PER_MINUTE);

// Model configuration
const MODEL = 'claude-3-5-haiku-20241022';

// =============================================================================
// LOAD API KEY
// =============================================================================

function loadApiKey() {
  if (!fs.existsSync(SECRETS_PATH)) {
    throw new Error(`secrets.js not found at ${SECRETS_PATH}`);
  }

  const content = fs.readFileSync(SECRETS_PATH, 'utf8');
  const match = content.match(/ANTHROPIC_API_KEY\s*=\s*['"]([^'"]+)['"]/);
  if (!match) {
    throw new Error('Could not find ANTHROPIC_API_KEY in secrets.js');
  }
  return match[1];
}

// =============================================================================
// LOAD TAG VOCABULARY
// =============================================================================

function loadTagVocabulary() {
  const vocab = JSON.parse(fs.readFileSync(TAG_VOCAB_PATH, 'utf8'));
  const validTags = {
    broad: new Set(vocab.tags.broad.map(t => t.id)),
    medium: new Set(vocab.tags.medium.map(t => t.id)),
    specific: new Set(vocab.tags.specific.map(t => t.id)),
    all: new Set()
  };

  // Combine all valid tags
  vocab.tags.broad.forEach(t => validTags.all.add(t.id));
  vocab.tags.medium.forEach(t => validTags.all.add(t.id));
  vocab.tags.specific.forEach(t => validTags.all.add(t.id));

  return { vocab, validTags };
}

// =============================================================================
// CLAUDE API CALL
// =============================================================================

function callClaude(apiKey, prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: MODEL,
      max_tokens: 200,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const options = {
      hostname: 'api.anthropic.com',
      path: '/v1/messages',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'Content-Length': Buffer.byteLength(body)
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          reject(new Error(`API error ${res.statusCode}: ${data}`));
          return;
        }
        try {
          const json = JSON.parse(data);
          const text = json.content?.[0]?.text || '';
          resolve(text);
        } catch (e) {
          reject(new Error(`Failed to parse response: ${e.message}`));
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// =============================================================================
// TAG GENERATION
// =============================================================================

async function generateTagsForChapter(apiKey, context, validTags) {
  const { libraryType, library, shelf, book, chapter, topics } = context;

  // Build a focused prompt
  const broadList = Array.from(validTags.broad).join(', ');
  const mediumSample = Array.from(validTags.medium).slice(0, 40).join(', ');
  const specificSample = Array.from(validTags.specific).slice(0, 60).join(', ');

  const prompt = `You are a taxonomy expert. Assign exactly 4 tags to this chapter for cross-library discovery.

CHAPTER CONTEXT:
- Library Type: ${libraryType}
- Library: ${library}
- Shelf: ${shelf}
- Book: ${book}
- Chapter: ${chapter}
- Sample topics: ${topics.slice(0, 3).join('; ')}

TAG TIERS:
1. BROAD (pick 1): ${broadList}
2. MEDIUM (pick 1-2): ${mediumSample}...
3. SPECIFIC (pick 1-2): ${specificSample}...

RULES:
- Return exactly 4 tags as a JSON array
- Tags must be kebab-case from the lists above
- Tag 1 should be broad, Tags 2-3 medium/specific, Tag 4 most specific
- Consider the full context to avoid false matches (e.g., "light" in art ≠ optics)

Return ONLY a JSON array like: ["science", "methodology", "discovery", "physics"]`;

  try {
    const response = await callClaude(apiKey, prompt);

    // Extract JSON array from response
    const match = response.match(/\[[\s\S]*?\]/);
    if (!match) {
      console.error(`  Parse error for "${chapter}": ${response.substring(0, 80)}`);
      return null;
    }

    let tags = JSON.parse(match[0]);

    // Normalize tags
    tags = tags.map(tag =>
      tag.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
    );

    // Filter to only valid tags
    const validatedTags = tags.filter(tag => validTags.all.has(tag));

    // Ensure exactly 4 tags with fallbacks
    const fallbacks = {
      'knowledge-libraries': ['education', 'foundations', 'theory', 'analysis'],
      'perspectives-libraries': ['philosophy', 'critical-thinking', 'analysis', 'epistemology'],
      'practical-libraries': ['application', 'technique', 'methodology', 'craft'],
      'event-libraries': ['history', 'conflict', 'narrative', 'legacy'],
      'geography-libraries': ['geography', 'identity', 'cultural-heritage', 'society'],
      'candidate-libraries': ['politics', 'democracy', 'elections', 'us-politics'],
      'infrastructure-libraries': ['technology', 'infrastructure', 'engineering', 'systems-thinking']
    };

    const fb = fallbacks[libraryType] || ['education', 'analysis', 'theory', 'application'];

    while (validatedTags.length < 4) {
      for (const f of fb) {
        if (!validatedTags.includes(f) && validTags.all.has(f)) {
          validatedTags.push(f);
          break;
        }
      }
      if (validatedTags.length < 4) {
        validatedTags.push('interdisciplinary');
        break;
      }
    }

    return validatedTags.slice(0, 4);

  } catch (e) {
    console.error(`  Error for "${chapter}": ${e.message}`);
    return null;
  }
}

// =============================================================================
// PROCESS BOOK FILE
// =============================================================================

async function processBook(bookPath, apiKey, validTags, dryRun = false) {
  console.log(`\nProcessing: ${path.basename(bookPath)}`);

  // Extract context from path
  const parts = bookPath.split(path.sep);
  const unlimitedIdx = parts.findIndex(p => p === 'unlimited');
  if (unlimitedIdx === -1) {
    console.error('  Could not determine library context from path');
    return { tagged: 0, failed: 0 };
  }

  const libraryType = parts[unlimitedIdx + 1] || 'knowledge-libraries';
  const library = parts[unlimitedIdx + 2] || 'unknown';
  const shelf = parts[unlimitedIdx + 3] || 'unknown';

  // Load book
  const data = JSON.parse(fs.readFileSync(bookPath, 'utf8'));
  if (!data.chapters) {
    console.error('  No chapters found');
    return { tagged: 0, failed: 0 };
  }

  const bookName = data.name || path.basename(bookPath, '.json');
  console.log(`  ${libraryType} → ${library} → ${shelf}`);
  console.log(`  Book: ${bookName} (${data.chapters.length} chapters)`);

  let tagged = 0;
  let failed = 0;

  for (let i = 0; i < data.chapters.length; i++) {
    const chapter = data.chapters[i];
    const chapterName = chapter.name || `Chapter ${i + 1}`;
    const topics = chapter.topics || [];

    process.stdout.write(`  [${i + 1}/${data.chapters.length}] ${chapterName.substring(0, 35).padEnd(35)}  `);

    const tags = await generateTagsForChapter(apiKey, {
      libraryType,
      library,
      shelf,
      book: bookName,
      chapter: chapterName,
      topics
    }, validTags);

    if (tags) {
      if (!dryRun) {
        chapter.tags = tags;
      }
      console.log(`✓ ${tags.join(', ')}`);
      tagged++;
    } else {
      console.log('✗ FAILED');
      failed++;
    }

    // Rate limiting delay
    if (i < data.chapters.length - 1) {
      await new Promise(resolve => setTimeout(resolve, DELAY_MS));
    }
  }

  // Save if not dry run
  if (!dryRun && tagged > 0) {
    fs.writeFileSync(bookPath, JSON.stringify(data, null, 2), 'utf8');
    console.log(`  ✓ Saved ${tagged} chapters`);
  } else if (dryRun) {
    console.log(`  (dry run - ${tagged} would be tagged)`);
  }

  return { tagged, failed };
}

// =============================================================================
// FIND ALL BOOKS
// =============================================================================

function findAllBooks(baseDir) {
  const books = [];
  const libraryTypes = [
    'knowledge-libraries',
    'perspectives-libraries',
    'practical-libraries',
    'event-libraries',
    'geography-libraries',
    'candidate-libraries',
    'infrastructure-libraries'
  ];

  for (const libType of libraryTypes) {
    const libDir = path.join(baseDir, libType);
    if (!fs.existsSync(libDir)) continue;

    const walk = (dir) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory() && !entry.name.startsWith('_')) {
          walk(fullPath);
        } else if (entry.isFile() && entry.name.endsWith('.json') && !entry.name.startsWith('_')) {
          books.push(fullPath);
        }
      }
    };

    walk(libDir);
  }

  return books;
}

// =============================================================================
// MAIN
// =============================================================================

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const testMode = args.includes('--test');
  const allMode = args.includes('--all');
  const files = args.filter(a => !a.startsWith('--'));

  console.log('TruthAngel LLM Auto-Tagger (Claude Haiku)');
  console.log('='.repeat(50));

  // Load API key
  let apiKey;
  try {
    apiKey = loadApiKey();
    console.log('API Key: Loaded ✓');
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }

  // Load tag vocabulary
  let validTags;
  try {
    const { validTags: vt } = loadTagVocabulary();
    validTags = vt;
    console.log(`Tags: ${validTags.all.size} valid tags loaded`);
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }

  console.log(`Rate: ${REQUESTS_PER_MINUTE}/min (${DELAY_MS}ms delay)`);
  if (dryRun) console.log('Mode: DRY RUN');

  // Determine books to process
  let booksToProcess = [];

  if (testMode) {
    const baseDir = path.join(SCRIPT_DIR, '..');
    const allBooks = findAllBooks(baseDir);
    if (allBooks.length > 0) {
      booksToProcess = [allBooks[0]];
      console.log('\nTest mode: 1 book');
    }
  } else if (allMode) {
    const baseDir = path.join(SCRIPT_DIR, '..');
    booksToProcess = findAllBooks(baseDir);
    const totalChapters = booksToProcess.reduce((sum, bp) => {
      try {
        const d = JSON.parse(fs.readFileSync(bp, 'utf8'));
        return sum + (d.chapters?.length || 0);
      } catch { return sum; }
    }, 0);
    console.log(`\nFound ${booksToProcess.length} books, ~${totalChapters} chapters`);
    console.log(`Estimated time: ~${Math.ceil(totalChapters * DELAY_MS / 60000)} minutes`);
    console.log(`Estimated cost: ~$${(totalChapters * 0.0005).toFixed(2)}`);
    console.log('\nStarting in 5 seconds... (Ctrl+C to cancel)');
    await new Promise(resolve => setTimeout(resolve, 5000));
  } else if (files.length > 0) {
    booksToProcess = files.map(f => path.resolve(f));
  } else {
    console.log('\nUsage:');
    console.log('  node llm-auto-tagger.js <book.json>           # Tag one book');
    console.log('  node llm-auto-tagger.js --dry-run <book.json> # Preview');
    console.log('  node llm-auto-tagger.js --all                 # Tag all');
    console.log('  node llm-auto-tagger.js --test                # Test one');
    process.exit(0);
  }

  // Process books
  let totalTagged = 0;
  let totalFailed = 0;
  const startTime = Date.now();

  for (const bookPath of booksToProcess) {
    if (!fs.existsSync(bookPath)) {
      console.error(`Not found: ${bookPath}`);
      continue;
    }

    const { tagged, failed } = await processBook(bookPath, apiKey, validTags, dryRun);
    totalTagged += tagged;
    totalFailed += failed;
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log('\n' + '='.repeat(50));
  console.log(`Done! ${totalTagged} tagged, ${totalFailed} failed (${elapsed}s)`);
}

main().catch(console.error);
