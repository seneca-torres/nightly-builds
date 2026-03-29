# Broadcaster Notes Web UI

A simple web application for the Broadcaster Notes Intelligence System. This local web app helps Victor's broadcaster friend manage years of coaching notes that are currently scattered across Google Docs.

## Features

1. **Text Input & File Uploads**: Paste notes directly or upload `.txt` files
2. **Entity Extraction**: Identifies coach names, school names, dates, and roles using static lists (no ML dependencies)
3. **Clean UI Display**: Shows extracted entities with color coding for easy visualization
4. **Search Functionality**: Search across multiple uploaded/saved notes
5. **Obsidian Export**: Generate and download Obsidian-ready markdown with YAML frontmatter and backlinks
6. **Self-contained**: HTML/CSS/JS frontend + Python backend with zero external dependencies
7. **Demo Data**: Includes sample broadcaster notes for demonstration

## How to Run

1. Start the server:
   ```bash
   python3 app.py
   ```

2. Open your browser to: `http://localhost:8080`

3. Use the interface to:
   - Paste notes or upload `.txt` files
   - View extracted entities
   - Search across notes
   - Download Obsidian-ready markdown

## Architecture

- **Backend**: Python Flask server (`app.py`)
- **Frontend**: HTML/CSS/JS with vanilla JavaScript
- **Entity Extraction**: Static lists of coaches, schools, etc. in `entities.py`
- **Data Storage**: In-memory storage for demo purposes

## Testing

1. Run the verification script:
   ```bash
   python3 verify.py
   ```

2. Test with sample data included in `sample_notes/` directory

## Notes for Victor's Broadcaster Friend

This tool addresses the problem of unwieldy Google Docs by:
- Extracting key entities (coaches, schools, dates, roles) automatically
- Creating searchable, organized notes
- Generating Obsidian-compatible markdown for easy browsing and graph visualization
- Providing a simple web interface that doesn't require technical expertise