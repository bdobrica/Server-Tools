#!/bin/bash
# Development setup script for site-builder

set -e

echo "Setting up site-builder for development..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: pyproject.toml not found. Please run this script from the site-builder directory."
    exit 1
fi

# Install in development mode
echo "Installing site-builder in development mode..."
pip3 install -e .

# Test the installation
echo "Testing installation..."
if command -v site-builder &> /dev/null; then
    echo "✅ site-builder command is available"
    site-builder --help | head -5
else
    echo "❌ site-builder command not found in PATH"
    exit 1
fi

echo ""
echo "✅ Development setup complete!"
echo ""
echo "You can now use:"
echo "  site-builder --help          # Show help"
echo "  site-builder --web-path /var/www  # Run with custom web path"
echo ""
echo "To build a distributable package:"
echo "  python3 -m build"
echo ""
echo "To upload to PyPI:"
echo "  python3 -m twine upload dist/*"
