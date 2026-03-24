#!/usr/bin/env python3
"""
Tool Catalog CLI - Discover and reference tools built in nightly builds.

Scans the ~/clawd/nightly-builds directory to create a searchable catalog
of all tools and utilities built during nightly builds.
"""

import os
import json
import argparse
import sys
import re
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import textwrap

class ToolCatalog:
    """Main tool catalog class."""
    
    def __init__(self, base_path: str = "~/clawd/nightly-builds"):
        """Initialize with path to nightly builds."""
        self.base_path = os.path.expanduser(base_path)
        self.catalog_file = os.path.join(self.base_path, "tool_catalog.json")
        self.tools: List[Dict[str, Any]] = []
        
    def scan_directory(self) -> List[Dict[str, Any]]:
        """Scan nightly-builds directory for tools."""
        tools = []
        seen_tools = set()  # Track to avoid duplicates
        
        # Get all directories that look like date directories
        all_dirs = [d for d in os.listdir(self.base_path) 
                   if os.path.isdir(os.path.join(self.base_path, d))]
        
        for dir_name in sorted(all_dirs, reverse=True):
            dir_path = os.path.join(self.base_path, dir_name)
            
            # Skip hidden directories
            if dir_name.startswith('.'):
                continue
            
            # Check if this is a date directory (starts with YYYY-MM-DD)
            date_match = re.match(r'(\d{4}-\d{2}-\d{2})(?:-(.+))?', dir_name)
            if not date_match:
                continue  # Skip non-date directories
                
            date_part = date_match.group(1)
            tool_name_part = date_match.group(2) or dir_name
            
            # Check if this directory contains tool files
            try:
                contents = os.listdir(dir_path)
            except (FileNotFoundError, PermissionError):
                continue
            
            # Look for tool indicators
            has_python = any(f.endswith('.py') for f in contents)
            has_readme = any(f.lower() == 'readme.md' for f in contents)
            has_verification = any(f.startswith('verify.') for f in contents)
            
            # Skip if doesn't look like a tool (except for known tool directories)
            if not (has_python or has_readme or has_verification):
                # Check if it might be a directory containing sub-tools
                subdirs = [d for d in contents if os.path.isdir(os.path.join(dir_path, d))]
                has_subdirs_with_tools = False
                
                for subdir in subdirs:
                    if subdir.startswith('.') or (subdir.startswith('__') and subdir.endswith('__')):
                        continue
                    
                    subdir_path = os.path.join(dir_path, subdir)
                    try:
                        sub_contents = os.listdir(subdir_path)
                        if any(f.endswith('.py') for f in sub_contents) or any(f.lower() == 'readme.md' for f in sub_contents):
                            # This is a subdirectory with a tool
                            tool_info = self._extract_tool_info(date_part, subdir, subdir_path)
                            if tool_info and subdir not in seen_tools:
                                seen_tools.add(subdir)
                                tools.append(tool_info)
                            has_subdirs_with_tools = True
                    except (FileNotFoundError, PermissionError):
                        continue
                
                if has_subdirs_with_tools:
                    continue  # Already processed subdirectories
                else:
                    continue  # Not a tool directory
            
            # Extract tool info from this directory
            tool_info = self._extract_tool_info(date_part, tool_name_part, dir_path)
            if tool_info:
                # Use a cleaner identifier (without date prefix for uniqueness)
                clean_id = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', dir_name)
                if clean_id not in seen_tools:
                    seen_tools.add(clean_id)
                    tools.append(tool_info)
        
        self.tools = tools
        return tools
    
    def _extract_tool_info(self, date: str, dir_name: str, tool_path: str) -> Optional[Dict[str, Any]]:
        """Extract tool information from directory."""
        # Try to read README.md first
        readme_path = os.path.join(tool_path, "README.md")
        description = ""
        usage = ""
        
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                    # Extract first paragraph as description
                    lines = readme_content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('```') and not line.startswith('---'):
                            description = line
                            break
            except (UnicodeDecodeError, IOError):
                pass
        
        # Look for Python files
        python_files = glob.glob(os.path.join(tool_path, "*.py"))
        main_file = None
        if python_files:
            # Try to find the main Python file
            # First, look for files that match directory name (without date prefix)
            clean_dir_name = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', dir_name)
            possible_main_names = [
                f"{clean_dir_name}.py",
                f"{clean_dir_name.replace('-', '_')}.py",
                "main.py",
                "cli.py",
                "tool.py"
            ]
            
            for py_file in python_files:
                basename = os.path.basename(py_file).lower()
                for possible_name in possible_main_names:
                    if basename == possible_name.lower():
                        main_file = py_file
                        break
                if main_file:
                    break
            
            # If no main file found, use the largest Python file
            if not main_file:
                main_file = max(python_files, key=lambda f: os.path.getsize(f) if os.path.exists(f) else 0)
        
        # Extract usage from README or Python file
        usage = self._extract_usage(readme_path if os.path.exists(readme_path) else None, main_file)
        
        # Clean up directory name for tool name
        # Remove date prefix if present (e.g., "2026-03-02-calendar-quickadd" -> "calendar-quickadd")
        clean_dir = dir_name
        if re.match(r'\d{4}-\d{2}-\d{2}-', dir_name):
            clean_dir = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', dir_name)
        
        # Convert to readable name
        tool_name = clean_dir.replace('-', ' ').title()
        
        # Special handling for known acronyms
        acronyms = {
            'cli': 'CLI',
            'api': 'API',
            'pr': 'PR',
            'gh': 'GitHub',
            'cfbd': 'CFBD',
            'opad': 'OPAD',
            'crm': 'CRM',
            'rag': 'RAG',
            'html': 'HTML',
            'css': 'CSS',
            'js': 'JavaScript',
            'json': 'JSON',
            'yaml': 'YAML',
            'csv': 'CSV',
            'pdf': 'PDF',
            'ui': 'UI',
            'ux': 'UX',
            'epa': 'EPA',
            'cbb': 'CBB',
            'nfl': 'NFL',
            'ncaa': 'NCAA',
            'sec': 'SEC',
            'fbs': 'FBS',
            'fcs': 'FCS',
            'w-l': 'W-L'
        }
        
        # Apply acronym replacements
        words = tool_name.split()
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in acronyms:
                words[i] = acronyms[word_lower]
        tool_name = ' '.join(words)
        
        return {
            'id': f"{date}-{clean_dir}",
            'name': tool_name,
            'date': date,
            'directory': clean_dir,
            'path': tool_path,
            'description': description[:200] + '...' if len(description) > 200 else description,
            'usage': usage,
            'main_file': main_file,
            'has_verification': os.path.exists(os.path.join(tool_path, "verify.py")) or 
                               os.path.exists(os.path.join(tool_path, "verify.sh")) or
                               os.path.exists(os.path.join(tool_path, "test.py"))
        }
    
    def _extract_usage(self, readme_path: Optional[str], python_file: Optional[str]) -> str:
        """Extract usage examples from README or Python file."""
        usage_lines = []
        
        # Try README first
        if readme_path:
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for code blocks with usage
                in_code_block = False
                for line in content.split('\n'):
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                    elif in_code_block and ('usage' in line.lower() or 'example' in line.lower()):
                        usage_lines.append(line)
                    elif not in_code_block and line.strip().startswith('Usage:'):
                        usage_lines.append(line)
        
        # Try Python file docstring
        if python_file and not usage_lines:
            try:
                with open(python_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for docstring
                    docstring_match = re.search(r'\"\"\"(.*?)\"\"\"', content, re.DOTALL)
                    if docstring_match:
                        docstring = docstring_match.group(1)
                        for line in docstring.split('\n'):
                            if 'usage' in line.lower() or 'example' in line.lower():
                                usage_lines.append(line.strip())
            except:
                pass
        
        # Try to find argparse usage
        if python_file and not usage_lines:
            try:
                with open(python_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'argparse' in content:
                        usage_lines.append("Uses argparse - run with --help for usage")
            except:
                pass
        
        return '\n'.join(usage_lines[:3]) if usage_lines else "Run with --help for usage"
    
    def save_catalog(self) -> None:
        """Save catalog to JSON file."""
        catalog = {
            'generated': datetime.now().isoformat(),
            'count': len(self.tools),
            'tools': self.tools
        }
        with open(self.catalog_file, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2)
    
    def load_catalog(self) -> bool:
        """Load catalog from JSON file."""
        if os.path.exists(self.catalog_file):
            try:
                with open(self.catalog_file, 'r', encoding='utf-8') as f:
                    catalog = json.load(f)
                self.tools = catalog.get('tools', [])
                return True
            except:
                pass
        return False
    
    def list_tools(self, verbose: bool = False) -> str:
        """List all tools."""
        if not self.tools:
            return "No tools found. Run 'scan' first."
        
        output = []
        if verbose:
            output.append(f"{'Date':<12} {'Name':<30} {'Description':<50}")
            output.append("-" * 94)
            for tool in self.tools:
                output.append(f"{tool['date']:<12} {tool['name'][:28]:<30} {tool['description'][:48]:<50}")
        else:
            for i, tool in enumerate(self.tools, 1):
                output.append(f"{i:3}. {tool['date']} - {tool['name']}")
        
        return '\n'.join(output)
    
    def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search tools by name, description, or directory."""
        query = query.lower()
        results = []
        for tool in self.tools:
            if (query in tool['name'].lower() or 
                query in tool['description'].lower() or
                query in tool['directory'].lower()):
                results.append(tool)
        return results
    
    def get_tool_info(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a specific tool."""
        # Try to match by ID first
        for tool in self.tools:
            if tool['id'] == identifier:
                return tool
        
        # Try by directory name
        for tool in self.tools:
            if tool['directory'] == identifier:
                return tool
        
        # Try by name (case-insensitive)
        identifier_lower = identifier.lower()
        for tool in self.tools:
            if tool['name'].lower() == identifier_lower:
                return tool
        
        # Try partial match
        for tool in self.tools:
            if identifier_lower in tool['name'].lower() or identifier_lower in tool['directory'].lower():
                return tool
        
        return None
    
    def generate_markdown(self) -> str:
        """Generate a Markdown reference table."""
        if not self.tools:
            return "No tools to generate markdown for."
        
        output = ["# Tool Catalog Reference", "", f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*", ""]
        output.append("| Date | Name | Directory | Description |")
        output.append("|------|------|-----------|-------------|")
        
        for tool in self.tools:
            # Escape pipes in description
            desc = tool['description'].replace('|', '\\|')
            output.append(f"| {tool['date']} | {tool['name']} | `{tool['directory']}` | {desc} |")
        
        output.append("")
        output.append("## Usage")
        output.append("")
        output.append("```bash")
        output.append("# List all tools")
        output.append("python3 tool-catalog.py list")
        output.append("")
        output.append("# Search for tools")
        output.append("python3 tool-catalog.py search 'calendar'")
        output.append("")
        output.append("# Get detailed info about a tool")
        output.append("python3 tool-catalog.py info 'calendar-quickadd'")
        output.append("")
        output.append("# Generate this markdown table")
        output.append("python3 tool-catalog.py generate-markdown > catalog.md")
        output.append("```")
        
        return '\n'.join(output)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Tool Catalog CLI - Discover and reference nightly build tools")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan nightly-builds directory and update catalog')
    scan_parser.add_argument('--force', action='store_true', help='Force rescan even if catalog exists')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all tools')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search tools')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get detailed info about a tool')
    info_parser.add_argument('identifier', help='Tool name, directory, or ID')
    
    # Usage command
    usage_parser = subparsers.add_parser('usage', help='Show usage examples for a tool')
    usage_parser.add_argument('identifier', help='Tool name, directory, or ID')
    
    # Generate markdown command
    md_parser = subparsers.add_parser('generate-markdown', help='Generate markdown reference table')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update catalog (scan + save)')
    
    args = parser.parse_args()
    
    catalog = ToolCatalog()
    
    # Load catalog if it exists
    catalog_loaded = catalog.load_catalog()
    
    if args.command == 'scan':
        print("Scanning nightly-builds directory...")
        tools_found = catalog.scan_directory()
        print(f"Found {len(tools_found)} tools")
        catalog.save_catalog()
        print(f"Catalog saved to {catalog.catalog_file}")
        
    elif args.command == 'update':
        print("Updating catalog...")
        catalog.scan_directory()
        catalog.save_catalog()
        print(f"Catalog updated with {len(catalog.tools)} tools")
        
    elif args.command == 'list':
        if not catalog.tools and not catalog_loaded:
            print("No catalog loaded. Run 'scan' first.")
            return
        print(catalog.list_tools(verbose=args.verbose))
        
    elif args.command == 'search':
        if not catalog.tools and not catalog_loaded:
            print("No catalog loaded. Run 'scan' first.")
            return
        results = catalog.search_tools(args.query)
        if not results:
            print(f"No tools found matching '{args.query}'")
            return
        
        if args.verbose:
            print(f"Found {len(results)} tools matching '{args.query}':")
            print(f"{'Date':<12} {'Name':<30} {'Description':<50}")
            print("-" * 94)
            for tool in results:
                print(f"{tool['date']:<12} {tool['name'][:28]:<30} {tool['description'][:48]:<50}")
        else:
            print(f"Found {len(results)} tools matching '{args.query}':")
            for i, tool in enumerate(results, 1):
                print(f"{i:3}. {tool['date']} - {tool['name']} ({tool['directory']})")
        
    elif args.command == 'info':
        if not catalog.tools and not catalog_loaded:
            print("No catalog loaded. Run 'scan' first.")
            return
        
        tool = catalog.get_tool_info(args.identifier)
        if not tool:
            print(f"Tool not found: {args.identifier}")
            print("Try 'list' to see all available tools.")
            return
        
        print(f"Tool: {tool['name']}")
        print(f"ID: {tool['id']}")
        print(f"Date: {tool['date']}")
        print(f"Directory: {tool['directory']}")
        print(f"Path: {tool['path']}")
        print(f"Description: {tool['description']}")
        print(f"Main file: {tool['main_file'] or 'Not found'}")
        print(f"Has verification script: {'Yes' if tool['has_verification'] else 'No'}")
        print("\nQuick access:")
        print(f"  cd {tool['path']}")
        if tool['main_file']:
            print(f"  python3 {os.path.basename(tool['main_file'])} --help")
        
    elif args.command == 'usage':
        if not catalog.tools and not catalog_loaded:
            print("No catalog loaded. Run 'scan' first.")
            return
        
        tool = catalog.get_tool_info(args.identifier)
        if not tool:
            print(f"Tool not found: {args.identifier}")
            return
        
        print(f"Usage for {tool['name']} ({tool['directory']}):")
        print("-" * 60)
        if tool['usage']:
            print(tool['usage'])
        else:
            print("No usage examples found.")
            if tool['main_file']:
                print(f"\nTry: cd {tool['path']} && python3 {os.path.basename(tool['main_file'])} --help")
        
    elif args.command == 'generate-markdown':
        if not catalog.tools and not catalog_loaded:
            print("No catalog loaded. Run 'scan' first.")
            return
        print(catalog.generate_markdown())
        
    else:
        # No command provided, show help
        parser.print_help()
        print("\nExamples:")
        print("  python3 tool-catalog.py scan                     # Scan for tools")
        print("  python3 tool-catalog.py list                     # List all tools")
        print("  python3 tool-catalog.py search 'calendar'        # Search for calendar tools")
        print("  python3 tool-catalog.py info 'calendar-quickadd' # Get info about a tool")
        print("  python3 tool-catalog.py usage 'calendar-quickadd' # Show usage examples")
        print("  python3 tool-catalog.py generate-markdown        # Generate markdown table")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)