#!/bin/bash
# Schedule Parser CLI - macOS/Linux
# Usage: ./scripts/run_cli.sh

cd "$(dirname "$0")/.."
python schedule_parser.py "$@"
