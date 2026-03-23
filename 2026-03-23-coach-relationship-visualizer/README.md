# Coach-School Relationship Visualizer

A web-based tool that visualizes connections between coaches, schools, and dates extracted from broadcaster notes.

## What it Does

This tool helps broadcasters and analysts discover hidden connections across hundreds of notes by:
1. **Parsing entity-extracted notes** from broadcaster tools (coaches, schools, dates)
2. **Building a relationship graph** showing how coaches move between schools over time
3. **Providing an interactive visualization** with filtering and search capabilities

## Architecture

- `parser.py`: CLI that extracts relationships from broadcaster notes
- `visualizer/`: Web interface with D3.js graph visualization
- `demo_data.py`: Sample data for testing
- `verify.py`: Verification script to test the tool

## Files Created

- `parser.py` - Python CLI for parsing notes and generating graph data
- `visualizer/index.html` - Main visualization interface
- `visualizer/style.css` - Styling for the visualization
- `visualizer/app.js` - Interactive D3.js visualization code
- `demo_data.py` - Sample coach-school relationships
- `verify.py` - Verification script
- `requirements.txt` - Python dependencies

## How to Test

### Quick Test (Demo Mode)
```bash
# 1. Run the parser with demo data
python3 parser.py --demo

# 2. Start the web server
python3 -m http.server 8000

# 3. Open browser to http://localhost:8000/visualizer/
```

### With Real Data
```bash
# Assuming you have broadcaster notes in markdown format
python3 parser.py --input ~/path/to/notes/*.md --output data/graph.json

# Then open the visualizer
```

### Verification
```bash
# Run the verification script
python3 verify.py
```

## Features

### Graph Visualization
- **Nodes**: Coaches (blue) and schools (orange)
- **Edges**: Relationships (coach worked at school)
- **Node sizing**: Based on frequency in notes
- **Interactive**: Hover for details, click to highlight connections
- **Force-directed layout**: Automatically arranges for clarity

### Filtering
- **Date range slider**: Filter relationships by year
- **Search box**: Find specific coaches or schools
- **Type toggle**: Show/hide coach or school nodes

### Data Export
- Export filtered graph as JSON
- Export visible subset as CSV
- Copy node/edge details to clipboard

## Integration with Existing Tools

This tool complements the existing Broadcaster Notes CLI and Entity Extractor by:
1. Using their output (markdown with YAML frontmatter and backlinks)
2. Adding visualization layer to see patterns
3. Enabling discovery of coaching career trajectories

## Example Use Cases

1. **Career path analysis**: See which coaches moved between which schools
2. **Conference connections**: Identify coaches who worked in multiple conferences
3. **Timeline view**: Track coaching movements over specific years
4. **Network density**: Find schools with many coaching connections

## Future Enhancements

1. **Google Docs integration**: Direct import from Google Docs
2. **RAG search**: Natural language queries over the graph
3. **Time-lapse animation**: Watch coaching movements over time
4. **Export to Obsidian**: Generate backlinks and network maps