#!/bin/sh
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOKS_SRC="$SCRIPT_DIR/hooks"
HOOKS_DST="$SCRIPT_DIR/../.git/hooks"

for hook in "$HOOKS_SRC"/*; do
  name=$(basename "$hook")
  dst="$HOOKS_DST/$name"
  cp "$hook" "$dst"
  chmod +x "$dst"
  echo "Installed: .git/hooks/$name"
done

echo "Done. Git hooks are active for this repo."
