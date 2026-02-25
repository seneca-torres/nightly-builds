# Portfolio Tag Filter Enhancement

## Objective
Add an interactive tag filtering system to the portfolio site (located at `~/clawd/portfolio`) that allows visitors to filter projects by tags (e.g., "Player Analytics", "Football Analytics", "Automation").

## Changes Made
1. **HTML**: Added a filter bar above the projects grid with buttons for each unique tag, plus an "All" button.
2. **CSS**: Added styles for filter buttons (active/inactive states) and transitions for project card filtering.
3. **JavaScript**: Added logic to handle tag selection, filter projects, and update UI accordingly.

## How to Integrate
Copy the modified files (`index.html`, `styles.css`, `script.js`) from this directory's `portfolio/` folder to your live portfolio directory (`~/clawd/portfolio`). Backup existing files first.

## Testing
Open `index.html` in a browser, click on any tag button — only projects with that tag will be shown. Click "All" to reset.

## Implementation Details
- Vanilla JavaScript, no external dependencies.
- Uses `data-tags` attribute on each project card to store tags.
- Smooth fade‑out/fade‑in animations via CSS transitions.
- Accessible keyboard navigation and ARIA labels.

## Screenshot
*(Optional)*

## Notes
The filter bar is responsive and matches the existing design language. It respects the user's reduced‑motion preference.