#!/usr/bin/env python3
"""
Broadcaster Notes Web UI - Flask Server
A simple web app for managing coaching notes with entity extraction.
"""

import os
import re
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file
import markdown
from werkzeug.utils import secure_filename

# Import our entity extraction module
from entities import extract_entities

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# In-memory storage for notes (for demo purposes)
notes_store = []

def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_obsidian_markdown(content, entities, title="Untitled Note"):
    """Generate Obsidian-ready markdown with YAML frontmatter and backlinks."""
    # Create YAML frontmatter
    frontmatter = f"""---
title: "{title}"
date: "{datetime.now().strftime('%Y-%m-%d')}"
coaches: {json.dumps(list(entities['coaches']))}
schools: {json.dumps(list(entities['schools']))}
dates: {json.dumps(list(entities['dates']))}
roles: {json.dumps(list(entities['roles']))}
---

"""
    
    # Create backlinks section
    backlinks = "## 🔗 Connections\n\n"
    
    if entities['coaches']:
        backlinks += "### Coaches Mentioned\n"
        for coach in entities['coaches']:
            backlinks += f"- [[{coach}]]\n"
        backlinks += "\n"
    
    if entities['schools']:
        backlinks += "### Schools Mentioned\n"
        for school in entities['schools']:
            backlinks += f"- [[{school}]]\n"
        backlinks += "\n"
    
    # Add the original content
    content_section = f"## 📝 Original Notes\n\n{content}\n"
    
    return frontmatter + backlinks + content_section

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process_text():
    """Process text input and extract entities."""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Extract entities
    entities = extract_entities(text)
    
    # Store note in memory (for demo)
    note_id = len(notes_store)
    note = {
        'id': note_id,
        'text': text,
        'entities': entities,
        'timestamp': datetime.now().isoformat(),
        'title': f"Note {note_id + 1}"
    }
    notes_store.append(note)
    
    return jsonify({
        'success': True,
        'entities': entities,
        'note_id': note_id,
        'preview': generate_obsidian_markdown(text[:500] + "..." if len(text) > 500 else text, entities, f"Note {note_id + 1}")
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract entities
        entities = extract_entities(text)
        
        # Store note
        note_id = len(notes_store)
        note = {
            'id': note_id,
            'text': text,
            'entities': entities,
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'title': os.path.splitext(filename)[0]
        }
        notes_store.append(note)
        
        # Clean up uploaded file (optional)
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'entities': entities,
            'note_id': note_id,
            'preview': generate_obsidian_markdown(text[:500] + "..." if len(text) > 500 else text, entities, os.path.splitext(filename)[0])
        })
    
    return jsonify({'error': 'File type not allowed. Please upload .txt files only.'}), 400

@app.route('/api/search', methods=['POST'])
def search_notes():
    """Search across all stored notes."""
    data = request.json
    query = data.get('query', '').lower()
    
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    results = []
    
    for note in notes_store:
        # Search in text
        text_match = query in note['text'].lower()
        
        # Search in entities
        entity_match = False
        for entity_type in ['coaches', 'schools', 'roles']:
            for entity in note['entities'].get(entity_type, []):
                if query in entity.lower():
                    entity_match = True
                    break
            if entity_match:
                break
        
        if text_match or entity_match:
            # Create a snippet
            text_lower = note['text'].lower()
            query_pos = text_lower.find(query)
            
            if query_pos != -1:
                start = max(0, query_pos - 100)
                end = min(len(note['text']), query_pos + len(query) + 100)
                snippet = note['text'][start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(note['text']):
                    snippet = snippet + "..."
            else:
                snippet = note['text'][:200] + "..." if len(note['text']) > 200 else note['text']
            
            results.append({
                'id': note['id'],
                'title': note.get('title', f"Note {note['id'] + 1}"),
                'snippet': snippet,
                'entities': note['entities'],
                'match_type': 'text' if text_match else 'entity'
            })
    
    return jsonify({
        'success': True,
        'results': results,
        'count': len(results)
    })

@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all stored notes."""
    return jsonify({
        'success': True,
        'notes': [
            {
                'id': note['id'],
                'title': note.get('title', f"Note {note['id'] + 1}"),
                'entities': note['entities'],
                'timestamp': note['timestamp'],
                'preview': note['text'][:100] + "..." if len(note['text']) > 100 else note['text']
            }
            for note in notes_store
        ],
        'count': len(notes_store)
    })

@app.route('/api/export/<int:note_id>', methods=['GET'])
def export_note(note_id):
    """Export a note as Obsidian markdown."""
    if note_id < 0 or note_id >= len(notes_store):
        return jsonify({'error': 'Note not found'}), 404
    
    note = notes_store[note_id]
    title = note.get('title', f"Note {note_id + 1}")
    
    markdown_content = generate_obsidian_markdown(
        note['text'],
        note['entities'],
        title
    )
    
    # Create a temporary file
    filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return send_file(
        filepath,
        as_attachment=True,
        download_name=filename,
        mimetype='text/markdown'
    )

@app.route('/api/clear', methods=['POST'])
def clear_notes():
    """Clear all stored notes (demo reset)."""
    global notes_store
    notes_store = []
    return jsonify({'success': True, 'message': 'All notes cleared'})

if __name__ == '__main__':
    print("Starting Broadcaster Notes Web UI...")
    print("Open http://localhost:8080 in your browser")
    print("Press Ctrl+C to stop")
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    app.run(host='0.0.0.0', port=8080, debug=False)