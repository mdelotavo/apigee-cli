#!/usr/bin/env bash
set -e

# Directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Project root is one level up from the tools repo
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Clean up .pyc files
find . -name "*.pyc" -delete

# Run tests with coverage
coverage run -p --source=tests,apigee -m pytest -s

if [ "$?" -eq 0 ]; then
    coverage combine

    echo -e "\n\n================================================"
    echo "Test Coverage"
    coverage report
    echo -e "\nrun \"coverage html\" for full report\n"
fi