# Quarex Style Guide

Reference for matching graphics and design elements to the Quarex website.

## Color Palette (CSS Variables)

```css
:root {
  --bg: #0A0A0A;        /* Dark background */
  --ink: #F7F7F7;       /* Light text */
  --muted: #B7BCC2;     /* Muted/secondary text */
  --line: #262626;      /* Border/divider color */
  --card: #111111;      /* Card background */
  --accent: #7CB9FF;    /* Accent blue (light) */
  --brand: #EDEDED;     /* Brand/heading color */
  --blue: #3B82F6;      /* Link blue */
}
```

## Typography

| Usage | Font Family | Weight |
|-------|-------------|--------|
| Headings | Playfair Display (serif) | 700 |
| Body text | Inter (sans-serif) | 400 |
| Emphasis | Inter (sans-serif) | 600, 700 |

- **Base font size**: 16px
- **Line height**: 1.6
- **Font smoothing**: `-webkit-font-smoothing: antialiased`

### Google Fonts Import
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
```

## Gradient Patterns

### Primary (Featured Buttons)
```css
background: linear-gradient(135deg, #1e3a8a, #1e40af);
box-shadow: 0 8px 28px rgba(30, 58, 138, 0.5);
```

### Secondary (Cards/Buttons)
```css
background: linear-gradient(135deg, #0f172a, #1e293b);
box-shadow: 0 6px 20px rgba(15, 23, 42, 0.5);
```

### Creator Tools (Bright Blue)
```css
background: linear-gradient(135deg, #2563eb, #3b82f6);
box-shadow: 0 8px 28px rgba(37, 99, 235, 0.4);
```

## Border & Radius

| Element | Border Radius |
|---------|---------------|
| Cards, buttons | 16px |
| Pill buttons | 999px |
| Input fields | 8px |
| Logo icons | 50% (circular) |

### Border Colors
- Card borders: `2px solid rgba(255, 255, 255, 0.1)` or `rgba(255, 255, 255, 0.15)`
- Logo icon borders: `2px solid rgba(255, 255, 255, 0.5)`
- Footer divider: `1px solid var(--line)` (#262626)

## Background

- **Hero image**: `assets/living-book-iceberg.png`
- **Overlay**: `rgba(0, 0, 0, 0.3)` (30% dark overlay)
- **Text shadow** (on overlay): `1px 1px 4px rgba(0, 0, 0, 0.7)` or `2px 2px 8px rgba(0, 0, 0, 0.7)` for headings

## Button Styles

### Light Button (on dark background)
```css
.btn-light {
  padding: 12px 20px;
  border-radius: 999px;
  background: #ffffff;
  color: #111;
  font-weight: 700;
  letter-spacing: 0.02em;
}
```

### Featured Button
```css
.featured-btn {
  padding: 24px 40px;
  border-radius: 16px;
  font-family: "Playfair Display", serif;
  font-weight: 700;
  font-size: clamp(28px, 3.5vw, 42px);
  letter-spacing: 0.1em;
  color: var(--accent); /* #7CB9FF */
}
```

## Hover States

- Transform: `translateY(-2px)`
- Brightness: `filter: brightness(1.1)` to `brightness(1.15)`
- Enhanced box-shadow (increase blur and opacity)

## Responsive Breakpoints

- **Tablet**: `max-width: 768px`
- **Mobile**: `max-width: 480px`

## Assets

- Logo (round): `assets/quarex-hero-round-500pixels.png`
- Hero image: `assets/quarex-hero.jpg`
- Background: `assets/living-book-iceberg.png`
