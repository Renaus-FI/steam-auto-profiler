#!/usr/bin/env bash

# Installer for steam-auto-profiler.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.local/bin"
WITH_NET_BOOST=0

for arg in "$@"; do
    case "$arg" in
        --with-net-boost)
            WITH_NET_BOOST=1
            ;;
        --help|-h)
            echo "Usage: ./install.sh [--with-net-boost]"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 2
            ;;
    esac
done

mkdir -p "$TARGET_DIR" "${XDG_CONFIG_HOME:-$HOME/.config}/steam-auto-profiler/profiles"

for script in steam-auto-run steam-auto-detect steam-auto-sync steam-net-boost; do
    install -m 755 "$REPO_DIR/bin/$script" "$TARGET_DIR/$script"
    echo "Installed $TARGET_DIR/$script"
done

if [[ "$WITH_NET_BOOST" -eq 1 ]]; then
    USER_NAME="$(id -un)"
    TMP_SUDOERS="$(mktemp)"
    printf '%s ALL=(root) NOPASSWD: /usr/local/bin/steam-net-boost\n' "$USER_NAME" >"$TMP_SUDOERS"
    sudo install -m 755 "$REPO_DIR/bin/steam-net-boost" /usr/local/bin/steam-net-boost
    sudo install -m 440 "$TMP_SUDOERS" /etc/sudoers.d/steam-net-boost
    sudo visudo -cf /etc/sudoers.d/steam-net-boost
    rm -f "$TMP_SUDOERS"
    echo "Installed optional network helper and sudoers rule"
fi

echo "Done! Test with: $TARGET_DIR/steam-auto-run --help"
