#!/usr/bin/env bash
# HashMate launcher (Linux / macOS)
# Usage:          chmod +x scripts/run.sh && ./scripts/run.sh
# Install desktop: ./scripts/run.sh --install-desktop

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# ---------- Install desktop entry ----------
if [[ "${1:-}" == "--install-desktop" ]]; then
    ICON_SRC="$PROJECT_ROOT/assets/logo.png"
    ICON_DST="$HOME/.local/share/icons/hashmate.png"
    DESKTOP_FILE="$HOME/.local/share/applications/hashmate.desktop"

    mkdir -p "$HOME/.local/share/icons" "$HOME/.local/share/applications"

    if [[ -f "$ICON_SRC" ]]; then
        cp "$ICON_SRC" "$ICON_DST"
        echo "Icon installed: $ICON_DST"
    fi

    cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=HashMate
Comment=File hash verification tool
Exec=$PROJECT_ROOT/scripts/run.sh
Icon=$ICON_DST
Terminal=false
Categories=Utility;Security;
EOF

    chmod +x "$DESKTOP_FILE"
    echo "Desktop entry created: $DESKTOP_FILE"
    echo "You can now find HashMate in your application launcher."
    exit 0
fi

# ---------- Normal launch ----------
if ! command -v uv >/dev/null 2>&1; then
    echo "[ERROR] uv not found. Install: https://docs.astral.sh/uv/" >&2
    exit 1
fi

echo "Syncing dependencies (uv sync)..."
uv sync

echo "Starting HashMate..."
exec uv run hashmate
