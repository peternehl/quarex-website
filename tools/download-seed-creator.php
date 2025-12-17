<?php
/**
 * Quarex Seed Creator Download Generator
 *
 * Scans the library structure and generates a downloadable HTML file
 * that users can use offline to create Quarex book seeds.
 */

header('Content-Type: text/html');
header('Content-Disposition: attachment; filename="quarex-seed-creator.html"');

// Scan the library structure
function scanLibraryStructure($basePath) {
    $structure = [];

    // Find all library type folders (e.g., knowledge-libraries, practical-libraries)
    $libraryTypes = glob($basePath . '/*-libraries', GLOB_ONLYDIR);

    foreach ($libraryTypes as $libraryTypePath) {
        $libraryTypeSlug = basename($libraryTypePath);

        // Skip questions-libraries (system-generated, not for user creation)
        if ($libraryTypeSlug === 'questions-libraries') {
            continue;
        }

        $libraryTypeName = formatName($libraryTypeSlug);

        $libraryTypeData = [
            'slug' => $libraryTypeSlug,
            'name' => $libraryTypeName,
            'libraries' => []
        ];

        // Read the library type's manifest to get libraries
        $manifestPath = $libraryTypePath . '/_manifest.json';
        if (file_exists($manifestPath)) {
            $libraries = json_decode(file_get_contents($manifestPath), true);

            foreach ($libraries as $library) {
                $libraryPath = $libraryTypePath . '/' . $library['slug'];
                $libraryData = [
                    'slug' => $library['slug'],
                    'name' => $library['name'],
                    'shelves' => []
                ];

                // Read the library's manifest to get shelves
                $shelfManifestPath = $libraryPath . '/_manifest.json';
                if (file_exists($shelfManifestPath)) {
                    $shelves = json_decode(file_get_contents($shelfManifestPath), true);
                    foreach ($shelves as $shelf) {
                        $libraryData['shelves'][] = [
                            'slug' => $shelf['slug'],
                            'name' => $shelf['name']
                        ];
                    }
                }

                $libraryTypeData['libraries'][] = $libraryData;
            }
        }

        $structure[] = $libraryTypeData;
    }

    return $structure;
}

function formatName($slug) {
    // Convert slug to readable name (e.g., "knowledge-libraries" -> "Knowledge Libraries")
    return ucwords(str_replace('-', ' ', $slug));
}

// Get the library structure
$basePath = __DIR__ . '/../libraries';
$structure = scanLibraryStructure($basePath);
$structureJson = json_encode($structure, JSON_PRETTY_PRINT);

// Generate the HTML content
$downloadDate = date('Y-m-d');
$version = date('Ymd.His');

$htmlContent = <<<HTML
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quarex Seed Creator</title>
    <style>
        :root {
            --bg-primary: #0A0A0A;
            --bg-secondary: #1a1a1a;
            --bg-tertiary: #2a2a2a;
            --text-primary: #F7F7F7;
            --text-secondary: #a0a0a0;
            --accent-blue: #60a5fa;
            --accent-purple: #a78bfa;
            --success: #4ade80;
            --warning: #fbbf24;
            --error: #f87171;
            --border: #333;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem;
            line-height: 1.6;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 2rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
        }

        h1 {
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 2rem;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }

        .version-info {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .instructions {
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border);
        }

        .instructions h2 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            color: var(--accent-blue);
        }

        .instructions ul {
            margin-left: 1.5rem;
            color: var(--text-secondary);
        }

        .instructions li {
            margin-bottom: 0.5rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-primary);
        }

        select, input, textarea {
            width: 100%;
            padding: 0.75rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
            font-family: inherit;
        }

        select:focus, input:focus, textarea:focus {
            outline: none;
            border-color: var(--accent-blue);
        }

        select option {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        textarea {
            min-height: 150px;
            resize: vertical;
        }

        .seed-mode-group {
            display: flex;
            gap: 1rem;
            margin-top: 0.5rem;
        }

        .seed-mode-option {
            flex: 1;
            padding: 1rem;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .seed-mode-option:hover {
            border-color: var(--accent-blue);
        }

        .seed-mode-option.selected {
            border-color: var(--accent-purple);
            background: var(--bg-tertiary);
        }

        .seed-mode-option h3 {
            font-size: 1rem;
            margin-bottom: 0.25rem;
        }

        .seed-mode-option p {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .button-group {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }

        button {
            flex: 1;
            padding: 1rem;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            color: white;
        }

        .btn-primary:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }

        .btn-secondary:hover {
            background: var(--bg-secondary);
        }

        .output-section {
            margin-top: 2rem;
            display: none;
        }

        .output-section.visible {
            display: block;
        }

        .output-box {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 400px;
            overflow-y: auto;
        }

        .hash-section {
            margin-top: 2rem;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .hash-section h3 {
            font-size: 1rem;
            margin-bottom: 0.75rem;
        }

        .hash-result {
            padding: 0.75rem;
            border-radius: 6px;
            font-family: monospace;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }

        .hash-valid {
            background: rgba(74, 222, 128, 0.1);
            border: 1px solid var(--success);
            color: var(--success);
        }

        .hash-invalid {
            background: rgba(248, 113, 113, 0.1);
            border: 1px solid var(--error);
            color: var(--error);
        }

        .hash-offline {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid var(--warning);
            color: var(--warning);
        }

        .quarex-link {
            color: var(--accent-blue);
            text-decoration: none;
        }

        .quarex-link:hover {
            text-decoration: underline;
        }

        footer {
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Quarex Seed Creator</h1>
            <div class="version-info">
                Version: {$version} | Downloaded: {$downloadDate}
            </div>
        </header>

        <div class="instructions">
            <h2>Instructions</h2>
            <ul>
                <li>This tool creates a Quarex "seed" - a JSON structure that defines a new Living Book for the Quarex library.</li>
                <li>Select your quarex context location using the dropdowns below.</li>
                <li>Choose a seed mode: <strong>Bare Bones</strong> for manual completion, or <strong>LLM-Ready</strong> to pass to an AI for expansion.</li>
                <li><strong>Version Note:</strong> Download a fresh copy periodically to get the latest library structure.</li>
            </ul>
        </div>

        <form id="seedForm">
            <div class="form-group">
                <label for="libraryType">Library Type</label>
                <select id="libraryType" required>
                    <option value="">-- Select Library Type --</option>
                </select>
            </div>

            <div class="form-group">
                <label for="library">Library</label>
                <select id="library" required disabled>
                    <option value="">-- Select Library --</option>
                </select>
            </div>

            <div class="form-group">
                <label for="shelf">Shelf</label>
                <select id="shelf" required disabled>
                    <option value="">-- Select Shelf --</option>
                </select>
            </div>

            <div class="form-group" id="newShelfGroup" style="display: none;">
                <label for="newShelfName">New Shelf Name</label>
                <input type="text" id="newShelfName" placeholder="e.g., Home Autonomy, Classical Music">
                <small style="color: var(--text-secondary); display: block; margin-top: 0.25rem;">
                    Enter the display name for the new shelf (will be converted to a slug automatically)
                </small>
            </div>

            <div class="form-group">
                <label for="bookName">Book Name</label>
                <input type="text" id="bookName" placeholder="e.g., Introduction to Quantum Physics" required>
            </div>

            <div class="form-group">
                <label for="createdBy">Created By</label>
                <input type="text" id="createdBy" placeholder="e.g., Your Name, ChatGPT, Claude" required>
            </div>

            <div class="form-group">
                <label>Seed Mode</label>
                <div class="seed-mode-group">
                    <div class="seed-mode-option selected" data-mode="bare">
                        <h3>Bare Bones</h3>
                        <p>Minimal structure for manual completion</p>
                    </div>
                    <div class="seed-mode-option" data-mode="llm">
                        <h3>LLM-Ready</h3>
                        <p>Includes instructions for AI expansion</p>
                    </div>
                </div>
            </div>

            <div class="button-group">
                <button type="submit" class="btn-primary">Generate Seed</button>
                <button type="button" class="btn-secondary" onclick="window.open('https://quarex.org/tools/seed-instructions.html', '_blank')">View Seed Instructions</button>
            </div>
        </form>

        <div class="output-section" id="outputSection">
            <h2 style="margin-bottom: 1rem;">Generated Seed</h2>
            <div class="output-box" id="outputBox"></div>
            <div class="button-group">
                <button type="button" class="btn-primary" id="copyBtn">Copy to Clipboard</button>
                <button type="button" class="btn-secondary" id="downloadBtn">Download JSON</button>
            </div>
        </div>

        <footer>
            <p>
                Quarex Seed Creator by <a href="https://quarex.org" class="quarex-link">Quarex.org</a><br>
                For creation instructions, see: <a href="https://quarex.org/tools/seed-instructions.html" class="quarex-link">Seed Creation Guide</a>
            </p>
            <p style="margin-top: 0.5rem;">&copy; 2025 Quarex / Peter Nehl. All Rights Reserved.</p>
        </footer>
    </div>

    <script>
        // Library structure embedded at download time
        const libraryStructure = {$structureJson};

        // DOM Elements
        const libraryTypeSelect = document.getElementById('libraryType');
        const librarySelect = document.getElementById('library');
        const shelfSelect = document.getElementById('shelf');
        const seedModeOptions = document.querySelectorAll('.seed-mode-option');
        const form = document.getElementById('seedForm');
        const outputSection = document.getElementById('outputSection');
        const outputBox = document.getElementById('outputBox');

        let selectedMode = 'bare';

        // Populate library types
        libraryStructure.forEach(lt => {
            const option = document.createElement('option');
            option.value = lt.slug;
            option.textContent = lt.name;
            libraryTypeSelect.appendChild(option);
        });

        // Library type change handler
        libraryTypeSelect.addEventListener('change', function() {
            librarySelect.innerHTML = '<option value="">-- Select Library --</option>';
            shelfSelect.innerHTML = '<option value="">-- Select Shelf --</option>';
            librarySelect.disabled = true;
            shelfSelect.disabled = true;

            if (this.value) {
                const libraryType = libraryStructure.find(lt => lt.slug === this.value);
                if (libraryType && libraryType.libraries.length > 0) {
                    libraryType.libraries.forEach(lib => {
                        const option = document.createElement('option');
                        option.value = lib.slug;
                        option.textContent = lib.name;
                        librarySelect.appendChild(option);
                    });
                    librarySelect.disabled = false;
                }
            }
        });

        // Library change handler
        librarySelect.addEventListener('change', function() {
            shelfSelect.innerHTML = '<option value="">-- Select Shelf --</option>';
            shelfSelect.disabled = true;
            document.getElementById('newShelfGroup').style.display = 'none';
            document.getElementById('newShelfName').value = '';

            if (this.value) {
                const libraryType = libraryStructure.find(lt => lt.slug === libraryTypeSelect.value);
                const library = libraryType?.libraries.find(lib => lib.slug === this.value);

                // Always add the "Create New Shelf" option
                const newShelfOption = document.createElement('option');
                newShelfOption.value = '__new__';
                newShelfOption.textContent = '+ Create New Shelf';
                shelfSelect.appendChild(newShelfOption);

                if (library && library.shelves.length > 0) {
                    library.shelves.forEach(shelf => {
                        const option = document.createElement('option');
                        option.value = shelf.slug;
                        option.textContent = shelf.name;
                        shelfSelect.appendChild(option);
                    });
                }
                shelfSelect.disabled = false;
            }
        });

        // Shelf change handler - show new shelf input if needed
        shelfSelect.addEventListener('change', function() {
            const newShelfGroup = document.getElementById('newShelfGroup');
            const newShelfInput = document.getElementById('newShelfName');

            if (this.value === '__new__') {
                newShelfGroup.style.display = 'block';
                newShelfInput.required = true;
            } else {
                newShelfGroup.style.display = 'none';
                newShelfInput.required = false;
                newShelfInput.value = '';
            }
        });

        // Seed mode selection
        seedModeOptions.forEach(option => {
            option.addEventListener('click', function() {
                seedModeOptions.forEach(o => o.classList.remove('selected'));
                this.classList.add('selected');
                selectedMode = this.dataset.mode;
            });
        });

        // Helper function to convert name to slug
        function toSlug(name) {
            return name.toLowerCase()
                .replace(/[^a-z0-9]+/g, '-')
                .replace(/^-|-$/g, '');
        }

        // Form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const bookName = document.getElementById('bookName').value.trim();
            const createdBy = document.getElementById('createdBy').value.trim();

            // Determine shelf value - use new shelf if selected
            let shelfSlug, shelfName;
            if (shelfSelect.value === '__new__') {
                shelfName = document.getElementById('newShelfName').value.trim();
                shelfSlug = toSlug(shelfName);
            } else {
                shelfSlug = shelfSelect.value;
                shelfName = shelfSelect.options[shelfSelect.selectedIndex].text;
            }

            const seed = {
                name: bookName,
                created_by: createdBy,
                chapters: [
                    {
                        name: "Chapter 1",
                        topics: [
                            "Topic 1",
                            "Topic 2",
                            "Topic 3",
                            "Topic 4"
                        ],
                        tags: []
                    }
                ]
            };

            let output;
            const placement = {
                library_type: libraryTypeSelect.value,
                library: librarySelect.value,
                shelf: shelfSlug
            };

            // Add shelf_name if it's a new shelf
            if (shelfSelect.value === '__new__') {
                placement.shelf_name = shelfName;
                placement.new_shelf = true;
            }

            if (selectedMode === 'llm') {
                output = {
                    _instructions: "Please expand this Quarex book seed into a complete book. Create as many chapters as necessary to cover the subject matter thoroughly. \\nWithin chapter: Create 4-8 Topics in form of questions that users can click to explore.\\nEach Topic should be a clear, curiosity-sparking question",
                    _placement: placement,
                    seed: seed
                };
            } else {
                output = seed;
                output._placement = placement;
            }

            outputBox.textContent = JSON.stringify(output, null, 2);
            outputSection.classList.add('visible');
        });

        // Copy to clipboard
        document.getElementById('copyBtn').addEventListener('click', function() {
            navigator.clipboard.writeText(outputBox.textContent).then(() => {
                this.textContent = 'Copied!';
                setTimeout(() => this.textContent = 'Copy to Clipboard', 2000);
            });
        });

        // Download JSON
        document.getElementById('downloadBtn').addEventListener('click', function() {
            const bookName = document.getElementById('bookName').value.trim();
            const slug = bookName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
            const blob = new Blob([outputBox.textContent], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = slug + '-seed.json';
            a.click();
            URL.revokeObjectURL(url);
        });

    </script>
</body>
</html>
HTML;

echo $htmlContent;
?>
