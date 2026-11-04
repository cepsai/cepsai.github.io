#!/bin/sh
# Fetches the same inputs the live leaderboard page loads (scripts/lb-config.js + data-loader.js).
# Data from Firebase RTDB, config from the GitHub Pages site (configBase '.').
set -e
DIR="${1:-$(dirname "$0")/raw}"
mkdir -p "$DIR"
RTDB=https://ai-model-leaderboard-default-rtdb.europe-west1.firebasedatabase.app
SITE=https://aileaderboard.franri.dev
for f in processed history sources; do curl -fsS -o "$DIR/$f.json" "$RTDB/$f.json"; done
for f in models tracking; do curl -fsSL -o "$DIR/$f.json" "$SITE/config/$f.json"; done
