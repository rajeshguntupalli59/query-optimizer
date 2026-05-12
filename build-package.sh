#!/usr/bin/env bash
# build-package.sh — Build a clean client delivery ZIP
# Usage: chmod +x build-package.sh && ./build-package.sh

set -euo pipefail

VERSION="1.0"
NAME="queryoptimizer-v${VERSION}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/dist"
STAGING="$OUT/$NAME"
ZIP_PATH="$OUT/$NAME.zip"

echo "Building $NAME.zip ..."

rm -rf "$STAGING"
rm -f  "$ZIP_PATH"
mkdir -p "$STAGING"

# Files and directories to include
INCLUDE=(
    "backend"
    "frontend"
    "docs"
    "docker-compose.yml"
    ".env.example"
    "setup.ps1"
    "setup.sh"
    "README.md"
    "CHANGELOG.md"
    "LICENSE"
)

for item in "${INCLUDE[@]}"; do
    src="$ROOT/$item"
    if [ ! -e "$src" ]; then
        echo "  Skipping (not found): $item"
        continue
    fi
    dst="$STAGING/$item"
    if [ -d "$src" ]; then
        cp -r "$src" "$dst"
    else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
    fi
done

# Remove excluded items from the staging tree
EXCLUDE_PATTERNS=(
    ".venv"
    "__pycache__"
    "*.pyc"
    "node_modules"
    ".git"
    "dist"
    "build"
    ".claude"
    "*.log"
    ".secret_key"
    "queryoptimizer.db"
    "tools"          # seller-only keygen scripts
)

for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    find "$STAGING" -name "$pattern" -exec rm -rf {} + 2>/dev/null || true
done

# Create empty data/ placeholder
mkdir -p "$STAGING/data"
touch "$STAGING/data/.gitkeep"

# Zip
(cd "$OUT" && zip -r "$ZIP_PATH" "$NAME")

SIZE=$(du -sh "$ZIP_PATH" | cut -f1)
echo ""
echo "Done: $ZIP_PATH ($SIZE)"
echo ""
echo "Contents:"
ls "$STAGING"
echo ""
echo "Deliver $NAME.zip to the client."
