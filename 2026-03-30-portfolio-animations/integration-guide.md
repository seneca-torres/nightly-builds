# Portfolio Animations Integration Guide

This guide explains how to integrate the animation enhancements into your existing portfolio site.

## Prerequisites

- Your portfolio is located at `~/clawd/portfolio/`
- You have basic familiarity with HTML, CSS, and JavaScript

## Step 1: Copy Files

Copy the animation enhancement files to your portfolio directory:

```bash
cd ~/clawd/nightly-builds/2026-03-30-portfolio-animations
cp -r animation-enhancement/ ~/clawd/portfolio/
```

Or copy manually:
- `animations.css`
- `animations.js`
- `demo.html` (optional, for testing)
- `verify.sh`

## Step 2: Update HTML

Add the CSS and JS links to your `index.html`:

In the `<head>` section, add after your existing styles.css link:
```html
<link rel="stylesheet" href="animation-enhancement/animations.css">
```

Before the closing `</body>` tag, add after your existing script.js:
```html
<script src="animation-enhancement/animations.js" defer></script>
```

## Step 3: Update Project Card HTML

Modify your project card generation in `script.js` to include animation classes.

Find where project cards are created (likely in a function that renders projects from `projects.json`).

### Option A: Add flip card wrapper (recommended)

Wrap each project card in a flip card structure:
```javascript
// Before: <div class="project-card">...</div>
// After:
const cardHTML = `
  <div class="flip-card project-card">
    <div class="flip-card-inner">
      <div class="flip-card-front">
        <!-- Front content (title, tags, image) -->
        <h3>${project.title}</h3>
        <img src="${project.images[0]}" alt="${project.title}">
        <button class="chalk-btn flip-btn">View Details</button>
      </div>
      <div class="flip-card-back">
        <!-- Back content (full description) -->
        <p>${project.longDescription}</p>
        <button class="chalk-btn close-btn">Back to Front</button>
      </div>
    </div>
  </div>
`;
```

### Option B: Add animation classes only

If you don't want flip cards, just add animation classes:
```javascript
// Add these classes to your existing project card div
const cardHTML = `
  <div class="project-card fade-in-up stagger-item">
    <!-- Existing content -->
  </div>
`;
```

## Step 4: Enhance Demo Images/GIFs

For project images that are GIFs or videos, add demo player controls:

```javascript
// Replace simple img tag with demo player
const imageHTML = `
  <div class="demo-player">
    <img src="${project.thumbnail}" 
         data-gif="${project.animatedGif}" 
         alt="${project.title} demo">
    <div class="demo-controls">
      <button class="chalk-btn play-btn">▶ Play</button>
      <button class="chalk-btn pause-btn">⏸ Pause</button>
      <div class="progress-bar">
        <div class="progress"></div>
      </div>
    </div>
  </div>
`;
```

## Step 5: Add Animation Classes to Sections

Add `fade-in-up` class to sections you want to animate on scroll:

```html
<section class="about fade-in-up">
  <!-- About content -->
</section>

<section class="projects fade-in-up">
  <div class="projects-grid">
    <!-- Project cards will be staggered -->
  </div>
</section>
```

For staggered animations in lists, add `stagger-item` to each item:
```html
<div class="skills-list">
  <div class="skill-item stagger-item">Skill 1</div>
  <div class="skill-item stagger-item">Skill 2</div>
  <div class="skill-item stagger-item">Skill 3</div>
</div>
```

## Step 6: Add Chalkboard Effects

Add `chalk-writing` class to headings for the chalk writing effect:
```html
<h1 class="chalk-writing">VT Sports Solutions</h1>
<h2 class="chalk-writing">Bespoke Analytics for Football</h2>
```

## Step 7: Test Integration

Run the verification script:
```bash
cd ~/clawd/portfolio/animation-enhancement
./verify.sh
```

Then open your portfolio in a browser and test:
1. Scroll to see fade-in animations
2. Hover over project cards
3. Click "View Details" to flip cards
4. Hover over demo images to see controls
5. Click play/pause on GIFs/videos

## Step 8: Customization

### Adjust Animation Speed
In `animations.css`, modify these variables:
```css
/* Slower animations */
.flip-card-inner {
  transition: transform 1s; /* Was 0.6s */
}

/* Faster fade-in */
.fade-in-up {
  transition: opacity 0.3s ease, transform 0.3s ease; /* Was 0.6s */
}
```

### Change Colors
The animations use CSS custom properties from your existing theme:
```css
.chalk-btn {
  border-color: var(--color-accent, #3b82f6); /* Uses your accent color */
}
```

### Disable Specific Animations
Remove classes from elements or comment out sections in `animations.js`:
```javascript
// Comment out to disable flip cards
// this.initFlipCards();
```

## Troubleshooting

### Animations Not Working
1. Check browser console for errors
2. Verify files are loaded (Network tab)
3. Ensure CSS classes are correctly applied

### Flip Cards Not Flipping
1. Check that `.flip-card`, `.flip-card-inner`, `.flip-card-front`, `.flip-card-back` classes are present
2. Verify `perspective` CSS property is set
3. Check that `backface-visibility: hidden` is set

### Demo Player Controls Not Showing
1. Ensure `.demo-player:hover .demo-controls` opacity transition works
2. Check that play/pause buttons have correct event listeners
3. For GIFs, verify `data-gif` attribute points to animated version

### Performance Issues
1. Reduce number of animated elements
2. Use `will-change` property sparingly
3. Consider disabling animations on mobile if needed

## Browser Support

The animations use modern CSS and JavaScript features:
- CSS Transforms, Transitions, Animations
- Intersection Observer API
- CSS Custom Properties

Polyfills are not included. For older browsers, animations will gracefully degrade.

## Removing Animations

To remove the animations:
1. Remove the CSS and JS links from `index.html`
2. Remove animation classes from your HTML
3. Delete the `animation-enhancement/` directory

## Support

For issues or questions, check the nightly builds repository or contact the maintainer.