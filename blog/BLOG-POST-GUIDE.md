# Quarex Blog Post Guide

Reference for creating consistent blog posts. All posts display on a **dark theme** background.

---

## Post HTML Structure

Posts are pure HTML fragments (no `<html>`, `<head>`, `<body>`). They get loaded into the `post.html` template.

```html
<!-- NO <style> block needed - use built-in classes -->

<p>Opening paragraph - hook the reader. No heading first.</p>

<h2>First Major Section</h2>

<p>Content paragraphs...</p>

<div class="callout">
  <p>Key point or call-to-action</p>
</div>

<h2>Second Major Section</h2>

<p>More content...</p>

<div class="callout green">
  <p><strong>Summary:</strong> Final takeaway for the reader.</p>
</div>
```

---

## Built-in CSS Classes

These classes are defined in `post.html` and available to all posts. **Do not redefine them.**

### Callout Boxes

```html
<div class="callout">Purple accent - default, announcements</div>
<div class="callout green">Green accent - success, positive</div>
<div class="callout gold">Gold accent - warnings, important</div>
<div class="callout blue">Blue accent - info, tips</div>
```

### Cards (for featured content)

```html
<div class="card">
  <h4>Card Title</h4>
  <p>Card description text.</p>
  <a href="...">Link text →</a>
</div>
```

### Card Grids

```html
<div class="card-grid">
  <div class="card">...</div>
  <div class="card">...</div>
</div>
```

### Pill Links (tag-style links)

```html
<div class="pill-links">
  <a href="...">Link 1</a>
  <a href="...">Link 2</a>
</div>
```

### Section Boxes (colored backgrounds)

```html
<div class="section-box">Neutral gray background</div>
<div class="section-box gold">Gold/warm background</div>
```

---

## Color Reference

The blog uses a dark theme. These colors are pre-defined:

| Purpose | Color | Use |
|---------|-------|-----|
| Background | `#0a0f1a` | Page background (don't override) |
| Text | `#e6eefc` | Default body text |
| Muted | `#8a9bb8` | Secondary text |
| Brand | `#7aa7ff` | Links, accents |
| Purple | `#6b46c1` | Callout accent |
| Green | `#38a169` | Success accent |
| Gold | `#d69e2e` | Warning accent |
| Blue | `#3182ce` | Info accent |

**Rule:** Light-background elements (cards, callouts) have dark text built-in. Don't override.

---

## Structure Rules

### Required Elements

1. **Opening paragraph** - Start with `<p>`, not a heading
2. **At least one `<h2>`** - Major sections
3. **Closing call-to-action** - End with a `.callout` linking somewhere

### Heading Hierarchy

- `<h2>` - Major sections (rendered large, with margin)
- `<h3>` - Subsections within an `<h2>`
- Never use `<h1>` (the post title is already h1)

### Links

- External links: Use full URLs (`https://...`)
- Internal Quarex links: Use absolute paths (`/libraries/...`)
- Always include link text that makes sense out of context

---

## blog-index.json Entry

Every post needs an entry in `blog/blog-index.json`:

```json
{
  "slug": "my-post-slug",
  "title": "Full Post Title",
  "date": "2026-02-18",
  "excerpt": "One or two sentences summarizing the post for the index page.",
  "tags": ["tag1", "tag2"],
  "quarexLinks": [
    {
      "title": "Related Quarex Content",
      "url": "/libraries/..."
    }
  ]
}
```

### Required Fields
- `slug` - URL-safe identifier, matches filename
- `title` - Full title shown on post
- `date` - ISO date (YYYY-MM-DD)
- `excerpt` - Summary for index page

### Optional Fields
- `tags` - Array of tag strings
- `quarexLinks` - Related Quarex content (shows in callout at end)

---

## File Naming

- Use kebab-case: `claude-ai-and-hispanic-studies.html`
- Match the `slug` in blog-index.json
- Save to `blog/posts/`

---

## Quality Checklist

Before publishing:

- [ ] Opens with `<p>`, not a heading
- [ ] Uses only built-in CSS classes (no custom `<style>`)
- [ ] All links have descriptive text
- [ ] Ends with a call-to-action callout
- [ ] Entry added to `blog-index.json`
- [ ] Slug matches filename
- [ ] Date is correct
- [ ] Excerpt is compelling

---

## Example Post

```html
<p>Big news this week: we've upgraded our AI and expanded our Hispanic Studies offerings.</p>

<h2>New AI: Claude Sonnet 4.5</h2>

<div class="callout">
  <p><strong>Try it now:</strong> Visit any <a href="/libraries/">Library</a> and ask a question.</p>
</div>

<p>We switched from Gemini to Claude. The difference is immediate: sharper reasoning, less hedging.</p>

<div class="callout green">
  <p>Claude states claims directly instead of adding "some might argue" qualifiers.</p>
</div>

<h2>Hispanic Studies Expansion</h2>

<p>Six new curricula now available:</p>

<div class="card-grid">
  <div class="card">
    <h4>Hispanic Cultures</h4>
    <p>Identity, communities, and traditions.</p>
    <a href="/libraries/pe/cultural-and-identity/hispanic-cultures/">Explore →</a>
  </div>
  <div class="card">
    <h4>Estudios Latinos</h4>
    <p>En español para la comunidad latina.</p>
    <a href="https://publicstudies.org/EstudiosLatinosSyllabus.html">Ver currículo →</a>
  </div>
</div>

<div class="callout">
  <p><strong>Explore:</strong> <a href="/libraries/">Libraries</a> · <a href="https://publicstudies.org">Public Studies</a></p>
</div>
```
