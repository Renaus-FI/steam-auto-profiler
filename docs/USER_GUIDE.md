# Steam Auto-Profiler User Guide

This guide describes the complete install, launch, synchronization, and troubleshooting workflow. Steam Auto-Profiler is a Bash/Python launcher for Linux that inspects a Steam AppID, applies a context-aware profile, and starts the existing game command; it does not install or inject a Proton runtime.

## Requirements

- Linux desktop session, Bash, Python 3, Steam, and standard command-line tools.
- Optional pre-launch dialog: `kdialog` or `zenity`.
- Optional network helper: `tc`, `ip`, and `ethtool`; the installer also needs `sudo` for `/usr/local/bin` and `/etc/sudoers.d`.
- Steam/Proton or native Linux game runtime, as appropriate.

## Installation from scratch

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

The installer copies all six commands (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run`, and `steam-auto-ui`) to `~/.local/bin`, installs the desktop launcher (`~/.local/share/applications/steam-auto-profiler.desktop`), creates `~/.config/steam-auto-profiler/profiles`, and adds default vkBasalt presets. Make sure `~/.local/bin` is in `PATH`.

Optional installation flags may be combined:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: installs the session network helper as `/usr/local/bin/steam-net-boost` and adds a narrowly scoped passwordless sudoers rule for that executable.
- `--compat-cachy-run`: preserves an existing `/usr/local/bin/cachy-run` as `/usr/local/bin/cachy-run.bak`, unless it already is the Steam Auto-Profiler shim, then installs a shim that delegates to `steam-auto-run`.
- `--with-auto-sync`: installs and enables a systemd user `steam-auto-profiler-sync.path` watcher and matching service.
- `--uninstall`: removes the installed commands, optional network helper/sudoers rule, compatibility shim, and auto-sync units.

Update or reinstall an existing checkout with:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Verify the system before configuring games:

```bash
steam-auto-run --doctor
```

## How it works end-to-end

1. **Resolve the AppID.** `SteamAppId` and `STEAM_COMPAT_APP_ID` take precedence, followed by numeric `GAMEID`; `umu-<appid>` is accepted and stripped to the numeric AppID.
2. **Locate the game.** `steam-auto-detect` searches standard Steam roots and secondary library folders in `libraryfolders.vdf`, reads `appmanifest_<APPID>.acf`, and scans the installation up to ten directory levels deep.
3. **Classify with four-tier precedence.** A known competitive AppID or detected anti-cheat runtime wins first. Native FidelityFX/FSR 3.1+ detection (`native-fsr4`/`native-fsr`) is second. Legacy DLSS/XeSS/FSR 2-style libraries select `legacy-upscaler`. Otherwise the title uses `standard`.
4. **Guard anti-cheat titles.** Competitive/anti-cheat profiles disable OptiScaler and MLFG/frame generation, disable competitive sharpening, and prefer Steam Linux Runtime + CachyOS compatibility tooling.
5. **Resolve compatibility settings.** Managed features are mapped into `PROTON_ADD_CONFIG` and `STEAM_COMPAT_CONFIG`. Existing user values are preserved. Supported tokens include `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, and `vkreflex`.
6. **Calculate a VRR cap.** An explicit `VRR_CAP=<fps>` is highest priority (`VRR_CAP=0` disables capping). Otherwise KDE (`kscreen-doctor`), wlroots (`wlr-randr`), or X11 (`xrandr`) refresh-rate data is read and used directly at 1:1 by default, such as 240 FPS on a 240 Hz display. Set `VRR_MINUS_MARGIN=1` to enable the optional -6% VRR headroom calculation (`hz * 94 / 100`). In Gamescope, DXVK/VKD3D frame caps are omitted unless `VRR_CAP` is explicit.
7. **Configure or load the per-AppID profile.** The pre-launch `kdialog` or `zenity` checklist is shown on the first launch unless a profile exists or GUI launch is disabled. Selecting **Save profile** writes a small allowlisted `KEY=VALUE` file to `~/.config/steam-auto-profiler/profiles/<APPID>.env`.
8. **Apply launch variables and scheduling.** The wrapper exports Wayland/HDR (`WAYLANDDRV_SHORTCUT_INHIBIT=0` by default, per-profile overridable), low-latency DXVK/VKD3D (`DXVK_FRAME_PACE=low-latency-vrr` when VRR capping is active), AMD `PROTON_NATIVE_AGS=1`, modern `VKD3D_CONFIG` (omitted when `SAFEDX12=1`), strict mutual-exclusion guards (disabling vkBasalt whenever FSR 4 or OptiScaler is active, and disabling Anti-Lag / low-latency / VRR frame caps whenever MLFG is enabled), upscaler, Steam Input, overlay, and compatibility variables. It uses `game-performance`, then `powerprofilesctl launch -p performance --`, and `gamemoderun` only when it will not conflict with `ananicy-cpp`.
9. **Start, monitor, and recover from fast crashes.** Native Linux titles omit Proton/Wine/DXVK/VKD3D variables. SteamVR (`250820`) and `-vr`/`--vr` launches bypass flatscreen orchestration cleanly. The wrapper records launch duration and exit code in `last-launch.log`; if a Proton/Windows title exits non-zero in under 20 seconds while experimental Wayland or DX12 flags are active (`USE_XWAYLAND=0` or `USE_SAFEDX12=0`), it logs a `crash_hint` and (when `NO_GUI=0`) offers a one-click `kdialog`/`zenity` prompt to save Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) for the next launch.
10. **Restore optional network state.** If QoS is enabled, `steam-net-boost` activates per-session state for the selected interface while preserving existing static CAKE setups (both root `cake` and LAN-exempted HTB + leaf `cake` trees, as well as `wan-cake-shaper.service` and `cake-shaper.service`). Pre-existing root qdisc (`cake` vs `fq_codel`), tx queue length, and NIC EEE state are restored after the last launch session exits. `steam-net-boost status` runs read-only without root privileges.

## Unified Control Center (`steam-auto-ui`)

Launch `steam-auto-ui` from the KDE/desktop application menu or terminal:

```bash
steam-auto-ui          # Auto-selects native Qt6 GUI (PySide6/PyQt6) or curses TUI
steam-auto-ui --gui    # Launch native Qt6 window
steam-auto-ui --tui    # Launch terminal curses interface (works over SSH)
steam-auto-ui --check  # Run headless self-test
```

The control center provides five synchronized views (also reachable via `steam-auto-run --ui`):

1. **Games & Profiles:** Searchable library table including both Steam titles and read-only Non-Steam `shortcuts.vdf` entries (`AppID`, `Name`, `Source`, `Auto Class`, `Synced`, `Profile`), actionable Upscaler SDK hint badge (`AUTO_UPSCALER_INFO`), interactive profile toggles (`XWayland`, `FSR4`, `MLFG`, `VRR_CAP`, `vkBasalt`, `Safe DX12`, `Net QoS`, `SDL Input`, `Keep Overlay`, `OptiScaler`, `Auto KDE HDR Toggle`), live mutual-exclusion validation, `Dry-Run` preview, `Benchmarks` jump button, and `Reset Profile`.
2. **System & Telemetry:** Displays `steam-auto-run --doctor`, `scxctl get` scheduler mode, live installed stack versions (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`), shader cache disk usage (`~/.cache/mesa_shader_cache*`), `/var/log/pacman.log` git/AUR downgrade warnings, GPU VRAM/utilization/temperature, `tc -s qdisc` LAN (`cake 10:`) vs WAN (`cake 20:`) throughput and `av_delay`, and `vr-mode status`.
3. **Library Sync:** Triggers `steam-auto-sync --report` (including Non-Steam shortcuts read-only), `--sanitize --dry-run`, `--sanitize` (warning if Steam is running), and `--migrate-cachy-run`.
4. **Logs & Recovery:** Browses `last-launch.log` and `last-<APPID>.log`, highlights `crash_hint` warnings, and offers one-click **Apply Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`)**.
5. **Benchmarks:** Compares silent `BENCH=1` MangoHud runs (`Avg FPS`, `1% Low FPS`, `P99 Frametime (ms)`) stored in `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` side-by-side across FSR4, MLFG, XWayland, and Safe DX12 settings.

## VR titles (`vr-run`)

For VR games, set Steam **Properties > General > Launch Options** to:

```text
vr-run %command%
```

`vr-run` is a dedicated, hardware-agnostic VR launch orchestrator:

- Scrubs inherited flatscreen variables (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Auto-selects the discrete GPU via `MESA_VK_DEVICE_SELECT` and sets `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` on AMD GPUs.
- Dynamically detects WiVRn and xrizer OpenXR/OpenVR paths (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) and exports `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW`, and `LD_LIBRARY_PATH` without clobbering user overrides.
- Automatically invokes `vr-mode on` before launch and `vr-mode off` when the last VR session exits (ref-counted in `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` so switching VR games does not toggle off prematurely; set `VR_AUTO_MODE=0` to disable).
- Runs through the safe scheduler chain (`game-performance` -> `powerprofilesctl` -> `gamemoderun` when `ananicy-cpp` is inactive -> direct `exec`).
- Supports `vr-run --dry-run` to inspect resolved VR variables without launching.

`steam-auto-detect` automatically detects VR titles via `openvr_api.dll`, `openxr_loader.dll`, and SteamVR manifests (`AUTO_IS_VR=1`, class `vr`). `steam-auto-sync` automatically assigns `vr-run %command%` to newly installed VR titles, preserves intentional `vr-run %command%` launch options during sync and `--sanitize`, and displays `VR` in `steam-auto-sync --report`.

## Steam launch automation

Set this in each game’s Steam **Properties > General > Launch Options**:

```text
steam-auto-run %command%
```

For UMU launchers, include `GAMEID=umu-<appid>`:

```text
GAMEID=umu-2357570 steam-auto-run %command%
```

Close Steam completely before changing `localconfig.vdf`. Preview discovery and library integration with:

```bash
steam-auto-sync --dry-run
steam-auto-sync --report
steam-auto-sync --print-library-paths
```

Apply the wrapper to discovered Steam libraries:

```bash
steam-auto-sync
```

Sanitize legacy or stale launch entries while preserving engine arguments such as `-dx12`:

```bash
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
```

The alias `steam-auto-sync --clean` is equivalent to `--sanitize`. Migrate legacy cachy-run profiles and remove the wrapper with:

```bash
steam-auto-sync --migrate-cachy-run
steam-auto-sync --remove
```

Steam libraries and timestamped backups:

- `--print-library-paths` prints every discovered Steam library.
- `--keep-backups N` retains the newest `N` timestamped `localconfig.vdf.bak.*` files per profile.
- `--keep-backups 0` keeps all backups; the default is `10`.

The optional watcher is installed with `./install.sh --with-auto-sync`. It watches Steam `steamapps` directories and runs:

```bash
steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300
```

Install or repair only the systemd units:

```bash
steam-auto-sync --install-systemd
systemctl --user enable --now steam-auto-profiler-sync.path
```

## Profiles and configuration

On a graphical session, the first launch shows `kdialog` or `zenity` when available. Check **Save profile** to persist choices as `~/.config/steam-auto-profiler/profiles/<APPID>.env`.

Useful commands:

| Purpose | Command |
| --- | --- |
| Inspect a game | `steam-auto-run --inspect APPID` |
| Machine-readable classification | `steam-auto-detect --inspect --json APPID` |
| Open/reconfigure a profile | `steam-auto-run --configure APPID` |
| Preview variables without launching | `steam-auto-run --dry-run APPID` |
| Reset a profile | `steam-auto-run --reset APPID` |
| List saved profiles | `steam-auto-run --list-profiles` |
| Show latest launch log | `steam-auto-run --last-log [APPID]` |
| Audit system readiness | `steam-auto-run --doctor` |
| Open Control Center (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check]` |
| Preview VR launch environment | `vr-run --dry-run` |
| Inspect network helper (read-only) | `steam-net-boost status [IFACE]` |

Profile files accept an allowlisted set of `KEY=VALUE` lines. CRLF and quoted values are accepted; shell syntax and unknown keys are ignored.

To disable the pre-launch dialog everywhere:

```bash
mkdir -p ~/.config/environment.d
printf 'NO_GUI=1\n' >> ~/.config/environment.d/gaming.conf
```

## Environment overrides

Place overrides before the wrapper:

```text
VRR_CAP=120 MLFG=1 KEEP_OVERLAY=1 steam-auto-run %command%
```

| Override | Effect |
| --- | --- |
| `NO_GUI=1` | Never show the pre-launch dialog. |
| `FORCE_GUI=1` | Reopen the checklist even for a saved profile. |
| `XWAYLAND=1` | Force XWayland instead of native Wayland. |
| `MLFG=1` | Enable frame generation. |
| `VRR_CAP=<fps>` | Set a custom VRR/DXVK/VKD3D frame cap; `VRR_CAP=0` disables capping. |
| `VRR_MINUS_MARGIN=1` | Enable the optional -6% monitor-refresh safety margin. |
| `KEEP_OVERLAY=1` | Preserve Steam Overlay `LD_PRELOAD` instead of clearing it. |
| `GAMEID=umu-<appid>` | Resolve UMU/other launcher AppIDs and strip the `umu-` prefix. |
| `NETOPT=1` | Request the session network profile. |
| `OPTISCALER=1` | Allow the optional upscaler bridge; guarded off for anti-cheat titles. |
| `SHARPEN=1` or `RCAS=1` | Enable post-process sharpening. |
| `SDL=1` | Prefer native SDL/Steam Input emulation. |
| `CEF=1` / `GST=1` | Enable launcher compatibility handling. |
| `FSR_HUD=1` | Enable FSR/DLSS indicator variables. |
| `SAFEDX12=1` | Omit experimental `VKD3D_CONFIG` flags and `vkd3dbindlesstb` compat token. |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Allow shortcut inhibition under Wine Wayland (default `0`; also supported in `.env` profiles). |
| `AUTO_HDR_SWITCH=1` | Automatically enable KDE Plasma 6 HDR via `kscreen-doctor` on launch when game HDR is active and restore SDR on exit. |
| `BENCH=1` | Run silent MangoHud CSV logging (`no_display`, duration via `BENCH_DURATION`, default `60`s) and record `Avg FPS`, `1% Low FPS`, and `P99 (ms)` to `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`. |
| `VULKAN=1` | Add `-vulkan` to a launch. |
| `NO_NTSYNC=1` | Disable NTSync for a legacy title. |
| `NO_DECORATION=1` | Disable window decorations. |

## Lutris, Heroic, Faugus, and UMU

Set `steam-auto-run` as the wrapper/command prefix and choose `proton-cachyos-slr` where supported.

- **Lutris:** enable advanced options, select the Proton runner, disable the Lutris runtime, prefer system libraries, and prefix the command with `steam-auto-run`.
- **Heroic/Faugus:** select `proton-cachyos-slr` or the intended Proton build and add `steam-auto-run` as the wrapper.
- **UMU/Protonfixes:** set `PROTON_VERB=waitforexitandrun` if the launch lifecycle requires it.

For UMU:

```text
GAMEID=umu-2357570 steam-auto-run %command%
```

## Troubleshooting

**The GUI does not appear:** install `kdialog` or `zenity`, or set `NO_GUI=1`. `FORCE_GUI=1` reopens a saved profile.

**A profile is not detected:** verify the AppID with `steam-auto-run --inspect APPID` or `steam-auto-detect --inspect --json APPID`. Confirm the game manifest exists and that its install folder is under a configured Steam library.

**Steam refuses launch-option changes:** close Steam completely and rerun `steam-auto-sync --sanitize --dry-run`, then apply `steam-auto-sync --sanitize`.

**Wayland or XWayland behaves incorrectly:** use `XWAYLAND=1` for XWayland or remove the override for native Wayland. If a saved profile still wins, use `FORCE_GUI=1` or `steam-auto-run --reset APPID`.

**Anti-cheat or launcher compatibility:** prefer `proton-cachyos-slr` and Steam Linux Runtime. Anti-cheat classification prevents MLFG and OptiScaler; use `steam-auto-run --doctor` to check EAC/Linux runtime prerequisites.

**Network helper is unavailable:** install it with `./install.sh --with-net-boost`, verify `sudo steam-net-boost status`, and select `netopt` or set `NETOPT=1`. The helper has no effect without `sudo` access or supported interface tools.

**Wrong frame cap:** set `VRR_CAP=<fps>` explicitly, or set `VRR_MINUS_MARGIN=1` for the optional -6% headroom. By default the detected monitor refresh rate is used directly. In a Gamescope session `VRR_CAP` is the only way to export DXVK/VKD3D frame rate variables intentionally.

**Review the last launch:** run `steam-auto-run --last-log APPID`; it includes launch variables, Gamescope state, command, and exit code.

For implementation details and compatibility design, see [ARCHITECTURE.md](ARCHITECTURE.md).
