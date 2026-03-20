# Victor Portfolio Theme Toggle

This package contains a standalone dark/light mode toggle for Victor's portfolio.

## Files

- `demo.html`: Complete component demo (HTML + CSS + minimal JS).
- `verify.sh`: Script that validates theme toggle behavior.

## Quick Start

1. Open `demo.html` in a browser.
2. Click the toggle button to switch themes.
3. Refresh the page and confirm the selected theme is preserved.

## Integration

1. Copy the toggle markup:

```html
<button id="themeToggle" class="theme-toggle" type="button" aria-label="Toggle dark mode" aria-pressed="false">
  Switch to dark mode
</button>
<span id="themeStatus" aria-live="polite"></span>
```

2. Copy the CSS variable blocks and button styles from `demo.html`:
- `:root { ... }`
- `[data-theme="dark"] { ... }`
- `.theme-toggle { ... }`

3. Copy the script from `demo.html` and keep these IDs/attributes:
- Root theme attribute: `data-theme` on `<html>`
- Button ID: `themeToggle`
- Status ID: `themeStatus`
- localStorage key: `victor-portfolio-theme`

4. If your site already has global colors, map your existing tokens to the two theme variable sets.

## Verification

Run:

```bash
./verify.sh
```

The script checks:
- `localStorage` preference is read on startup.
- Theme toggles from light to dark on click.
- New preference is saved back to `localStorage`.
