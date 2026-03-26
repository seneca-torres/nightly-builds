#!/usr/bin/env python3
"""
Portfolio Logo Tool - Helps preview and apply logos to the VT Sports Solutions portfolio.

This tool scans for logo files in:
- ~/clawd/portfolio/images/
- ~/clawd/vt-logos/

And provides a web interface to preview and apply them.
"""

import os
import sys
import json
import shutil
from pathlib import Path
import http.server
import socketserver
import webbrowser
from typing import List, Dict, Any

# Paths
PORTFOLIO_ROOT = Path.home() / "clawd" / "portfolio"
PORTFOLIO_IMAGES = PORTFOLIO_ROOT / "images"
VT_LOGOS = Path.home() / "clawd" / "vt-logos"
TOOL_DIR = Path(__file__).parent

# Supported image extensions
IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.svg', '.gif'}


def scan_logos() -> List[Dict[str, Any]]:
    """Scan for all logo files in portfolio/images and vt-logos directories."""
    logos = []
    
    # Scan portfolio/images
    if PORTFOLIO_IMAGES.exists():
        for file_path in PORTFOLIO_IMAGES.iterdir():
            if file_path.suffix.lower() in IMAGE_EXTS:
                logos.append({
                    'name': file_path.stem.replace('-', ' ').title(),
                    'path': str(file_path),
                    'relative_path': f"portfolio/images/{file_path.name}",
                    'type': 'portfolio',
                    'filename': file_path.name
                })
    
    # Scan vt-logos
    if VT_LOGOS.exists():
        for file_path in VT_LOGOS.iterdir():
            if file_path.suffix.lower() in IMAGE_EXTS:
                logos.append({
                    'name': file_path.stem.replace('-', ' ').title(),
                    'path': str(file_path),
                    'relative_path': f"vt-logos/{file_path.name}",
                    'type': 'vt-logos',
                    'filename': file_path.name
                })
    
    return logos


def create_logo_preview_html(logos: List[Dict[str, Any]]) -> str:
    """Create an HTML preview page with all logos."""
    # Read the template
    template_path = TOOL_DIR / "logo_preview.html"
    if template_path.exists():
        with open(template_path, 'r') as f:
            html = f.read()
        
        # Replace the static logo list with dynamic one
        logos_json = json.dumps(logos, indent=2)
        html = html.replace('// Sample logo data', f'const logos = {logos_json};')
        return html
    else:
        # Fallback basic HTML
        return create_fallback_html(logos)


def create_fallback_html(logos: List[Dict[str, Any]]) -> str:
    """Create a simple HTML page if template doesn't exist."""
    items = []
    for logo in logos:
        items.append(f"""
        <div style="border: 1px solid #ccc; padding: 10px; margin: 10px;">
            <h3>{logo['name']}</h3>
            <p><strong>Path:</strong> {logo['relative_path']}</p>
            <p><strong>Type:</strong> {logo['type']}</p>
            <img src="{logo['relative_path']}" alt="{logo['name']}" style="max-width: 200px; max-height: 100px;">
            <div>
                <button onclick="alert('Would copy {logo['filename']} to portfolio')">Apply to Portfolio</button>
            </div>
        </div>
        """)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logo Preview</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            h1 {{ color: #333; }}
            .logo-container {{ display: flex; flex-wrap: wrap; }}
        </style>
    </head>
    <body>
        <h1>Portfolio Logo Preview</h1>
        <p>Found {len(logos)} logo files.</p>
        <div class="logo-container">
            {''.join(items)}
        </div>
    </body>
    </html>
    """


def copy_logo_to_portfolio(src_path: str, target_name: str = None) -> bool:
    """
    Copy a logo file to the portfolio images directory.
    
    Args:
        src_path: Source logo file path
        target_name: Optional target filename (default: keep original name)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        src = Path(src_path)
        if not src.exists():
            print(f"Error: Source file not found: {src_path}")
            return False
        
        if target_name:
            dst = PORTFOLIO_IMAGES / target_name
        else:
            dst = PORTFOLIO_IMAGES / src.name
        
        # Ensure destination directory exists
        PORTFOLIO_IMAGES.mkdir(exist_ok=True)
        
        # Copy the file
        shutil.copy2(src, dst)
        print(f"Copied {src.name} to {dst}")
        return True
        
    except Exception as e:
        print(f"Error copying logo: {e}")
        return False


def start_preview_server(port: int = 8080):
    """Start a simple HTTP server to serve the preview page."""
    logos = scan_logos()
    html = create_logo_preview_html(logos)
    
    # Write temporary HTML file
    temp_html = TOOL_DIR / "preview_temp.html"
    with open(temp_html, 'w') as f:
        f.write(html)
    
    print(f"Found {len(logos)} logo files")
    print(f"Starting preview server on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    # Change to tool directory to serve files
    os.chdir(TOOL_DIR)
    
    # Custom handler to serve our HTML
    class LogoHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(html.encode())
            else:
                # Serve other files (like images) normally
                super().do_GET()
    
    # Start server
    try:
        with socketserver.TCPServer(("", port), LogoHandler) as httpd:
            print(f"Server started at http://localhost:{port}")
            print("Opening browser...")
            webbrowser.open(f"http://localhost:{port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error starting server: {e}")


def show_logo_list():
    """Print a list of all found logos."""
    logos = scan_logos()
    
    print(f"Found {len(logos)} logo files:\n")
    
    for i, logo in enumerate(logos, 1):
        print(f"{i:2}. {logo['name']}")
        print(f"    Path: {logo['relative_path']}")
        print(f"    Type: {logo['type']}")
        print()


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Portfolio Logo Tool - Preview and apply logos for VT Sports Solutions portfolio"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all available logos')
    
    # Preview command
    preview_parser = subparsers.add_parser('preview', help='Start web preview server')
    preview_parser.add_argument('--port', type=int, default=8080, help='Port for preview server')
    
    # Apply command
    apply_parser = subparsers.add_parser('apply', help='Apply a logo to the portfolio')
    apply_parser.add_argument('source', help='Source logo file path or index from list')
    apply_parser.add_argument('--target', help='Target filename in portfolio/images/')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        show_logo_list()
    
    elif args.command == 'preview':
        start_preview_server(args.port)
    
    elif args.command == 'apply':
        # Check if source is a number (index from list)
        logos = scan_logos()
        try:
            index = int(args.source) - 1
            if 0 <= index < len(logos):
                src_path = logos[index]['path']
            else:
                print(f"Error: Index {args.source} out of range (1-{len(logos)})")
                return
        except ValueError:
            # Treat as file path
            src_path = args.source
        
        if copy_logo_to_portfolio(src_path, args.target):
            print("Logo copied successfully!")
            print(f"Open ~/clawd/portfolio/index.html to see it in context.")
        else:
            print("Failed to copy logo")
    
    else:
        # No command specified, show help
        parser.print_help()
        print("\nExamples:")
        print("  python logo_tool.py list                    # List all logos")
        print("  python logo_tool.py preview                 # Start web preview")
        print("  python logo_tool.py apply vt-logos/logo-color.png  # Copy a logo")
        print("  python logo_tool.py apply 1                 # Apply logo #1 from list")


if __name__ == "__main__":
    main()