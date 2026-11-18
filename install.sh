#!/usr/bin/env bash

# Installer for steam-auto-profiler.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.local/bin"
WITH_NET_BOOST=0
UNINSTALL=0

for arg in "$@"; do
    case "$arg" in
        --with-net-boost)
            WITH_NET_BOOST=1
            ;;
        --uninstall)
        UNINSTALL=1
        ;;
        --help|-h)
            echo "Usage: ./install.sh [--with-net-boost | --uninstall]"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 2
            ;;
    esac
done

if [[ "$UNINSTALL" -eq 1 ]]; then
    for script in steam-auto-run steam-auto-detect steam-auto-sync steam-net-boost; do
        rm -f "$TARGET_DIR/$script"
        echo "Removed $TARGET_DIR/$script"
    done
    if [[ -e "/usr/local/bin/steam-net-boost" ]]; then
        sudo rm -f /usr/local/bin/steam-net-boost
        echo "Removed /usr/local/bin/steam-net-boost"
    fi
    if [[ -e "/etc/sudoers.d/steam-net-boost" ]]; then
        sudo rm -f /etc/sudoers.d/steam-net-boost
        echo "Removed /etc/sudoers.d/steam-net-boost"
    fi
    echo "Steam Auto-Profiler uninstalled."
    exit 0
fi

mkdir -p "$TARGET_DIR" "${XDG_CONFIG_HOME:-$HOME/.config}/steam-auto-profiler/profiles"
VK_BASALT_PRESET_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/vkBasalt/presets"
mkdir -p "$VK_BASALT_PRESET_DIR"

if [[ ! -e "$VK_BASALT_PRESET_DIR/competitive.conf" ]]; then
    cat >"$VK_BASALT_PRESET_DIR/competitive.conf" <<'EOF'
# Safe competitive preset: low-cost contrast sharpening only.
effects = cas
casSharpness = 0.35
EOF
fi
if [[ ! -e "$VK_BASALT_PRESET_DIR/standard.conf" ]]; then
    cat >"$VK_BASALT_PRESET_DIR/standard.conf" <<'EOF'
# Balanced built-in vkBasalt preset.
effects = cas:dls
casSharpness = 0.55
dlsSharpness = 0.35
dlsDenoise = 0.15
EOF
fi
if [[ ! -e "$VK_BASALT_PRESET_DIR/vivid.conf" ]]; then
    cat >"$VK_BASALT_PRESET_DIR/vivid.conf" <<'EOF'
# Vivid built-in vkBasalt preset.
effects = cas:dls:deband
casSharpness = 0.75
dlsSharpness = 0.45
dlsDenoise = 0.25
debandIterations = 2
EOF
fi

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
