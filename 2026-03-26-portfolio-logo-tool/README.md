# Portfolio Logo Tool

A simple tool to help preview and apply logos for the VT Sports Solutions portfolio site.

## Problem

The VT Sports Solutions portfolio site (`~/clawd/portfolio/`) has been "waiting on new logo" according to the half-baked ideas list. Multiple logo variations exist in:
- `~/clawd/portfolio/images/` (current portfolio logos)
- `~/clawd/vt-logos/` (additional logo variations)

This tool makes it easy to:
1. **Browse** all available logo files
2. **Preview** how they look on the actual portfolio site
3. **Apply** selected logos to the portfolio

## Features

- **CLI Interface**: Simple command-line interface with `list`, `preview`, and `apply` commands
- **Web Preview**: Interactive web interface to browse and preview logos
- **One-click Apply**: Copy logos to the portfolio images directory
- **Portfolio Integration**: Works with the existing portfolio structure

## Installation & Usage

### Quick Start

1. Navigate to the tool directory:
   ```bash
   cd ~/clawd/nightly-builds/2026-03-26-portfolio-logo-tool
   ```

2. List all available logos:
   ```bash
   python logo_tool.py list
   ```

3. Start the web preview (opens browser automatically):
   ```bash
   python logo_tool.py preview
   ```

4. Apply a logo to the portfolio:
   ```bash
   # By index from list
   python logo_tool.py apply 1
   
   # By file path
   python logo_tool.py apply ~/clawd/vt-logos/logo-color.png
   
   # With custom target name
   python logo_tool.py apply ~/clawd/vt-logos/logo-white.png --target nav-logo.png
   ```

### Web Interface

The web interface (`logo_preview.html`) provides:

- **Logo Gallery**: Grid view of all logos with preview images
- **Selection**: Click any logo to select it
- **Portfolio Preview**: See how logos look on the actual site (simulated)
- **Apply Function**: One-click copy to portfolio

## How It Works

1. **Scanning**: The tool scans `~/clawd/portfolio/images/` and `~/clawd/vt-logos/` for image files
2. **Preview**: Creates an HTML page showing all logos with preview images
3. **Application**: Copies selected logo files to the portfolio images directory
4. **Integration**: After applying, you need to update the portfolio HTML/CSS to reference the new logo

## Portfolio Integration Notes

After applying a logo:

1. **Check current logo usage** in the portfolio:
   - `~/clawd/portfolio/index.html` - Look for logo image references
   - `~/clawd/portfolio/styles.css` - Check `.nav-logo` and `.hero-logo` CSS classes
   - `~/clawd/portfolio/script.js` - Any JavaScript logo handling

2. **Update references** if needed:
   - The portfolio HTML uses CSS classes for logos, not direct `<img>` tags
   - Update CSS background-image properties in `styles.css` if changing logo names
   - Or rename the applied logo to match existing filenames

3. **Test locally**:
   ```bash
   open ~/clawd/portfolio/index.html
   ```

## File Structure

```
2026-03-26-portfolio-logo-tool/
├── logo_tool.py          # Main Python CLI tool
├── logo_preview.html     # Web interface template
├── README.md            # This file
└── preview_temp.html    # Generated preview (not in git)
```

## Design Decisions

1. **Simplicity over complexity**: Focused on the core problem (logo selection/preview)
2. **Non-destructive**: Doesn't modify portfolio HTML/CSS, only copies logo files
3. **Interactive**: Web interface for visual comparison
4. **CLI-first**: Can be used from terminal or scripts
5. **Portfolio-aware**: Understands the portfolio structure and constraints

## Next Steps / Future Improvements

1. **Actual portfolio preview**: Modify portfolio HTML on-the-fly for true preview
2. **Logo generation**: Integrate with existing logo generator tools
3. **Batch operations**: Apply multiple logos (light/dark variants)
4. **Auto-update CSS**: Automatically update portfolio CSS with new logo references
5. **Logo optimization**: Resize/optimize logos for web use
6. **Deployment helper**: Help deploy logo changes to live site

## Why This Tool?

The portfolio site has been "waiting on new logo" in the half-baked ideas. This tool:
- **Solves the immediate problem**: Makes it easy to choose/apply a logo
- **Leverages existing assets**: Uses logos that already exist in the codebase
- **Saves time**: Visual comparison beats manual file browsing
- **Educational**: Shows how the portfolio logo system works

## Testing

To test the tool:

1. Run list command to see available logos
2. Start preview server and browse logos
3. Apply a test logo (creates backup of original)
4. Check portfolio looks correct
5. Restore original if needed

## Troubleshooting

- **"No images found"**: Check that `~/clawd/portfolio/images/` and `~/clawd/vt-logos/` exist
- **Preview images not loading**: Some logos might be in formats not supported by browser
- **Apply fails**: Check file permissions and that destination directory exists
- **Portfolio not updating**: May need to clear browser cache or update CSS references

## Built With

- Python 3.x (standard library only)
- HTML/CSS/JavaScript for web interface
- Built in ~30 minutes for "Surprise Me" nightly build

---

*Built with 🦉 by Seneca for VT Sports Solutions • Nightly Build 2026-03-26*