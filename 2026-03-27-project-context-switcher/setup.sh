#!/bin/bash
# Setup script for Project Context Switcher

set -e

echo "🔧 Setting up Project Context Switcher"

# Make script executable
chmod +x context_switcher.py

# Create symlink for easy access
if [ ! -f /usr/local/bin/pctx ]; then
    echo "Creating symlink: /usr/local/bin/pctx"
    sudo ln -sf "$(pwd)/context_switcher.py" /usr/local/bin/pctx
else
    echo "Symlink /usr/local/bin/pctx already exists"
fi

# Check for PyYAML
echo "Checking dependencies..."
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    pip3 install pyyaml
else
    echo "PyYAML already installed"
fi

# Create initial config if it doesn't exist
CONFIG_FILE="$HOME/.project_contexts.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating initial configuration at $CONFIG_FILE"
    cp sample-config.yaml "$CONFIG_FILE"
    echo "✅ Initial configuration created. Edit $CONFIG_FILE to customize."
else
    echo "Configuration already exists at $CONFIG_FILE"
fi

# Run verification
echo ""
echo "Running verification tests..."
if python3 verify.py; then
    echo ""
    echo "🎉 Setup complete!"
    echo ""
    echo "Usage:"
    echo "  pctx list                 # List available projects"
    echo "  pctx activate <name>      # Activate a project"
    echo "  pctx status               # Show current status"
    echo "  pctx deactivate           # Deactivate current project"
    echo "  pctx add                  # Add new project interactively"
    echo ""
    echo "Quick test:"
    echo "  pctx list"
else
    echo ""
    echo "⚠️ Verification failed. Check the errors above."
    exit 1
fi