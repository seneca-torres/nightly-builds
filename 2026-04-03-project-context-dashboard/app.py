#!/usr/bin/env python3
"""
Project Context Dashboard - Flask Backend

A web dashboard for managing and visualizing Victor's project auto-load system.
Provides visibility into Telegram topic → project mappings and project context.
"""

import os
import json
import glob
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from pathlib import Path

# Configuration
CLAWD_PATH = os.path.expanduser("~/clawd")
PROJECT_REGISTRY_PATH = os.path.join(CLAWD_PATH, "memory/project-registry.json")
PROJECTS_PATH = os.path.join(CLAWD_PATH, "memory/projects")
DAILY_PATH = os.path.join(CLAWD_PATH, "memory/daily")
TOPIC_WATCHDOG_PATH = os.path.join(CLAWD_PATH, "runtime/topic-lane-watchdog-events.jsonl")

app = Flask(__name__)

def load_project_registry():
    """Load the project registry JSON file."""
    try:
        with open(PROJECT_REGISTRY_PATH, 'r') as f:
            data = json.load(f)
            return data.get('projects', {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading project registry: {e}")
        return {}

def get_recent_topics():
    """Extract recent topic IDs from topic-lane-watchdog-events.jsonl."""
    recent_topics = set()
    try:
        if os.path.exists(TOPIC_WATCHDOG_PATH):
            with open(TOPIC_WATCHDOG_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # Simple extraction of topicId
                        match = re.search(r'"topicId":"(\d+)"', line)
                        if match:
                            recent_topics.add(match.group(1))
    except Exception as e:
        print(f"Error reading topic watchdog file: {e}")
    
    return sorted(recent_topics, key=int)

def get_mapped_and_unmapped_topics():
    """Return mapped and unmapped topics."""
    registry = load_project_registry()
    recent_topics = get_recent_topics()
    
    mapped = {}
    unmapped = []
    
    # Find mapped topics
    for slug, project in registry.items():
        topic_id = str(project.get('topicId', ''))
        if topic_id:
            mapped[topic_id] = project
    
    # Find unmapped topics
    for topic_id in recent_topics:
        if topic_id not in mapped:
            unmapped.append(topic_id)
    
    return mapped, unmapped

def get_project_context(slug):
    """Get context for a specific project."""
    registry = load_project_registry()
    if slug not in registry:
        return None
    
    project = registry[slug]
    file_path = os.path.join(CLAWD_PATH, project.get('file', ''))
    
    # Read project file
    content = ""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file: {e}"
    
    # Get recent activity (last 7 days)
    recent_activity = get_recent_activity_for_project(slug)
    
    # Extract todos/deadlines
    todos = extract_todos(content)
    
    return {
        **project,
        'content': content,
        'recent_activity': recent_activity,
        'todos': todos,
        'exists': os.path.exists(file_path)
    }

def get_recent_activity_for_project(slug):
    """Get recent activity for a project from daily logs."""
    activity = []
    try:
        # Get last 7 days of daily files
        today = datetime.now()
        for i in range(7):
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            file_path = os.path.join(DAILY_PATH, f"{date_str}.md")
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    # Look for project mentions
                    if f"#{slug}" in content or slug in content.lower():
                        # Extract relevant events
                        lines = content.split('\n')
                        in_events = False
                        for line in lines:
                            if line.startswith('## Events'):
                                in_events = True
                                continue
                            if in_events and line.startswith('##'):
                                break
                            if in_events and line.strip() and '[' in line and ']' in line:
                                # Check if this line mentions the project
                                if f"#{slug}" in line or slug in line.lower():
                                    activity.append({
                                        'date': date_str,
                                        'entry': line.strip()
                                    })
    except Exception as e:
        print(f"Error getting recent activity: {e}")
    
    return activity[:10]  # Return last 10 entries

def extract_todos(content):
    """Extract TODO items from project content."""
    todos = []
    lines = content.split('\n')
    for line in lines:
        if 'TODO' in line.upper() or 'FIXME' in line.upper() or 'XXX' in line.upper():
            todos.append(line.strip())
    return todos[:10]  # Return at most 10 todos

def get_all_projects_context():
    """Get context for all projects."""
    registry = load_project_registry()
    projects = {}
    
    for slug in registry:
        context = get_project_context(slug)
        if context:
            projects[slug] = context
    
    return projects

@app.route('/')
def index():
    """Main dashboard page."""
    mapped, unmapped = get_mapped_and_unmapped_topics()
    all_projects = get_all_projects_context()
    
    return render_template('index.html',
                         mapped_topics=mapped,
                         unmapped_topics=unmapped,
                         all_projects=all_projects,
                         total_mapped=len(mapped),
                         total_unmapped=len(unmapped))

@app.route('/api/projects')
def api_projects():
    """API endpoint for projects data."""
    mapped, unmapped = get_mapped_and_unmapped_topics()
    return jsonify({
        'mapped': mapped,
        'unmapped': unmapped,
        'registry': load_project_registry()
    })

@app.route('/api/project/<slug>')
def api_project(slug):
    """API endpoint for specific project."""
    context = get_project_context(slug)
    if context:
        return jsonify(context)
    return jsonify({'error': 'Project not found'}), 404

@app.route('/api/recent-activity')
def api_recent_activity():
    """API endpoint for recent activity across all projects."""
    activity = []
    try:
        # Get today's daily file
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(DAILY_PATH, f"{today}.md")
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                in_events = False
                for line in lines:
                    if line.startswith('## Events'):
                        in_events = True
                        continue
                    if in_events and line.startswith('##'):
                        break
                    if in_events and line.strip() and '[' in line and ']' in line:
                        activity.append(line.strip())
    except Exception as e:
        print(f"Error getting recent activity: {e}")
    
    return jsonify({'activity': activity[:20]})

@app.route('/api/create-mapping', methods=['POST'])
def create_mapping():
    """API endpoint to create a new mapping (simulated - would require file write)."""
    # Note: This is a demo version - real implementation would write to file
    data = request.json
    topic_id = data.get('topicId')
    slug = data.get('slug')
    label = data.get('label')
    
    if not all([topic_id, slug, label]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    return jsonify({
        'message': 'Mapping created (simulated)',
        'mapping': {
            'topicId': topic_id,
            'slug': slug,
            'label': label
        }
    })

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("Project Context Dashboard starting...")
    print(f"Clawd path: {CLAWD_PATH}")
    print(f"Projects in registry: {len(load_project_registry())}")
    
    app.run(host='127.0.0.1', port=5150, debug=True)