# Quarex Project Rules

## Working Directory
- **Canonical path**: `E:\projects\websites\Quarex`
- **Never use**: `E:\www\Quarex` (should not exist)

## Processing Seed Files
When processing a Quarex book seed, follow `libraries/Seed Quarex/Seed Workflow.txt`:

1. Read and validate the seed JSON
2. Replace tags with vocabulary-compliant tags from `libraries/_utils/tag-vocabulary.json`
   - Each chapter gets exactly 4 tags: Broad → Medium → Specific → Specific
3. Place book in the shelf specified by `_placement` field
4. Update the shelf's `_manifest.json` with book metadata
5. Update the library's `_manifest.json` bookCount if new shelf
6. Rebuild discovery index: `node "libraries/_utils/build-discovery-index-v2.js"`
7. List files to upload to server

## File Structure
- Libraries: `libraries/[library-type]/[library]/[shelf]/[book].json`
- Manifests: `_manifest.json` at library and shelf levels
- Tag vocabulary: `libraries/_utils/tag-vocabulary.json`
- Discovery index: `libraries/discovery-index.json`

## JSON Formatting
- Use 2-space indentation
- Preserve existing formatting conventions in manifest files

## Deployment
- **Server**: quarex.org (hosted externally)
- **Local development**: Laragon pointing to `E:\projects\websites\Quarex`
- **CRITICAL**: Always sync local changes TO server, never the other way
- After making changes locally, upload modified files to server via FTP/hosting panel
- The local repo is the source of truth - server should mirror it

## Deprecated Folders (DO NOT USE)
- `E:\www\Quarex` - deleted
- `E:\old-www\Quarex` - archived, do not use
