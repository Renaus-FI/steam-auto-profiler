# Steam Auto-Profiler User Guide

This guide covers the complete installation, flatscreen & VR launch orchestration, `steam-auto-ui` Control Center, library synchronization, benchmarking, Steam Controller 2026 Wayland+HDR routing, Ultra Bleeding-Edge mode, and troubleshooting workflow for **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler is a lightweight Bash/Python launcher and control center for Linux that inspects a Steam AppID (or Non-Steam shortcut), applies a context-aware profile with strict driver/upscaler/anti-cheat guardrails, and starts the existing game command. It never bundles or injects a third-party Proton runtime.

---

## Requirements

- Linux desktop session (KDE Plasma 6 / Wayland, GNOME, wlroots, or X11), Bash 5+, Python 3.10+, Steam, and standard core utilities.
- Optional native Control Center GUI: `PyQt6` or `PySide6` (falls back automatically to zero-dependency stdlib `curses` TUI).
- Optional pre-launch checklist dialogs: `kdialog` or `zenity`.
- Optional silent frametime benchmarking: `mangohud`.
- Optional session network helper: `tc`, `ip`, and `ethtool` (`sudo` required only during `--with-net-boost` installation).

---

## Installation & Updates

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` copies all six executables (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run`, and `steam-auto-ui`) into `~/.local/bin`, installs the desktop entry (`~/.local/share/applications/steam-auto-profiler.desktop`), creates `~/.config/steam-auto-profiler/profiles`, and adds default vkBasalt presets (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Ensure `~/.local/bin` is in `PATH`.

Optional installer flags may be combined:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync --with-steam-controller
```

- `--with-net-boost`: installs `/usr/local/bin/steam-net-boost` (plus system copies of the other scripts) and a narrowly scoped passwordless sudoers rule for `steam-net-boost`.
- `--compat-cachy-run`: preserves an existing `/usr/local/bin/cachy-run` as `/usr/local/bin/cachy-run.bak` (unless it is already the Steam Auto-Profiler shim) and installs a forwarding shim to `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): installs and enables the systemd user `steam-auto-profiler-sync.path` watcher and matching oneshot service across all discovered Steam libraries.
- `--with-steam-controller`: installs `/etc/udev/rules.d/61-steam-controller-2026.rules` for Steam Controller 2026 (`Triton`/`Proteus`) and Wireless Steam Puck (`28de:{1302,1304,1005,1007}`) with `uaccess`/`uucp` `hidraw` + `ttyACM*` firmware permissions, `ID_MM_DEVICE_IGNORE=1` (`ModemManager` ignore), and zero-latency disabled USB selective suspend (`power/control=on`, `power/autosuspend=-1`).
- `--uninstall`: removes installed binaries, desktop entry, optional network helper/sudoers rule, Steam Controller udev rules, compatibility shim, and systemd user auto-sync units.

To update an existing checkout:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Verify host readiness before syncing games:

```bash
steam-auto-run --doctor
```

---

## End-to-End Launch Pipeline

1. **AppID Resolution:** Checks `SteamAppId`, `STEAM_COMPAT_APP_ID`, then `GAMEID` (stripping any `umu-` prefix for Lutris/Heroic/UMU).
2. **Library & Shortcut Discovery:** `steam-auto-detect` searches Steam roots and secondary libraries in `libraryfolders.vdf`, reads `appmanifest_<APPID>.acf`, or falls back read-only to binary `userdata/*/config/shortcuts.vdf`, then performs a single-pass `find` up to 10 levels deep (pruning `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Five-Tier Classification Precedence:**
   - **1. `competitive-anticheat`:** Known competitive AppID or detected anti-cheat runtime (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE, etc.). Disables OptiScaler, MLFG, vkBasalt, and async DXVK; enables low-latency and session network QoS.
   - **2. `vr`:** Detected `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest`, or `vr-run`/`-vr` shortcut flags. Exports `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modular FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Enables driver-level FSR4 upgrade (`PROTON_FSR4_UPGRADE=1` or `PROTON_FSR4_RDNA3_UPGRADE=1` on AMD RDNA 3).
   - **4. `legacy-upscaler`:** Legacy DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`), or FSR 2/3.0 DLLs. Marks `AUTO_OPTISCALER=1` and sets `AUTO_UPSCALER_INFO` guidance.
   - **5. `standard`:** Safe native Wine Wayland + low-latency VRR profile.
4. **VRR Refresh-Rate Capping:** Explicit `VRR_CAP=<fps>` always wins (`VRR_CAP=0` disables capping). Otherwise active display refresh is probed via `kscreen-doctor` (KDE Plasma 6 active `*` mode or legacy `Hz`), `wlr-randr`, or `xrandr` and applied 1:1 by default (`240 FPS` on 240 Hz). Enable `VRR_MINUS_MARGIN=1` for the optional `-6%` VRR safety margin (`hz * 94 / 100`, e.g., `225 FPS` on 240 Hz). In Gamescope sessions, DXVK/VKD3D caps are omitted unless `VRR_CAP` is explicit.
5. **Mutual-Exclusion Guardrails:**
   - **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` is enforced whenever `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1`, or `USE_OPTISCALER=1` (prevents double-sharpening and HDR10 clipping).
   - **MLFG + Low-Latency / VRR Caps:** `MLFG=1` (`USE_MLFG=1`) exports `ENABLE_LAYER_MESA_ANTI_LAG=0`, `LOW_LATENCY_LAYER=0`, `LOW_LATENCY_LAYER_REFLEX=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, unsets `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, and `DXVK_FRAME_PACE`, and exports `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` on AMD RDNA 3. When `USE_MLFG=0` and VRR capping is active, `DXVK_FRAME_PACE=low-latency-vrr` is exported.
   - **Mesa 27.0 / RDNA 4 & Reflex-to-Anti-Lag 2 Guards:** `USE_TRANSFER_QUEUE=1` (`TRANSFER_QUEUE=1`) appends deduplicated `transfer_queue` to `RADV_PERFTEST` on AMD RDNA 3/4 GPUs (default stays `RADV_PERFTEST=sam`). `USE_NATIVE_ANTILAG=1` (`NATIVE_ANTILAG=1`) uses Mesa 26.3+/27.0 native RADV `VK_AMD_anti_lag` with `ENABLE_LAYER_MESA_ANTI_LAG=0`. `USE_REFLEX_LAYER=1` (`REFLEX_LAYER=1`) enables `LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1` (translating Reflex to native `VK_AMD_anti_lag`), forces `ENABLE_LAYER_MESA_ANTI_LAG=0` so latency layers never stack, is disabled by `MLFG=1`, and is hard-blocked (`=0`) in `competitive-anticheat` titles. `USE_VK_VIDEO_DECODE=1` (`VK_VIDEO_DECODE=1`) exports deduplicated `RADV_EXPERIMENTAL=video_decode` (migrating legacy `RADV_PERFTEST=video_decode`).
   - **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** Opt-in experimental stack for non-anticheat titles enabling deduplicated `RADV_PERFTEST=sam,transfer_queue` (RDNA 3/4), `RADV_EXPERIMENTAL=video_decode`, `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, and `WAYLANDDRV_RAWINPUT=1` (exported **only** when `USE_XWAYLAND=0` and `GAMESCOPE_SESSION=0`, explicitly unset otherwise). Hard-blocked in `competitive-anticheat` titles and automatically enforces `ENABLE_VKBASALT=0`.
   - **Hunt: Showdown 1896 (`AppID 594650`) Compatibility Guard:** Enforces `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, and `USE_NET_OPT=1` without conflicting with `USE_STEAM_CONTROLLER`. Both `steam-auto-run --doctor` and `steam-auto-ui` inspect Steam `config/config.vdf` `CompatToolMapping` for `594650` and warn if unset or set to `proton-cachyos*` (recommending Valve's `Proton 11.0-2` or `Proton Hotfix`).
   - **Steam Controller 2026 & Wireless Steam Puck (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`):**
     - `auto` (default): detects Valve 2026 hardware (`28de:{1302,1304,1005,1007}`) via `/sys/bus/usb/devices/*` and selects `wayland-hdr` on Wayland sessions (or `xwayland` on X11).
     - `wayland-hdr`: preserves native `winewayland.drv` + OLED HDR10 (`USE_XWAYLAND=0`, `PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`) without forcing `LD_PRELOAD` overlay overhead, exports `PROTON_USE_SDL=0`, `PROTON_PREFER_SDL=0`, `PROTON_NO_STEAMINPUT=0` (omitting `sdlinput`), launches a background watcher that applies `steam steam://forceinputappid/<APPID>` (~3s + ~8s confirmation nudge) and monitors `udevadm monitor --udev --subsystem-match=hidraw --subsystem-match=usb` (debounced >= 2s) to re-apply on mid-game controller sleep/reconnect, and resets `steam://forceinputappid/0` in the unified `EXIT`/`INT`/`TERM` trap.
     - `xwayland`: fallback forcing `USE_XWAYLAND=1`, `USE_KEEP_OVERLAY=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0` (omitting `sdlinput`) for engines requiring XWayland Steam Input.
     - `off` (`0`): disables all Steam Controller routing overrides. Legacy `USE_STEAM_CONTROLLER=1` maps to `wayland-hdr` on Wayland or `xwayland` on X11.
   - **Modern DX12 + Safe DX12:** Exports `PROTON_NATIVE_AGS=1` on AMD and `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` when `USE_SAFEDX12=0` (cleanly omitted when `SAFEDX12=1`).
6. **Compat-Token Mapping & Retired Flag Purge:** Managed features are appended without clobbering existing user values into both `PROTON_ADD_CONFIG` and `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `lowlatencylayer`, `localshadercache`, `pipewire`, `fsr4`, `wow64`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`. Retired Proton/Wine variables (`PROTON_ENABLE_HDR`, `PROTON_VKREFLEX`, `PROTON_MEDIA_USE_GST`, `PROTON_FSR3_UPGRADE`, `PROTON_VKD3D_HEAP`, `WINEPULSE_FAST_POLLING`) are purged on launch and stripped during `steam-auto-sync --sanitize`.
7. **Auto KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** When enabled outside Gamescope with `DXVK_HDR=1` (or `USE_HDR=1`), probes the primary enabled output via `kscreen-doctor -o`; if HDR is currently disabled, enables it before launch and restores SDR in an `EXIT`/`INT`/`TERM` trap.
8. **Silent Frametime Benchmarking (`BENCH=1`):** Runs MangoHud in hidden CSV mode (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), parses frametimes on exit, appends `Avg FPS`, `1% Low FPS`, and `P99 (ms)` to `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`, and removes temporary CSVs.
9. **Fast-Crash Safe Mode Auto-Recovery:** If a Proton/Windows title exits non-zero in under `20s` (configurable via `SAP_CRASH_THRESHOLD_SEC`) while experimental Wayland or DX12 flags are active (`USE_XWAYLAND=0` or `USE_SAFEDX12=0`), logs a `crash_hint` in `last-<APPID>.log` and `last-launch.log`, and prompts (when GUI is active) to save `USE_XWAYLAND=1` + `USE_SAFEDX12=1` for the next launch.
10. **Scheduler & Network Lifecycle:** Runs through `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (only when `ananicy-cpp.service` is inactive) -> direct execution, with optional `PRIME=1` (`prime-run`). If `USE_NET_OPT=1`, `steam-net-boost` runs ref-counted `on`/`off` with `flock` while preserving static root CAKE and HTB + leaf CAKE hierarchies.

---

## Unified Control Center (`steam-auto-ui`)

Launch `steam-auto-ui` from your desktop application menu, via `steam-auto-run --ui`, or directly:

```bash
steam-auto-ui                 # Auto-detects Qt6 GUI (PyQt6/PySide6) or curses TUI
steam-auto-ui --gui           # Force native Qt6 GUI window
steam-auto-ui --tui           # Force stdlib curses TUI (works over SSH)
steam-auto-ui --lang fi       # Launch with explicit UI language (27 languages supported)
steam-auto-ui --check         # Run headless self-check (prints JSON diagnostics)
```

`steam-auto-ui` auto-detects the system locale from `LC_ALL` / `LC_MESSAGES` / `LANG` and provides a live language selector dropdown in the Qt6 GUI (and the `L` hotkey in the `curses` TUI) to switch between all 27 languages at runtime without restarting.

### Five Synchronized Views

1. **Games & Profiles:** Filterable table of Steam titles and read-only Non-Steam `shortcuts.vdf` entries (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), Upscaler SDK badge (`AUTO_UPSCALER_INFO`), live mutual-exclusion validation across all 15 profile controls (including `Transfer Queue`, `Native RADV Anti-Lag`, `Reflex -> Anti-Lag 2`, `Ultra Bleeding-Edge`, and the 4-mode `Steam Controller 2026 / Puck Routing` selector: `Auto`, `Wayland + HDR`, `XWayland`, `Off`) + `VRR_CAP`, `Dry-Run Preview`, `Benchmarks` jump button, and `Reset Profile`.
2. **System & Telemetry:** Non-blocking live readout of `steam-auto-run --doctor`, `scxctl get` / `sched_ext` state, installed stack versions (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), shader cache usage (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` git/AUR downgrade alerts, GPU VRAM/utilization/temperature, `tc -s qdisc` LAN (`10:`) vs WAN (`20:`/root) throughput and `av_delay`, and `vr-mode status`.
3. **Library Sync:** Live Steam running-state guard banner plus one-click `--report`, `--sanitize --dry-run`, `--sanitize` (refused while Steam is running), and `--migrate-cachy-run`.
4. **Logs & Recovery:** Browse `last-launch.log` and `last-<APPID>.log`, inspect `crash_hint` alerts, and apply one-click Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarks:** Filterable side-by-side comparison table of `BENCH=1` frametime runs (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR Orchestration (`vr-run`)

Set Steam **Properties > General > Launch Options** for VR titles to:

```text
vr-run %command%
```

- Scrubs inherited flatscreen overrides (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Auto-selects the highest-VRAM discrete GPU via `MESA_VK_DEVICE_SELECT` and sets `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` on AMD GPUs.
- Dynamically probes WiVRn & xrizer OpenXR/OpenVR paths (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) and configures `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW`, and `LD_LIBRARY_PATH` without overwriting explicit user overrides.
- Ref-counts `vr-mode on` / `vr-mode off` in `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (with `flock`) when `vr-mode` is installed (`VR_AUTO_MODE=0` disables it).
- Runs through the same `ananicy-cpp`-aware scheduler chain (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> direct `exec`).
- Preview resolved variables at any time with `vr-run --dry-run`.

`steam-auto-run` bypasses SteamVR (`250820`) and `-vr`/`--vr` launches automatically, and `steam-auto-sync` auto-assigns and preserves `vr-run %command%` for VR titles.

---

## Steam Library Sync (`steam-auto-sync`)

Close Steam completely before writing to `localconfig.vdf`:

```bash
steam-auto-sync --report              # Read-only library + shortcuts.vdf audit
steam-auto-sync --print-library-paths # Show all discovered Steam libraries
steam-auto-sync --dry-run             # Preview edits
steam-auto-sync                       # Inject steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Preview legacy flag cleanup
steam-auto-sync --sanitize            # Clean messy/orphan flags (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migrate legacy cachy-run profiles
steam-auto-sync --remove              # Remove steam-auto-run wrapper
```

- Timestamped `localconfig.vdf.bak.*` backups are pruned automatically with `--keep-backups N` (default `10`; `0` keeps all).
- Exclude specific AppIDs by listing them (one per line, `#` comments allowed) in `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Systemd auto-sync watcher (`./install.sh --with-auto-sync` or `steam-auto-sync --install-systemd`) runs `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` when Steam manifests change.

---

## CLI & Profile Reference

### Commands

| Purpose | Command |
| --- | --- |
| System readiness audit | `steam-auto-run --doctor` (alias `--check-system`) |
| Re-apply Steam Input layout | `steam-auto-run --reapply-input <APPID\|0>` |
| Launch Control Center (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` or `steam-auto-run --ui` |
| Inspect a game (human-readable) | `steam-auto-run --inspect APPID` |
| Inspect a game (JSON) | `steam-auto-detect --inspect --json APPID` |
| Reconfigure profile interactively | `steam-auto-run --configure APPID` |
| Preview resolved launch env | `steam-auto-run --dry-run APPID` |
| Reset saved profile | `steam-auto-run --reset APPID` |
| List saved profiles | `steam-auto-run --list-profiles` |
| Show latest launch log | `steam-auto-run --last-log [APPID]` |
| Preview VR launch env | `vr-run --dry-run` |
| Inspect network helper (read-only) | `steam-net-boost status [IFACE]` |

### Saved `.env` Profile Keys & Environment Overrides

Profile files live at `~/.config/steam-auto-profiler/profiles/<APPID>.env` and accept an allowlisted `KEY=VALUE` format (shell command substitutions and unknown keys are safely ignored):

| `.env` Key | Env Override | Effect |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Force XWayland instead of native Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Disable driver-level FSR 4 upgrade (default `1`) |
| `USE_MLFG=1` | `MLFG=1` | Enable frame generation (disables Anti-Lag, low-latency, and VRR frame caps) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Enable OptiScaler bridge (guarded off for `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Enable vkBasalt sharpening (disabled when FSR 4 or OptiScaler is active) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Omit experimental `VKD3D_CONFIG` flags and `vkd3dbindlesstb` token |
| `USE_NET_OPT=1` | `NETOPT=1` | Activate session network QoS via `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Prefer native SDL / Steam Input emulation |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Preserve Steam Overlay `LD_PRELOAD` |
| `USE_CEF_FIX=1` | `CEF=1` | Append `--in-process-gpu` for CEF launchers |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Disable NTSync for legacy titles |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Disable window manager decorations |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Custom DXVK/VKD3D frame cap (`0` disables capping) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Apply `-6%` monitor-refresh headroom (e.g. `225 FPS` on 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Allow shortcut inhibition under Wine Wayland (default `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Auto-enable KDE Plasma 6 HDR on launch and restore SDR on exit |
| `USE_TRANSFER_QUEUE=1` | `TRANSFER_QUEUE=1` | Append `,transfer_queue` to `RADV_PERFTEST` on AMD RDNA 3/4 GPUs (SDMA queue) |
| `USE_NATIVE_ANTILAG=1` | `NATIVE_ANTILAG=1` | Use Mesa 26.3+/27.0 native RADV `VK_AMD_anti_lag` (`ENABLE_LAYER_MESA_ANTI_LAG=0`) |
| `USE_REFLEX_LAYER=1` | `REFLEX_LAYER=1` | Enable Proton-CachyOS `LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1` (blocked in anti-cheat / MLFG) |
| `USE_VK_VIDEO_DECODE=1` | `VK_VIDEO_DECODE=1` | Enable Mesa 27.0 Vulkan video decode via `RADV_EXPERIMENTAL=video_decode` |
| `USE_BLEEDING_EDGE=1` | `BLEEDING_EDGE=1` | Enable Ultra Bleeding-Edge experimental Mesa 27 / VKD3D 12_2 / SM 6_8 / WoW64 / GStreamer / RawInput stack (non-anticheat only) |
| `USE_STEAM_CONTROLLER=auto\|wayland-hdr\|xwayland\|off` | `STEAM_CONTROLLER=...` | Route Steam Controller 2026 / Puck (`28de:{1302,1304,1005,1007}`): `wayland-hdr` keeps native Wayland+HDR + `forceinputappid` & reconnect watcher; `xwayland` fallback; `off` disables (legacy `1`/`0` supported) |
| — | `BENCH=1`, `BENCH_DURATION=60` | Run silent MangoHud CSV benchmark and save JSON summary |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Suppress or force-reopen pre-launch `kdialog`/`zenity` checklist |
| — | `FSR_HUD=1` | Export FSR/DLSS/MLFG HUD indicator variables |
| — | `VULKAN=1` / `PRIME=1` | Append `-vulkan` / wrap with `prime-run` |
| — | `GAMEID=umu-<appid>` | Resolve UMU / Lutris / Heroic AppIDs |

---

## Lutris, Heroic, Faugus & UMU

- **Lutris:** Enable advanced options, select `proton-cachyos-slr` (or your Proton build), disable the Lutris runtime, prefer system libraries, and set the command prefix to `steam-auto-run`.
- **Heroic / Faugus:** Choose `proton-cachyos-slr` and add `steam-auto-run` as the wrapper/command prefix.
- **UMU / Protonfixes:** Export `PROTON_VERB=waitforexitandrun` and `GAMEID=umu-<appid>` when needed.

---

## Troubleshooting

- **Fast crash on Wayland or DX12:** Open **Logs & Recovery** in `steam-auto-ui` (or run `steam-auto-run --last-log APPID`) and apply Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), or run `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Anti-cheat titles fail to launch:** Use `proton-cachyos-slr` (Steam Linux Runtime) and run `steam-auto-run --doctor` to verify EAC v2, `/dev/ntsync`, and `vm.max_map_count`.
- **Steam reverts launch options:** Close Steam completely before running `steam-auto-sync` or `steam-auto-sync --sanitize`.
- **Wrong or missing VRR cap:** Set `VRR_CAP=<fps>` explicitly, `VRR_CAP=0` to disable, or `VRR_MINUS_MARGIN=1` for `-6%` headroom. In Gamescope, only an explicit `VRR_CAP` exports DXVK/VKD3D caps.
- **Network QoS check:** Run `steam-net-boost status` (unprivileged read-only). Install the root helper with `./install.sh --with-net-boost` if you want automatic session QoS.

See [ARCHITECTURE.md](ARCHITECTURE.md) for design internals and [i18n/README.md](i18n/README.md) for all 27 localized guides.
