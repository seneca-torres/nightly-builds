#!/usr/bin/env python3
"""
Coach-School Relationship Parser

Parses broadcaster notes (markdown with YAML frontmatter) to extract
coach-school relationships and build a graph for visualization.
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime
from collections import defaultdict
from pathlib import Path

class RelationshipParser:
    def __init__(self):
        self.coaches = defaultdict(int)  # coach name -> frequency
        self.schools = defaultdict(int)  # school name -> frequency
        self.relationships = []  # list of {coach, school, date, source}
        self.coach_school_pairs = set()  # (coach, school) tuples for dedup
        
    def parse_markdown_file(self, filepath):
        """Parse a markdown file with YAML frontmatter."""
        content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        
        # Try to extract YAML frontmatter (simple parsing without PyYAML)
        frontmatter = {}
        body = content
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_str = parts[1]
                body = parts[2] if len(parts) > 2 else ""
                
                # Simple YAML parsing for coaches and schools
                for line in frontmatter_str.split('\n'):
                    line = line.strip()
                    if line.startswith('coaches:'):
                        # Parse list format: coaches: ["Name1", "Name2"]
                        coaches_match = re.search(r'\[(.*?)\]', line)
                        if coaches_match:
                            coaches_str = coaches_match.group(1)
                            coaches = [c.strip().strip('"\'') for c in coaches_str.split(',') if c.strip()]
                            frontmatter['coaches'] = coaches
                    elif line.startswith('schools:'):
                        schools_match = re.search(r'\[(.*?)\]', line)
                        if schools_match:
                            schools_str = schools_match.group(1)
                            schools = [s.strip().strip('"\'') for s in schools_str.split(',') if s.strip()]
                            frontmatter['schools'] = schools
                    elif line.startswith('date:'):
                        date_match = re.search(r'date:\s*["\']?(.*?)["\']?$', line)
                        if date_match:
                            frontmatter['date'] = date_match.group(1).strip()
        
        # Extract coaches and schools from frontmatter
        coaches = frontmatter.get('coaches', [])
        schools = frontmatter.get('schools', [])
        date = frontmatter.get('date', '')
        
        # Also extract from body using simple pattern matching
        body_coaches = self._extract_entities(body, r'\b(Coach|coach)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b')
        body_schools = self._extract_entities(body, r'\b(University|College|School|Academy)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b')
        
        all_coaches = list(set(coaches + body_coaches))
        all_schools = list(set(schools + body_schools))
        
        # Create relationships
        for coach in all_coaches:
            self.coaches[coach] += 1
            for school in all_schools:
                self.schools[school] += 1
                pair = (coach, school)
                if pair not in self.coach_school_pairs:
                    self.coach_school_pairs.add(pair)
                    self.relationships.append({
                        'coach': coach,
                        'school': school,
                        'date': date,
                        'source': os.path.basename(filepath)
                    })
        
        return len(all_coaches), len(all_schools)
    
    def _extract_entities(self, text, pattern):
        """Extract entities from text using regex."""
        matches = re.findall(pattern, text)
        # Return the full matched string
        return [match[1] if isinstance(match, tuple) else match for match in matches]
    
    def parse_directory(self, directory, pattern="*.md"):
        """Parse all markdown files in a directory."""
        count = 0
        for filepath in Path(directory).glob(pattern):
            try:
                coaches, schools = self.parse_markdown_file(filepath)
                count += 1
                if count % 10 == 0:
                    print(f"  Processed {count} files...")
            except Exception as e:
                print(f"  Error parsing {filepath}: {e}")
        return count
    
    def to_graph_json(self):
        """Convert parsed data to graph JSON format for D3.js."""
        nodes = []
        edges = []
        node_id_map = {}
        
        # Add coach nodes
        for i, (coach, freq) in enumerate(self.coaches.items()):
            node_id = f"coach_{i}"
            node_id_map[coach] = node_id
            nodes.append({
                'id': node_id,
                'label': coach,
                'type': 'coach',
                'frequency': freq,
                'size': min(30, 10 + freq * 2)  # Size based on frequency
            })
        
        # Add school nodes
        school_offset = len(node_id_map)
        for i, (school, freq) in enumerate(self.schools.items()):
            node_id = f"school_{i}"
            node_id_map[school] = node_id
            nodes.append({
                'id': node_id,
                'label': school,
                'type': 'school',
                'frequency': freq,
                'size': min(40, 15 + freq * 3)
            })
        
        # Add edges (relationships)
        for rel in self.relationships:
            coach_id = node_id_map.get(rel['coach'])
            school_id = node_id_map.get(rel['school'])
            
            if coach_id and school_id:
                # Check if edge already exists
                edge_exists = any(
                    e['source'] == coach_id and e['target'] == school_id 
                    for e in edges
                )
                
                if not edge_exists:
                    edges.append({
                        'source': coach_id,
                        'target': school_id,
                        'date': rel['date'],
                        'source_file': rel['source']
                    })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'total_coaches': len(self.coaches),
                'total_schools': len(self.schools),
                'total_relationships': len(self.relationships),
                'generated_at': datetime.now().isoformat()
            }
        }

def generate_demo_data():
    """Generate demo data for testing."""
    parser = RelationshipParser()
    
    # Sample coach-school relationships (common in college football)
    demo_relationships = [
        # Big names
        ('Nick Saban', 'Alabama', '2007-2023'),
        ('Nick Saban', 'LSU', '2000-2004'),
        ('Nick Saban', 'Michigan State', '1995-1999'),
        ('Kirby Smart', 'Georgia', '2016-present'),
        ('Kirby Smart', 'Alabama', '2007-2015'),
        ('Dabo Swinney', 'Clemson', '2009-present'),
        ('Lincoln Riley', 'USC', '2022-present'),
        ('Lincoln Riley', 'Oklahoma', '2017-2021'),
        
        # Moving between schools
        ('Dan Lanning', 'Oregon', '2022-present'),
        ('Dan Lanning', 'Georgia', '2019-2021'),
        ('Ryan Day', 'Ohio State', '2019-present'),
        ('Ryan Day', 'Ohio State', '2017-2018'),  # OC before HC
        
        # Common coaching trees
        ('Steve Sarkisian', 'Texas', '2021-present'),
        ('Steve Sarkisian', 'Alabama', '2019-2020'),
        ('Steve Sarkisian', 'USC', '2014-2015'),
        ('Kalen DeBoer', 'Alabama', '2024-present'),
        ('Kalen DeBoer', 'Washington', '2022-2023'),
        ('Kalen DeBoer', 'Fresno State', '2020-2021'),
        
        # Schools with multiple coaches
        ('Jim Harbaugh', 'Michigan', '2015-2023'),
        ('Sherrone Moore', 'Michigan', '2024-present'),
        ('Sherrone Moore', 'Michigan', '2018-2023'),  # Assistant before HC
        
        # Cross-conference moves
        ('Brent Venables', 'Oklahoma', '2022-present'),
        ('Brent Venables', 'Clemson', '2012-2021'),
        ('Mike Norvell', 'Florida State', '2020-present'),
        ('Mike Norvell', 'Memphis', '2016-2019'),
    ]
    
    # Add to parser
    for coach, school, date in demo_relationships:
        parser.coaches[coach] += 1
        parser.schools[school] += 1
        parser.relationships.append({
            'coach': coach,
            'school': school,
            'date': date,
            'source': 'demo_data'
        })
        parser.coach_school_pairs.add((coach, school))
    
    return parser

def main():
    parser = argparse.ArgumentParser(description='Parse coach-school relationships from broadcaster notes')
    parser.add_argument('--input', '-i', nargs='+', help='Input markdown files or directories')
    parser.add_argument('--output', '-o', default='data/graph.json', help='Output JSON file')
    parser.add_argument('--demo', action='store_true', help='Generate demo data instead of parsing files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.demo:
        print("Generating demo data...")
        relationship_parser = generate_demo_data()
        print(f"  Generated {len(relationship_parser.coaches)} coaches")
        print(f"  Generated {len(relationship_parser.schools)} schools")
        print(f"  Generated {len(relationship_parser.relationships)} relationships")
    elif args.input:
        relationship_parser = RelationshipParser()
        total_files = 0
        
        for input_path in args.input:
            path = Path(input_path)
            if path.is_file():
                if args.verbose:
                    print(f"Parsing file: {path}")
                coaches, schools = relationship_parser.parse_markdown_file(path)
                if args.verbose:
                    print(f"  Found {coaches} coaches, {schools} schools")
                total_files += 1
            elif path.is_dir():
                if args.verbose:
                    print(f"Parsing directory: {path}")
                files_processed = relationship_parser.parse_directory(path)
                total_files += files_processed
                if args.verbose:
                    print(f"  Processed {files_processed} files")
            else:
                print(f"Warning: {input_path} not found, skipping")
        
        print(f"\nParsed {total_files} files total")
        print(f"Found {len(relationship_parser.coaches)} unique coaches")
        print(f"Found {len(relationship_parser.schools)} unique schools")
        print(f"Found {len(relationship_parser.relationships)} relationships")
    else:
        print("Error: No input files specified. Use --demo for demo data or --input for files.")
        parser.print_help()
        return 1
    
    # Generate graph JSON
    graph_data = relationship_parser.to_graph_json()
    
    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2)
    
    print(f"\nGraph data written to: {output_path}")
    print(f"Total nodes: {graph_data['metadata']['total_nodes']}")
    print(f"Total edges: {graph_data['metadata']['total_edges']}")
    
    # Also write a simpler version for the web visualizer
    web_path = output_path.parent / 'web_graph.json'
    with open(web_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f)
    
    print(f"Web-friendly version: {web_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())