#!/bin/bash
# Demo GIF recording script for README
# Prerequisites: pip install asciinema && brew install agg
#
# Usage:
#   1. pip install -e .
#   2. bash scripts/record_demo.sh
#   3. Move docs/demo.gif to repo root or docs/
#
# If you don't have agg, use https://asciinema.org to record and convert online.

set -e

CAST_FILE="docs/demo.cast"
GIF_FILE="docs/demo.gif"

mkdir -p docs

echo "Recording demo..."

# Record with asciinema (auto-play scripted commands)
asciinema rec "$CAST_FILE" --command '
echo "$ llm-medical-guard check -v \"Take 50000 IU of vitamin D daily to cure your depression. This miracle supplement has no side effects!\""
sleep 1
llm-medical-guard check -v "Take 50000 IU of vitamin D daily to cure your depression. This miracle supplement has no side effects!"
sleep 3

echo ""
echo "$ llm-medical-guard check --json \"Vitamin D supports bone health. Consult your doctor for proper dosage. Source: NIH\""
sleep 1
llm-medical-guard check --json "Vitamin D supports bone health. Consult your doctor for proper dosage. Source: NIH"
sleep 3

echo ""
echo "$ llm-medical-guard bench -n 5000"
sleep 1
llm-medical-guard bench -n 5000
sleep 2
' --overwrite

echo "Converting to GIF..."
agg "$CAST_FILE" "$GIF_FILE" --cols 100 --rows 30 --speed 1.5 --theme monokai

echo "Done! GIF saved to $GIF_FILE"
echo "File size: $(du -h "$GIF_FILE" | cut -f1)"
