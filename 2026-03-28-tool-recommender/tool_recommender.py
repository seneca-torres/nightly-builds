#!/usr/bin/env python3
"""
Tool Recommender - Prevents tool duplication by recommending existing tools.

Scans TOOLS_REGISTRY.md and nightly-builds directory to build an index of
existing tools, then matches natural language queries against tool descriptions
to suggest relevant tools before building something new.
"""

import os
import re
import sys
import json
import argparse
import math
import collections
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


class ToolRecommender:
    def __init__(self, tools_registry_path: str, nightly_builds_path: str):
        self.tools_registry_path = tools_registry_path
        self.nightly_builds_path = nightly_builds_path
        self.tools: List[Dict[str, Any]] = []
        self.term_freq: Dict[str, Dict[int, int]] = {}  # term -> tool_idx -> count
        self.doc_freq: Dict[str, int] = {}  # term -> number of docs containing it
        self.tool_texts: List[str] = []
        
    def load_tools(self) -> None:
        """Load tools from TOOLS_REGISTRY.md and nightly-builds directory."""
        self.tools = []
        
        # Load from TOOLS_REGISTRY.md if it exists
        if os.path.exists(self.tools_registry_path):
            self._parse_tools_registry()
        
        # Scan nightly-builds directory
        self._scan_nightly_builds()
        
        # Build search index
        self._build_index()
    
    def _parse_tools_registry(self) -> None:
        """Parse TOOLS_REGISTRY.md file."""
        try:
            with open(self.tools_registry_path, 'r') as f:
                content = f.read()
            
            # Parse sections (tools are under ## or ### headings)
            lines = content.split('\n')
            current_tool = None
            current_section = None
            
            for line in lines:
                # Section headers
                if line.startswith('### '):
                    # This is likely a tool entry
                    tool_name = line[4:].strip()
                    if tool_name and not tool_name.startswith('('):
                        current_tool = {
                            'name': tool_name,
                            'source': 'TOOLS_REGISTRY.md',
                            'description': '',
                            'location': '',
                            'when_to_use': '',
                            'added': '',
                            'category': self._get_category(line)
                        }
                        self.tools.append(current_tool)
                
                elif line.startswith('**File:**'):
                    if current_tool:
                        location = line.replace('**File:**', '').strip()
                        if location.startswith('`') and location.endswith('`'):
                            location = location[1:-1]
                        current_tool['location'] = location
                
                elif line.startswith('**What it does:**'):
                    if current_tool:
                        description = line.replace('**What it does:**', '').strip()
                        current_tool['description'] = description
                
                elif line.startswith('**When to use:**'):
                    if current_tool:
                        when_to_use = line.replace('**When to use:**', '').strip()
                        current_tool['when_to_use'] = when_to_use
                
                elif line.startswith('**Added:**'):
                    if current_tool:
                        added = line.replace('**Added:**', '').strip()
                        current_tool['added'] = added
                        
        except Exception as e:
            print(f"Warning: Failed to parse TOOLS_REGISTRY.md: {e}", file=sys.stderr)
    
    def _get_category(self, line: str) -> str:
        """Extract category from emoji or context."""
        if '🗺️' in line or 'Visualization' in line:
            return 'Visualization'
        elif '📊' in line or 'Data' in line:
            return 'Data'
        elif '📧' in line or 'Email' in line:
            return 'Email'
        elif '📅' in line or 'Calendar' in line:
            return 'Calendar'
        elif '🔧' in line or 'Utilities' in line:
            return 'Utilities'
        elif '🏀' in line:
            return 'CBB'
        elif '🏈' in line:
            return 'Football'
        elif '🗃️' in line:
            return 'Coach Data'
        else:
            return 'Other'
    
    def _scan_nightly_builds(self) -> None:
        """Scan nightly-builds directory for tools."""
        if not os.path.exists(self.nightly_builds_path):
            return
        
        for build_dir in sorted(os.listdir(self.nightly_builds_path)):
            build_path = os.path.join(self.nightly_builds_path, build_dir)
            if not os.path.isdir(build_path):
                continue
            
            # Skip if not a date directory
            if not re.match(r'\d{4}-\d{2}-\d{2}', build_dir):
                continue
            
            # Look for Python files
            py_files = glob.glob(os.path.join(build_path, '*.py'))
            for py_file in py_files:
                tool_name = os.path.basename(py_file).replace('.py', '')
                if tool_name == 'test' or tool_name == 'verify':
                    continue
                
                # Read README if it exists
                description = ''
                when_to_use = ''
                readme_path = os.path.join(build_path, 'README.md')
                if os.path.exists(readme_path):
                    try:
                        with open(readme_path, 'r') as f:
                            readme_content = f.read()
                            # Extract first paragraph after title
                            lines = readme_content.split('\n')
                            for i, line in enumerate(lines):
                                if line.startswith('# '):
                                    # Get next non-empty line as description
                                    for j in range(i + 1, min(i + 5, len(lines))):
                                        if lines[j].strip() and not lines[j].startswith('#'):
                                            description = lines[j].strip()
                                            break
                                    break
                    except:
                        pass
                
                tool = {
                    'name': tool_name,
                    'source': f'nightly-builds/{build_dir}',
                    'description': description or f"Tool from {build_dir}",
                    'location': py_file,
                    'when_to_use': when_to_use,
                    'added': build_dir,
                    'category': 'Nightly Build'
                }
                self.tools.append(tool)
    
    def _build_index(self) -> None:
        """Build TF-IDF index for tool descriptions."""
        self.term_freq = {}
        self.doc_freq = {}
        self.tool_texts = []
        
        for i, tool in enumerate(self.tools):
            # Combine relevant text for searching
            text = f"{tool['name']} {tool['description']} {tool['when_to_use']} {tool['category']}".lower()
            self.tool_texts.append(text)
            
            # Tokenize
            tokens = re.findall(r'\b[a-z]{3,}\b', text)
            term_counts = collections.Counter(tokens)
            
            # Update term frequencies
            for term, count in term_counts.items():
                if term not in self.term_freq:
                    self.term_freq[term] = {}
                self.term_freq[term][i] = count
            
            # Update document frequencies (once per document per term)
            for term in set(tokens):
                self.doc_freq[term] = self.doc_freq.get(term, 0) + 1
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[float, Dict[str, Any]]]:
        """Search for tools matching the query."""
        if not self.tools:
            return []
        
        query_terms = re.findall(r'\b[a-z]{3,}\b', query.lower())
        if not query_terms:
            return []
        
        scores = [0.0] * len(self.tools)
        
        # Simple TF-IDF scoring
        for term in query_terms:
            if term not in self.term_freq:
                continue
            
            # IDF = log(N / df)
            idf = math.log(len(self.tools) / self.doc_freq[term])
            
            # For each document containing the term
            for doc_idx, tf in self.term_freq[term].items():
                # TF = 1 + log(tf)
                tf_score = 1 + math.log(tf)
                scores[doc_idx] += tf_score * idf
        
        # Get top K results
        scored_tools = list(zip(scores, self.tools))
        scored_tools.sort(key=lambda x: x[0], reverse=True)
        
        return scored_tools[:top_k]
    
    def add_tool(self, name: str, description: str, location: str, category: str = "Other") -> None:
        """Add a new tool to the registry (--learn mode)."""
        tool = {
            'name': name,
            'source': 'Manual addition',
            'description': description,
            'location': location,
            'when_to_use': '',
            'added': datetime.now().strftime('%Y-%m-%d'),
            'category': category
        }
        self.tools.append(tool)
        
        # Rebuild index
        self._build_index()
        
        # Update TOOLS_REGISTRY.md
        self._update_tools_registry(tool)
    
    def _update_tools_registry(self, tool: Dict[str, Any]) -> None:
        """Append tool to TOOLS_REGISTRY.md."""
        try:
            with open(self.tools_registry_path, 'a') as f:
                f.write(f"\n\n### {tool['name']}\n")
                f.write(f"**File:** `{tool['location']}`\n")
                f.write(f"**What it does:** {tool['description']}\n")
                if tool.get('when_to_use'):
                    f.write(f"**When to use:** {tool['when_to_use']}\n")
                f.write(f"**Added:** {tool['added']}\n")
            print(f"✓ Added {tool['name']} to TOOLS_REGISTRY.md")
        except Exception as e:
            print(f"Warning: Could not update TOOLS_REGISTRY.md: {e}", file=sys.stderr)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about tools."""
        categories = collections.Counter(t['category'] for t in self.tools)
        sources = collections.Counter(t['source'] for t in self.tools)
        
        return {
            'total_tools': len(self.tools),
            'categories': dict(categories),
            'sources': dict(sources),
            'oldest_tool': min((t['added'] for t in self.tools if t['added']), default='Unknown'),
            'newest_tool': max((t['added'] for t in self.tools if t['added']), default='Unknown')
        }


def main():
    parser = argparse.ArgumentParser(
        description='Tool Recommender - Prevents tool duplication by recommending existing tools.'
    )
    parser.add_argument('query', nargs='?', help='Natural language query describing what you need')
    parser.add_argument('--learn', action='store_true', help='Add a new tool to the registry')
    parser.add_argument('--stats', action='store_true', help='Show tool statistics')
    parser.add_argument('--demo', action='store_true', help='Run demo queries')
    parser.add_argument('--list', action='store_true', help='List all tools')
    parser.add_argument('--registry', default='~/clawd/TOOLS_REGISTRY.md', help='Path to TOOLS_REGISTRY.md')
    parser.add_argument('--nightly', default='~/clawd/nightly-builds', help='Path to nightly-builds directory')
    parser.add_argument('--top', type=int, default=3, help='Number of results to show (default: 3)')
    
    args = parser.parse_args()
    
    # Expand tilde paths
    registry_path = os.path.expanduser(args.registry)
    nightly_path = os.path.expanduser(args.nightly)
    
    # Initialize recommender
    recommender = ToolRecommender(registry_path, nightly_path)
    recommender.load_tools()
    
    if args.stats:
        stats = recommender.get_stats()
        print(f"\n📊 Tool Statistics")
        print(f"   Total tools: {stats['total_tools']}")
        print(f"   Categories: {', '.join(f'{k} ({v})' for k, v in stats['categories'].items())}")
        print(f"   Sources: {', '.join(f'{k} ({v})' for k, v in stats['sources'].items())}")
        print(f"   Oldest: {stats['oldest_tool']}")
        print(f"   Newest: {stats['newest_tool']}")
        return 0
    
    if args.list:
        print(f"\n📋 All Tools ({len(recommender.tools)} total)")
        for i, tool in enumerate(recommender.tools, 1):
            print(f"\n{i}. {tool['name']} ({tool['category']})")
            print(f"   Source: {tool['source']}")
            print(f"   Description: {tool['description'][:100]}...")
            if tool['location']:
                print(f"   Location: {tool['location']}")
        return 0
    
    if args.demo:
        print("🚀 Running demo queries...\n")
        demos = [
            "search session logs",
            "calendar management",
            "github pull requests",
            "football data",
            "voice notes",
            "rental search"
        ]
        for query in demos:
            print(f"Query: '{query}'")
            results = recommender.search(query, top_k=2)
            if results:
                for score, tool in results:
                    print(f"  • {tool['name']} (score: {score:.2f}) - {tool['description'][:80]}...")
            else:
                print(f"  No matches found")
            print()
        return 0
    
    if args.learn:
        print("📝 Add a new tool to the registry")
        name = input("Tool name: ").strip()
        description = input("Description (what it does): ").strip()
        location = input("File path: ").strip()
        category = input("Category (Visualization/Data/Calendar/Utilities/etc): ").strip() or "Other"
        
        recommender.add_tool(name, description, location, category)
        print("✓ Tool added successfully!")
        return 0
    
    if args.query:
        print(f"\n🔍 Searching for: '{args.query}'")
        results = recommender.search(args.query, top_k=args.top)
        
        if not results:
            print("🤷 No matching tools found.")
            print("\n💡 Try one of these similar tools:")
            # Show some random tools as suggestions
            for i, tool in enumerate(recommender.tools[:3]):
                print(f"\n{i+1}. {tool['name']}")
                print(f"   {tool['description'][:100]}...")
                print(f"   Source: {tool['source']}")
            return 0
        
        print(f"✅ Found {len(results)} matching tool{'s' if len(results) > 1 else ''}:\n")
        
        for i, (score, tool) in enumerate(results, 1):
            print(f"{i}. {tool['name']} (score: {score:.2f})")
            print(f"   📍 Source: {tool['source']}")
            if tool['description']:
                print(f"   📝 {tool['description']}")
            if tool['when_to_use']:
                print(f"   🕐 When to use: {tool['when_to_use']}")
            if tool['location']:
                print(f"   📂 Location: {tool['location']}")
            if tool['added']:
                print(f"   📅 Added: {tool['added']}")
            print()
        
        print("💡 Use `--list` to see all tools or `--stats` for statistics.")
        return 0
    
    # No arguments, show help
    parser.print_help()
    print("\n📚 Examples:")
    print("  python tool_recommender.py 'search session logs'")
    print("  python tool_recommender.py --stats")
    print("  python tool_recommender.py --list")
    print("  python tool_recommender.py --demo")
    print("  python tool_recommender.py --learn")
    return 0


if __name__ == '__main__':
    sys.exit(main())