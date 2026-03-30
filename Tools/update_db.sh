#!/bin/bash
# Syncs ai_funding_tracker.db from Dropbox to the repo and pushes to GitHub Pages.
# Run this whenever the database updates.

set -e

DB_SRC="/Users/robertpraas/CEPS-DST Dropbox/Robert Praas/Funding_Trackers/AI_Work/ai_funding_tracker.db"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_DEST="$REPO_DIR/Tools/ai_funding_tracker.db"

echo "Copying database from Dropbox..."
cp "$DB_SRC" "$DB_DEST"

echo "Committing and pushing..."
cd "$REPO_DIR"
git add Tools/ai_funding_tracker.db
git commit -m "update: AI funding tracker database $(date '+%Y-%m-%d %H:%M')"
git push

echo "Done. GitHub Pages will update in ~1 minute."
