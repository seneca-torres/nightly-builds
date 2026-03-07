# Portfolio Accessibility & UX Improvements

**Date:** 2026-03-07  
**Scope:** 30-minute nightly build  
**Goal:** Add accessibility and user experience enhancements to Victor's portfolio site.

## Changes Made

### 1. Skip‑to‑main‑content link
- **What:** A hidden “Skip to main content” link appears on keyboard focus, allowing screen‑reader and keyboard‑only users to bypass the navigation and jump directly to the main content.
- **Implementation:**
  - Added `<a href="#main" class="skip-link">Skip to main content</a>` right after the opening `<body>` tag.
  - Added `id="main"` to the `<main>` element.
  - Styled with CSS to be hidden off‑screen until focused, then slide into view with the site’s accent colors.

### 2. Back‑to‑top button
- **What:** A floating circular button that appears after scrolling 300px down, smoothly scrolls back to the top when clicked, and matches the site’s design language.
- **Implementation:**
  - Added `<button id="back-to-top" class="back-to-top" aria-label="Back to top">↑</button>` before the closing `</body>`.
  - CSS positions it fixed at the bottom‑right, with smooth opacity/visibility transitions and hover effects using the existing accent variables.
  - JavaScript adds/removes the `.visible` class based on scroll position and handles the smooth scroll on click.

### 3. Print‑style cleanup
- **What:** Ensures the new elements are hidden when printing, keeping the printed output clean.
- **Implementation:** Extended the existing `@media print` rule to also hide `.skip‑link` and `.back‑to‑top`.

## Files Modified
All changes are contained within the portfolio site’s three core files:

- `index.html` – added skip link, `id="main"`, back‑to‑top button
- `styles.css` – added `.skip‑link` and `.back‑to‑top` styles, updated print rule
- `script.js` – added scroll‑based visibility toggle and click handler for the back‑to‑top button

## How to Test

1. **Skip link:**
   - Open the portfolio page (`index.html`) in a browser.
   - Press the `Tab` key immediately after the page loads — the “Skip to main content” link should appear in the top‑left corner.
   - Press `Enter` to jump to the main content (the page should scroll to the `<main>` section).

2. **Back‑to‑top button:**
   - Scroll down at least 300px — a cyan circular button with an up‑arrow should fade in at the bottom‑right.
   - Hover over the button; it should lift slightly and change to a brighter cyan.
   - Click the button; the page should smoothly scroll back to the top, and the button should fade out.

3. **Print preview:**
   - Open the browser’s print dialog (⌘P / Ctrl+P).
   - The skip link and back‑to‑top button should not appear in the print preview.

4. **Mobile/responsive:**
   - The new elements respect the existing responsive breakpoints and should work correctly on all screen sizes.

## Design Decisions
- **Colors & spacing:** Leveraged the existing CSS custom properties (`--color‑accent`, `--color‑bg`, etc.) to keep the new elements visually consistent with the rest of the site.
- **Accessibility first:** The skip link follows WCAG best practices (hidden until focused, clear focus indicator). The back‑to‑top button includes an `aria‑label` for screen readers.
- **Performance:** The JavaScript is lightweight and uses passive scroll listeners where possible. No extra dependencies added.

## Notes
- The portfolio site already had excellent accessibility foundations (semantic HTML, ARIA labels, proper focus management). These additions further improve the experience for keyboard and screen‑reader users.
- The back‑to‑top button is a small quality‑of‑life improvement for longer pages; it’s especially useful on mobile where scrolling back up can be tedious.

## Future Ideas (if time allowed)
- Add a “prefers‑reduced‑motion” check for the smooth‑scroll behavior.
- Make the back‑to‑top button’s threshold configurable via a data‑attribute.
- Add a subtle tooltip on hover for the back‑to‑top button (e.g., “Back to top”).

---

**Built as part of the Nightly “Surprise Me” Build series.**  
See [NIGHTLY‑BUILDS.md](../../NIGHTLY-BUILDS.md) for the full backlog and completed builds.