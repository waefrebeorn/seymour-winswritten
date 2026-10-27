#!/bin/bash
# waefrebeorn repo setup script
# Run this in a new repo to apply the correct dual-license setup

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(pwd)"

echo "=== Waefrebeorn Dual-License Setup ==="
echo ""

# Check if LICENSE exists
if [ ! -f "LICENSE" ]; then
    echo "Adding Unlicense (original absorbed code)..."
    echo "See LICENSE.waefrebeorn for waefrebeorn code additions."
else
    echo "LICENSE file already exists (absorbed code)."
fi

# Check if LICENSE.waefrebeorn exists
if [ ! -f "LICENSE.waefrebeorn" ]; then
    echo "Adding Waefrebeorn Umbrella License for new additions..."
    # Copy from template
    cp "${SCRIPT_DIR}/LICENSE.waefrebeorn" "LICENSE.waefrebeorn" 2>/dev/null ||     curl -sL -o LICENSE.waefrebeorn       "https://raw.githubusercontent.com/waefrebeorn/waefrebeorn/master/LICENSE.template" ||     echo "WARNING: Could not copy LICENSE.waefrebeorn template"
else
    echo "LICENSE.waefrebeorn already exists."
fi

# Check README
if [ -f "README.md" ]; then
    if ! grep -q "Waefrebeorn Umbrella License" README.md; then
        echo "Adding Waefrebeorn license disclosure to README..."
        echo "" >> README.md
        echo "---" >> README.md
        echo "" >> README.md
        echo "## License" >> README.md
        echo "" >> README.md
        echo "Original absorbed code remains under its original license (see [LICENSE](LICENSE))." >> README.md
        echo "" >> README.md
        echo "All waefrebeorn modifications, extensions, and new code fall under the" >> README.md
        echo "**Waefrebeorn Umbrella License v3.0**. See [LICENSE.waefrebeorn](LICENSE.waefrebeorn) for the full license text." >> README.md
        echo "" >> README.md
        echo "The Waefrebeorn Umbrella License is a custom source-available license." >> README.md
        echo "It is not OSI-approved and not FSF-approved." >> README.md
    else
        echo "README.md already has Waefrebeorn disclosure."
    fi
else
    echo "No README.md found. Please create one with license disclosure."
fi

echo ""
echo "Setup complete. Commit your changes:"
echo "  git add LICENSE LICENSE.waefrebeorn README.md"
echo "  git commit -m 'Apply Waefrebeorn dual-license setup'"
echo "  git push"
