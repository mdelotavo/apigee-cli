#!/usr/bin/env bash
set -e

# Resolve the directory where this script lives (handles symlinks too)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Option 1: Assume script sits in repo root
cd "$SCRIPT_DIR"

# If the script is *not* in root, adjust like:
# cd "$SCRIPT_DIR/.."   # example: script is in /scripts

# Clean up .pyc files
find . -name "*.pyc" -delete

# Run tests with coverage
coverage run -p --source=tests,apigee -m pytest -s

# If successful
if [ "$?" -eq 0 ]; then
    coverage combine

    echo -e "\n\n================================================"
    echo "Test Coverage"
    coverage report
    echo -e "\nrun \"coverage html\" for full report\n"

    # lint step could go here
fi