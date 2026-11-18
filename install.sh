#!/usr/bin/env bash

# Installer for steam-auto-profiler.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.local/bin"
WITH_NET_BOOST=0
COMPAT_CACHY_RUN=0
WITH_AUTO_SYNC=0
UNINSTALL=0

for arg in "$@"; do
    case "$arg" in
        --with-net-boost)
            WITH_NET_BOOST=1
            ;;
        --compat-cachy-run)
            COMPAT_CACHY_RUN=1
            ;;
        --with-auto-sync|--enable-auto-sync)
            WITH_AUTO_SYNC=1
            ;;
        --uninstall)
            UNINSTALL=1
            ;;
        --help|-h)
            echo "Usage: ./install.sh [--with-net-boost] [--compat-cachy-run] [--with-auto-sync] [--uninstall]"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 2
            ;;
    esac
done

if [[ "$UNINSTALL" -eq 1 ]]; then
    SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    if command -v systemctl >/dev/null 2>&1; then
        systemctl --user disable --now steam-auto-profiler-sync.path 2>/dev/null || true
    fi
    rm -f "$SYSTEMD_USER_DIR/steam-auto-profiler-sync.path" \
        "$SYSTEMD_USER_DIR/steam-auto-profiler-sync.service"
    if command -v systemctl >/dev/null 2>&1; then
        systemctl --user daemon-reload 2>/dev/null || true
    fi
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
    for script in steam-auto-run steam-auto-detect steam-auto-sync; do
        if [[ -e "/usr/local/bin/$script" || -L "/usr/local/bin/$script" ]]; then
            sudo rm -f "/usr/local/bin/$script"
            echo "Removed /usr/local/bin/$script"
        fi
    done
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
if [[ ! -e "$VK_BASALT_PRESET_DIR/shooter.conf" ]]; then
    cat >"$VK_BASALT_PRESET_DIR/shooter.conf" <<'EOF'
# Safe shooter preset: low-latency competitive sharpening.
effects = cas
casSharpness = 0.40
EOF
fi
if [[ ! -e "$VK_BASALT_PRESET_DIR/oled-clean.conf" ]]; then
    cat >"$VK_BASALT_PRESET_DIR/oled-clean.conf" <<'EOF'
# OLED-clean preset: restrained contrast and color cleanup.
effects = cas:dls
casSharpness = 0.45
dlsSharpness = 0.25
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
    sudo rm -f /etc/sudoers.d/cachy-net-boost /usr/local/bin/cachy-net-boost
    for script in steam-auto-run steam-auto-detect steam-auto-sync; do
        sudo install -m 755 "$REPO_DIR/bin/$script" "/usr/local/bin/$script"
        echo "Installed /usr/local/bin/$script"
    done
    sudo install -m 755 "$REPO_DIR/bin/steam-net-boost" /usr/local/bin/steam-net-boost
    sudo install -m 440 "$TMP_SUDOERS" /etc/sudoers.d/steam-net-boost
    sudo visudo -cf /etc/sudoers.d/steam-net-boost
    rm -f "$TMP_SUDOERS"
    echo "Installed optional network helper and sudoers rule"
fi

if [[ "$COMPAT_CACHY_RUN" -eq 1 ]]; then
    if [[ -e "/usr/local/bin/cachy-run" || -L "/usr/local/bin/cachy-run" ]]; then
        if ! grep -Fq 'steam-auto-run' /usr/local/bin/cachy-run 2>/dev/null; then
            if [[ ! -e "/usr/local/bin/cachy-run.bak" ]]; then
                sudo cp -p /usr/local/bin/cachy-run /usr/local/bin/cachy-run.bak
                echo "Preserved existing cachy-run at /usr/local/bin/cachy-run.bak"
            else
                echo "Preserved existing cachy-run; /usr/local/bin/cachy-run.bak already exists"
            fi
        fi
    fi
    TMP_CACHY_RUN="$(mktemp)"
    cat >"$TMP_CACHY_RUN" <<'EOF'
#!/usr/bin/env bash
exec steam-auto-run "$@"
EOF
    sudo install -m 755 "$TMP_CACHY_RUN" /usr/local/bin/cachy-run
    rm -f "$TMP_CACHY_RUN"
    echo "Installed /usr/local/bin/cachy-run compatibility shim"
fi

if [[ "$WITH_AUTO_SYNC" -eq 1 ]]; then
    SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
    mkdir -p "$SYSTEMD_USER_DIR"
    cat >"$SYSTEMD_USER_DIR/steam-auto-profiler-sync.service" <<EOF
[Unit]
Description=Synchronize Steam launch options with Steam Auto-Profiler

[Service]
Type=oneshot
ExecStart=$TARGET_DIR/steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300
EOF
    cat >"$SYSTEMD_USER_DIR/steam-auto-profiler-sync.path" <<'EOF'
[Unit]
Description=Watch Steam app manifests for new games

[Path]
PathChanged=%h/.local/share/Steam/steamapps
Unit=steam-auto-profiler-sync.service

[Install]
WantedBy=default.target
EOF
    if command -v systemctl >/dev/null 2>&1 &&
       systemctl --user daemon-reload 2>/dev/null &&
       systemctl --user enable --now steam-auto-profiler-sync.path 2>/dev/null; then
        echo "Enabled systemd user auto-sync watcher"
    else
        echo "Installed systemd user auto-sync units (user session unavailable; enable manually)."
    fi
fi

echo "Done! Test with: $TARGET_DIR/steam-auto-run --help"
