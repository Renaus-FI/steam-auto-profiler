#!/usr/bin/env bash

# Installer for steam-auto-profiler.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.local/bin"
APPLICATIONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
SYSTEM_BIN_DIR="${STEAM_AUTO_PROFILER_SYSTEM_BIN_DIR:-/usr/local/bin}"
SUDOERS_DIR="${STEAM_AUTO_PROFILER_SUDOERS_DIR:-/etc/sudoers.d}"
UDEV_RULES_DIR="${STEAM_AUTO_PROFILER_UDEV_DIR:-/etc/udev/rules.d}"
PACMAN_HOOKS_DIR="${STEAM_AUTO_PROFILER_PACMAN_HOOKS_DIR:-/etc/pacman.d/hooks}"
WITH_NET_BOOST=0
COMPAT_CACHY_RUN=0
WITH_AUTO_SYNC=0
WITH_STEAM_CONTROLLER=0
WITH_MESA_HOOK=0
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
        --with-steam-controller)
            WITH_STEAM_CONTROLLER=1
            ;;
        --with-mesa-hook)
            WITH_MESA_HOOK=1
            ;;
        --uninstall)
            UNINSTALL=1
            ;;
        --help|-h)
            echo "Usage: ./install.sh [--with-net-boost] [--compat-cachy-run] [--with-auto-sync] [--with-steam-controller] [--with-mesa-hook] [--uninstall]"
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
    for script in steam-auto-run steam-auto-detect steam-auto-sync steam-net-boost vr-run steam-auto-ui steam-auto-clean-shaders; do
        rm -f "$TARGET_DIR/$script"
        echo "Removed $TARGET_DIR/$script"
    done
    if [[ -e "$APPLICATIONS_DIR/steam-auto-profiler.desktop" ]]; then
        rm -f "$APPLICATIONS_DIR/steam-auto-profiler.desktop"
        echo "Removed $APPLICATIONS_DIR/steam-auto-profiler.desktop"
    fi
    if [[ -e "$SYSTEM_BIN_DIR/steam-net-boost" ]]; then
        sudo rm -f "$SYSTEM_BIN_DIR/steam-net-boost"
        echo "Removed $SYSTEM_BIN_DIR/steam-net-boost"
    fi
    if [[ -e "$SUDOERS_DIR/steam-net-boost" ]]; then
        sudo rm -f "$SUDOERS_DIR/steam-net-boost"
        echo "Removed $SUDOERS_DIR/steam-net-boost"
    fi
    if [[ -e "$UDEV_RULES_DIR/61-steam-controller-2026.rules" ]]; then
        if [[ -n "${STEAM_AUTO_PROFILER_UDEV_DIR:-}" ]]; then
            rm -f "$UDEV_RULES_DIR/61-steam-controller-2026.rules"
        else
            sudo rm -f "$UDEV_RULES_DIR/61-steam-controller-2026.rules"
            if command -v udevadm >/dev/null 2>&1; then
                sudo udevadm control --reload-rules 2>/dev/null || true
            fi
        fi
        echo "Removed $UDEV_RULES_DIR/61-steam-controller-2026.rules"
    fi
    if [[ -e "$PACMAN_HOOKS_DIR/95-steam-auto-profiler-mesa-shaders.hook" ]]; then
        if [[ -n "${STEAM_AUTO_PROFILER_PACMAN_HOOKS_DIR:-}" ]]; then
            rm -f "$PACMAN_HOOKS_DIR/95-steam-auto-profiler-mesa-shaders.hook"
        else
            sudo rm -f "$PACMAN_HOOKS_DIR/95-steam-auto-profiler-mesa-shaders.hook"
        fi
        echo "Removed $PACMAN_HOOKS_DIR/95-steam-auto-profiler-mesa-shaders.hook"
    fi
    for script in steam-auto-run steam-auto-detect steam-auto-sync vr-run steam-auto-ui steam-auto-clean-shaders; do
        if [[ -e "$SYSTEM_BIN_DIR/$script" || -L "$SYSTEM_BIN_DIR/$script" ]]; then
            if [[ -n "${STEAM_AUTO_PROFILER_SYSTEM_BIN_DIR:-}" ]]; then
                rm -f "$SYSTEM_BIN_DIR/$script"
            else
                sudo rm -f "$SYSTEM_BIN_DIR/$script"
            fi
            echo "Removed $SYSTEM_BIN_DIR/$script"
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

for script in steam-auto-run steam-auto-detect steam-auto-sync steam-net-boost vr-run steam-auto-ui steam-auto-clean-shaders; do
    install -m 755 "$REPO_DIR/bin/$script" "$TARGET_DIR/$script"
    echo "Installed $TARGET_DIR/$script"
done

mkdir -p "$APPLICATIONS_DIR"
cat >"$APPLICATIONS_DIR/steam-auto-profiler.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Steam Auto-Profiler
GenericName=Steam Gaming Control Center
Comment=Manage Steam Auto-Profiler per-game profiles, VR mode, network QoS, and crash recovery
Exec=$TARGET_DIR/steam-auto-ui --gui
Icon=steam
Terminal=false
Categories=Game;Settings;System;Utility;
Keywords=Steam;Proton;FSR4;Wayland;VR;Gaming;
StartupNotify=true
EOF
echo "Installed $APPLICATIONS_DIR/steam-auto-profiler.desktop"

if [[ "$WITH_NET_BOOST" -eq 1 ]]; then
    USER_NAME="$(id -un)"
    sudo rm -f "$SUDOERS_DIR/cachy-net-boost" "$SYSTEM_BIN_DIR/cachy-net-boost"
    for script in steam-auto-run steam-auto-detect steam-auto-sync vr-run steam-auto-ui steam-auto-clean-shaders; do
        sudo install -m 755 "$REPO_DIR/bin/$script" "$SYSTEM_BIN_DIR/$script"
        echo "Installed $SYSTEM_BIN_DIR/$script"
    done
    sudo install -m 755 "$REPO_DIR/bin/steam-net-boost" "$SYSTEM_BIN_DIR/steam-net-boost"
    printf '%s ALL=(root) NOPASSWD: %s/steam-net-boost\n' "$USER_NAME" "$SYSTEM_BIN_DIR" |
        sudo tee "$SUDOERS_DIR/steam-net-boost" >/dev/null
    sudo chmod 440 "$SUDOERS_DIR/steam-net-boost"
    sudo visudo -cf "$SUDOERS_DIR/steam-net-boost"
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
    sudo tee /usr/local/bin/cachy-run >/dev/null <<'EOF'
#!/usr/bin/env bash
exec steam-auto-run "$@"
EOF
    sudo chmod 755 /usr/local/bin/cachy-run
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
    LIBRARY_PATHS=()
    while IFS= read -r library; do
        [[ -n "$library" ]] && LIBRARY_PATHS+=("$library")
    done < <(HOME="$HOME" python3 "$REPO_DIR/bin/steam-auto-sync" --print-library-paths 2>/dev/null || true)
    if ((${#LIBRARY_PATHS[@]} == 0)); then
        LIBRARY_PATHS+=("$HOME/.local/share/Steam")
    fi
    {
        cat <<'EOF'
[Unit]
Description=Watch Steam app manifests for new games

[Path]
EOF
        for library in "${LIBRARY_PATHS[@]}"; do
            printf 'PathChanged=%s/steamapps\n' "$library"
        done
        cat <<'EOF'
Unit=steam-auto-profiler-sync.service

[Install]
WantedBy=default.target
EOF
    } >"$SYSTEMD_USER_DIR/steam-auto-profiler-sync.path"
    if command -v systemctl >/dev/null 2>&1 &&
       systemctl --user daemon-reload 2>/dev/null &&
       systemctl --user enable --now steam-auto-profiler-sync.path 2>/dev/null; then
        echo "Enabled systemd user auto-sync watcher"
    else
        echo "Installed systemd user auto-sync units (user session unavailable; enable manually)."
    fi
fi

if [[ "$WITH_STEAM_CONTROLLER" -eq 1 ]]; then
    UDEV_RULE_FILE="$UDEV_RULES_DIR/61-steam-controller-2026.rules"
    UDEV_CONTENT='# Steam Controller (2026, Triton/Proteus) & Wireless Steam Puck (28de:{1302,1304,1005,1007})
# Installed by steam-auto-profiler (--with-steam-controller)

# USB permissions, ModemManager ignore, and disable USB selective suspend for zero wireless wake-up latency
ACTION=="add|change", SUBSYSTEM=="usb", ATTR{idVendor}=="28de", ATTR{idProduct}=="1302|1304|1005|1007", MODE="0660", GROUP="uucp", TAG+="uaccess", ENV{ID_MM_DEVICE_IGNORE}="1", TEST=="power/control", ATTR{power/control}="on", TEST=="power/autosuspend", ATTR{power/autosuspend}="-1"

# HIDRAW access for Steam Input (USB, 2.4 GHz Steam Puck, and BLE)
KERNEL=="hidraw*", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1302|1304|1005|1007", MODE="0660", GROUP="uucp", TAG+="uaccess"
KERNEL=="hidraw*", KERNELS=="*28DE:1302*|*28DE:1304*|*28DE:1005*|*28DE:1007*", MODE="0660", GROUP="uucp", TAG+="uaccess"

# Serial bootloader / firmware update ports (ttyACM*): grant uucp/uaccess and block ModemManager probing
SUBSYSTEM=="tty", KERNEL=="ttyACM*", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1302|1304|1005|1007", MODE="0660", GROUP="uucp", TAG+="uaccess", ENV{ID_MM_DEVICE_IGNORE}="1"'
    if [[ -n "${STEAM_AUTO_PROFILER_UDEV_DIR:-}" ]]; then
        mkdir -p "$UDEV_RULES_DIR"
        printf '%s\n' "$UDEV_CONTENT" >"$UDEV_RULE_FILE"
        chmod 644 "$UDEV_RULE_FILE"
    else
        sudo mkdir -p "$UDEV_RULES_DIR"
        printf '%s\n' "$UDEV_CONTENT" | sudo tee "$UDEV_RULE_FILE" >/dev/null
        sudo chmod 644 "$UDEV_RULE_FILE"
        if command -v udevadm >/dev/null 2>&1; then
            sudo udevadm control --reload-rules 2>/dev/null || true
            sudo udevadm trigger --attr-match=idVendor=28de 2>/dev/null || true
        fi
    fi
    echo "Installed Steam Controller 2026 udev rules at $UDEV_RULE_FILE"
fi

if [[ "$WITH_MESA_HOOK" -eq 1 ]]; then
    MESA_HOOK_FILE="$PACMAN_HOOKS_DIR/95-steam-auto-profiler-mesa-shaders.hook"
    MESA_HOOK_CONTENT="[Trigger]
Operation = Upgrade
Type = Package
Target = mesa
Target = mesa-git
Target = lib32-mesa
Target = lib32-mesa-git

[Action]
Description = Cleaning Mesa/RADV shader caches via steam-auto-clean-shaders...
When = PostTransaction
Exec = ${SYSTEM_BIN_DIR}/steam-auto-clean-shaders --hook"
    if [[ -n "${STEAM_AUTO_PROFILER_PACMAN_HOOKS_DIR:-}" ]]; then
        mkdir -p "$SYSTEM_BIN_DIR" "$PACMAN_HOOKS_DIR"
        install -m 755 "$REPO_DIR/bin/steam-auto-clean-shaders" "$SYSTEM_BIN_DIR/steam-auto-clean-shaders"
        printf '%s\n' "$MESA_HOOK_CONTENT" >"$MESA_HOOK_FILE"
        chmod 644 "$MESA_HOOK_FILE"
    else
        sudo mkdir -p "$SYSTEM_BIN_DIR" "$PACMAN_HOOKS_DIR"
        sudo install -m 755 "$REPO_DIR/bin/steam-auto-clean-shaders" "$SYSTEM_BIN_DIR/steam-auto-clean-shaders"
        printf '%s\n' "$MESA_HOOK_CONTENT" | sudo tee "$MESA_HOOK_FILE" >/dev/null
        sudo chmod 644 "$MESA_HOOK_FILE"
    fi
    echo "Installed Mesa shader-cleanup helper at $SYSTEM_BIN_DIR/steam-auto-clean-shaders"
    echo "Installed Mesa shader-cleanup pacman hook at $MESA_HOOK_FILE"
fi

echo "Done! Test with: $TARGET_DIR/steam-auto-run --help"
