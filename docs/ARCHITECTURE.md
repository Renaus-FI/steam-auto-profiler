# Steam Auto-Profiler Architecture

## Design Goal

Deliver a deterministic, zero-bloat, context-aware launch pipeline and control center for Steam on Linux (KDE Plasma 6 / Wayland, GNOME, wlroots, X11, and Gamescope) without vendoring Proton runtimes, injecting third-party binaries, or forcing users to maintain fragile environment strings.

---

## Component Topology

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    steam-auto-ui (PyQt6 / PySide6 / curses)             │
│  5 Views: Games & Profiles | Telemetry | Sync | Logs | Benchmarks       │
│  27-language live i18n · Daemon worker threads · Cancellable Popen PG   │
└───────────┬─────────────────────┬────────────────────┬──────────────────┘
            │                     │                    │
            ▼                     ▼                    ▼
  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────┐
  │ steam-auto-detect│  │ steam-auto-sync  │  │ steam-auto-run / vr-run│
  │ Single-pass scan │  │ flock VDF span   │  │ Launch orchestrators   │
  │ shortcuts.vdf RO │  │ editor & backup  │  │ HDR · Bench · Recovery │
  │ AUTO_IS_VR / SDK │  │ pruner & VR sync │  │ Scheduler & QoS traps  │
  └──────────────────┘  └──────────────────┘  └───────────┬────────────┘
                                                          │
                                                          ▼
                                              ┌────────────────────────┐
                                              │    steam-net-boost     │
                                              │ flock ref-counted QoS  │
                                              │ HTB + CAKE preserving  │
                                              └────────────────────────┘
```

---

## 1. Heuristic Classifier (`bin/steam-auto-detect`)

- **Library & Shortcut Discovery:** Scans standard and Flatpak Steam roots plus secondary libraries listed in `libraryfolders.vdf`. When no Steam `appmanifest_<APPID>.acf` matches, falls back to a read-only binary parser for `userdata/*/config/shortcuts.vdf` (preserving exact bytes on disk).
- **Single-Pass Directory Traversal:** Performs one pruned `find` (depth `<= 10`, skipping `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`) to classify titles in strict precedence order:
  1. `competitive-anticheat` (known competitive AppIDs + anti-cheat DLL/SYS/EXE/SO signatures)
  2. `vr` (`openvr_api.dll`/`so`, `openxr_loader.dll`/`so*`, `*.vrmanifest`, or `vr-run`/`-vr` shortcut flags -> `AUTO_IS_VR=1`)
  3. `native-fsr4` / `native-fsr` (modular FidelityFX SDK 3.1+ & `amdxcffx64.dll`)
  4. `legacy-upscaler` (`nvngx_dlss*.dll`, `libxess*.dll`, `sl.interposer.dll`, `ffx_fsr2*.dll`, `ffx_fsr3*.dll`)
  5. `standard`
- **Reflex / Streamline / DLSS & Hardware-Aware Smart Defaults (`v2.2.0` / `v2.3.0`):** Detects `sl.reflex.dll`, `sl.interposer.dll`, and `nvngx_dlss*.dll` (`AUTO_HAS_REFLEX=1`), probes AMD RDNA 3/4 PCI IDs via `SAP_DRM_DIR`/`/sys/class/drm`, and computes hardware- and class-aware defaults (`AUTO_TRANSFER_QUEUE`, `AUTO_NATIVE_ANTILAG`, `AUTO_VK_VIDEO_DECODE`, `AUTO_REFLEX_LAYER`, `AUTO_BLEEDING_EDGE`, `AUTO_OPTISCALER=1` for AMD RDNA 3/4 `legacy-upscaler` titles, and `AUTO_HDR_SWITCH=1` on Wayland with `kscreen-doctor`) plus a pure `smart_defaults` map in `--json` for `steam-auto-ui`.
- **Actionable Upscaler SDK Info (`AUTO_UPSCALER_INFO`):** Emits human- and machine-readable (`--json`) guidance distinguishing native `PROTON_FSR4_UPGRADE=1` eligible titles from legacy upscaler titles that can opt in to `USE_OPTISCALER=1`.
- **Compat-Token Preview:** Computes `AUTO_PROTON_ADD_CONFIG` respecting saved `.env` profiles and runtime overrides (`SAFEDX12=1`, `FSR4=0`, `USE_FSR4=0`, `CONSERVATIVE=1`, explicit `=0` opt-outs, and anti-cheat guards).

---

## 2. Flatscreen Pre-Launch Orchestrator (`bin/steam-auto-run`)

- **Safe `.env` Loading:** Allowlist-only key parser (`load_profile_safe`) supporting CRLF and quoted values while rejecting shell command substitutions (`$(...)`, backticks, `;`) and unknown keys.
- **Discrete GPU & Hardware Detection:** Selects the highest-VRAM discrete GPU (`vram > 2 GiB` and `vram >= best_vram`, or non-`boot_vga` fallback) for `MESA_VK_DEVICE_SELECT`. RDNA 3 / RDNA 4 PCI ID probing runs only when `GPU_VENDOR=amd`.
- **VRR Frame Capping:** Probes active display refresh once (after profile load) via `kscreen-doctor` (Plasma 6 `*` active mode + legacy `Hz` fallback), `wlr-randr`, or `xrandr`. Applies 1:1 refresh by default, `-6%` when `VRR_MINUS_MARGIN=1`, and suppresses DXVK/VKD3D frame caps inside Gamescope unless `VRR_CAP` is explicit.
- **Mutual-Exclusion Invariants & v2.2 Smart Experimental-by-Default Stack Guards:**
  - `ENABLE_VKBASALT=0` whenever `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1`, `USE_OPTISCALER=1`, or `USE_BLEEDING_EDGE=1`.
  - `USE_MLFG=1` enforces `ENABLE_LAYER_MESA_ANTI_LAG=0`, `LOW_LATENCY_LAYER=0`, `LOW_LATENCY_LAYER_REFLEX=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, unsets `DXVK_FRAME_RATE`/`VKD3D_FRAME_RATE`/`DXVK_FRAME_PACE`, and sets `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` on RDNA 3.
  - `competitive-anticheat` forces `USE_OPTISCALER=0`, `USE_MLFG=0`, `USE_REFLEX_LAYER=0`, `USE_BLEEDING_EDGE=0`, `LOW_LATENCY_LAYER=0`, `LOW_LATENCY_LAYER_REFLEX=0`, `PROTON_DXVK_SAREK=0`, `PROTON_DXVK_GPLASYNC=0`, `PROTON_DXVK_LLASYNC=0`, and unsets `PROTON_USE_WOW64`, `PROTON_MEDIA_FORCE_GST`, `VKD3D_FEATURE_LEVEL`, `VKD3D_SHADER_MODEL`, `WAYLANDDRV_RAWINPUT` (while preserving safe driver-level AMD RADV defaults `transfer_queue`, `native_antilag`, and `video_decode`).
  - **Hunt: Showdown 1896 (`AppID 594650`):** Enforces `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, `USE_NET_OPT=1`, and audits `config/config.vdf` `CompatToolMapping` in `--doctor` and `steam-auto-ui` (recommending Valve `Proton 11.0-2` / `Proton Hotfix`).
  - **Smart Experimental-by-Default (`v2.2.0`), Explicit `=0` Opt-Out & `CONSERVATIVE=1`:** Driver-level AMD RADV defaults (`AUTO_NATIVE_ANTILAG=1`, `AUTO_TRANSFER_QUEUE=1` on RDNA 3/4, `AUTO_VK_VIDEO_DECODE=1`) are active across all classes; non-anticheat Proton titles default to `AUTO_BLEEDING_EDGE=1` (`VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1` / `PROTON_FSR4_RDNA3_UPGRADE=1`, `PROTON_NATIVE_AGS=1` on AMD, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, and `WAYLANDDRV_RAWINPUT=1` strictly on native Wayland outside Gamescope; also toggleable via `BLEEDING_EDGE=1`/`BLEEDING_EDGE=0`), and AMD non-anticheat titles shipping Reflex/Streamline/DLSS DLLs auto-activate `USE_REFLEX_LAYER=1`. All shorthand and `USE_*` overrides support explicit `=0` and `=1`, `CONSERVATIVE=1` (`USE_CONSERVATIVE=1`) disables all five experimental defaults cleanly, and older `.env` profiles inherit missing v2.2 keys from detector smart defaults.
  - **Steam Controller 2026 Routing (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`):** Detects Valve `28de:{1302,1304,1005,1007}` via `/sys/bus/usb/devices/*` (`SAP_USB_DIR`). In `wayland-hdr` mode, preserves `winewayland.drv` + `DXVK_HDR=1` without forcing `LD_PRELOAD`, sets `PROTON_USE_SDL=0`, `PROTON_PREFER_SDL=0`, `PROTON_NO_STEAMINPUT=0` (omitting `sdlinput`), spawns an isolated `setsid` watcher process group that triggers `steam steam://forceinputappid/<APPID>` (~3s + ~8s) and re-applies on debounced (`>= 2s`) `udevadm monitor --udev --subsystem-match=hidraw --subsystem-match=usb` wake/reconnect events, and tears down the watcher + resets `steam://forceinputappid/0` inside the unified `EXIT`/`INT`/`TERM` trap. Also exposes `--reapply-input <APPID|0>` and `--with-steam-controller` udev rule installation.
  - `USE_SAFEDX12=0` exports `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` and `vkd3dbindlesstb`; `SAFEDX12=1` omits both.
- **Compat-Token Mapping & Retired Flag Purge:** Appends managed tokens (`wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `lowlatencylayer`, `localshadercache`, `pipewire`, `fsr4`, `wow64`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`) into both `PROTON_ADD_CONFIG` and `STEAM_COMPAT_CONFIG` without clobbering existing values, while purging retired variables (`PROTON_ENABLE_HDR`, `PROTON_VKREFLEX`, `PROTON_MEDIA_USE_GST`, `PROTON_FSR3_UPGRADE`, `PROTON_VKD3D_HEAP`, `WINEPULSE_FAST_POLLING`).
- **Zero-Touch Silent Launch & XWayland SDL Isolation (`v2.3.0`):** `NO_GUI=1` is the default so games with no saved `.env` apply smart defaults and launch immediately with zero interrupting `kdialog`/`zenity` popups (`FORCE_GUI=1` and `--configure <APPID>` remain available on demand). Under `USE_XWAYLAND=1`, both `SDL_VIDEODRIVER=x11` and `SDL_VIDEO_DRIVER=x11` are explicitly exported so inherited `SDL_VIDEO_DRIVER=wayland` from `~/.config/environment.d/` never leaks into XWayland games (e.g. AppID `594650`).
- **Enhanced System Doctor (`--doctor`):** Performs read-only checks for Vulkan RADV extensions (`VK_AMD_anti_lag`, `VK_EXT_descriptor_heap`, `VK_KHR_maintenance12`), CachyOS 261122 gaming stack (`scx_cake`, `bpftune`/`bpftune-gaming`, `cachyos-drm-awaiter`, `game-devices-udev`, `systemd-oomd`), Hunt `594650` `config.vdf` mapping, Steam Controller 2026 udev rules / `power/control=on` / `ModemManager` ignore, and automatic Mesa shader-cleanup pacman hook status (`95-steam-auto-profiler-mesa-shaders.hook` + `pending-shader-cleanup` flag).
- **Auto KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1` by default on Wayland):** Automatically enabled for non-XWayland, non-Gamescope launches when `kscreen-doctor` is present and `DXVK_HDR=1`. Detects the primary enabled output and current HDR state via `kscreen-doctor -o`; skips toggling when desktop HDR is already enabled, or enables HDR from SDR and restores SDR cleanly in the unified `EXIT`/`INT`/`TERM` trap. Honors explicit `AUTO_HDR_SWITCH=0` or `DXVK_NO_HDR=1`.
- **Silent Benchmarks (`BENCH=1`):** Runs MangoHud in `no_display` CSV mode and computes `Avg FPS`, `1% Low FPS`, and `P99 (ms)` into `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`.
- **Silent Two-Stage Self-Healing Fast-Crash Recovery:** Records bounded launch logs (`last-<APPID>.log` & `last-launch.log`, 200 lines max) and per-AppID recovery state (`$XDG_STATE_HOME/steam-auto-profiler/recovery-<APPID>.state`). Non-zero Proton exits `< 20s` trigger non-blocking progressive self-healing (with optional `notify-send` notice): Stage 1 disables experimental flags (`USE_OPTISCALER=0`, `USE_BLEEDING_EDGE=0`, `USE_REFLEX_LAYER=0`, `USE_TRANSFER_QUEUE=0`, `USE_VK_VIDEO_DECODE=0`); Stage 2 escalates repeated fast crashes to `USE_SAFEDX12=1` and `USE_XWAYLAND=1`. Recovery state resets automatically after a healthy `>= 20s` session or via `--reset <APPID>`.
- **VR & Native Linux Isolation:** SteamVR (`250820`) and `-vr`/`--vr` launches bypass orchestration immediately; Native Linux launches strip all `PROTON_*`/`WINE_*`/`DXVK_*`/`VKD3D_*` variables.
- **Scheduler Chain:** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (only if `ananicy-cpp.service` is inactive) -> direct execution (with optional `prime-run` when `PRIME=1`).

---

## 3. VR Orchestrator (`bin/vr-run`)

- Scrubs inherited flatscreen overrides (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Auto-selects the highest-VRAM discrete GPU (`MESA_VK_DEVICE_SELECT`) and sets RADV flags on AMD.
- Probes WiVRn & xrizer OpenXR/OpenVR paths (`~/.local/share/wivrn-slr`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) and configures Steam Linux Runtime pass-through (`PRESSURE_VESSEL_FILESYSTEMS_RO`/`RW`, `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `LD_LIBRARY_PATH`) without overriding user values.
- Manages ref-counted `vr-mode on/off` sessions in `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` guarded by `flock` so switching VR games never toggles `vr-mode` off prematurely.

---

## 4. Unified Control Center (`bin/steam-auto-ui`)

- **Dual Frontend, Shared Backend:** Single-file Python application supporting PyQt6/PySide6 GUI and zero-dependency `curses` TUI backed by `ProfilerBackend`.
- **Non-Blocking & Clean Exit Architecture:**
  - All library scans and telemetry probes run in daemon `threading.Thread` workers bridged to Qt via queued signals (`WorkerBridge`), eliminating `concurrent.futures` `atexit` `t.join()` hangs and Qt `QThread` destruction aborts.
  - Child subprocesses run in their own POSIX session (`start_new_session=True`) and are tracked in `ProfilerBackend._active_procs`. Window `closeEvent`, `app.aboutToQuit`, and `SIGINT` immediately stop timers, set `cancel_event`, terminate/kill active process groups, and exit within `<= 0.2s` with exit status `0`.
- **Zero-Dependency 27-Language i18n:** Auto-detects `LC_ALL`/`LC_MESSAGES`/`LANG`, supports `--lang <code>`, and supports live runtime language switching in both GUI and TUI with automatic fallback to English.

---

## 5. VDF Synchronizer (`bin/steam-auto-sync`), Network Helper (`bin/steam-net-boost`) & Shader Cleaner (`bin/steam-auto-clean-shaders`)

- **`steam-auto-sync`:** Uses span-accurate VDF token editing to modify only `LaunchOptions` values in `localconfig.vdf` while leaving all other keys untouched. Serializes writes with `flock`, creates timestamped backups with `--keep-backups N` pruning, respects `XDG_CONFIG_HOME` across all subcommands (including `--migrate-cachy-run`), automatically assigns `vr-run %command%` to detected VR titles, and reads `shortcuts.vdf` strictly read-only in `--report`.
- **`steam-net-boost`:** Hardens `PATH` under `uid == 0`, validates interface names against `/sys/class/net/` (rejecting whitespace, shell metacharacters, and `..`), refuses symlink state directories in `on`, `off`, and `status`, guards session ref-counting with `flock`, detects and preserves static root CAKE, HTB + leaf CAKE hierarchies, and `wan-cake-shaper.service` / `cake-shaper.service`, and restores pre-existing root qdisc (`cake` vs `fq_codel`), EEE, and `txqueuelen` after the last session exits.
- **`steam-auto-clean-shaders`:** Portable shader cache cleaner (`--dry-run`, `--user <username>`, `--hook`) invoked manually or automatically via `/etc/pacman.d/hooks/95-steam-auto-profiler-mesa-shaders.hook` (`./install.sh --with-mesa-hook`) on `Upgrade` of `mesa`, `mesa-git`, `lib32-mesa`, and `lib32-mesa-git`. Cleans Mesa/RADV/Vulkan/Qt caches safely at all times; when Steam is idle, also clears Steam `shadercache/*` across all `libraryfolders.vdf` paths plus DXVK/VKD3D/DirectX/Unreal caches; when Steam is running, avoids disrupting Steam and writes `$XDG_STATE_HOME/steam-auto-profiler/pending-shader-cleanup`. Strictly protects `PrismLauncher` and `shaderpacks` directories via an explicit path-guard allowlist.

---

## Proton Runtime Compatibility Matrix

| Runtime | Steam Linux Runtime | Recommendation |
| --- | --- | --- |
| `proton-cachyos-slr` | SteamRT3 / SteamRT4 | Recommended for EAC/BattlEye and full CachyOS Wayland/FSR4/MLFG support |
| Valve Official Proton 10 / 11 / Experimental | SteamRT3 / SteamRT4 | Hardware-agnostic upstream baseline |
| Proton-EM 11 | Community CachyOS build | Supports native Wayland, FSR4/MLFG, and controller fixes |
| Proton-GE | Community build | Upstream-compatible defaults; prefer SLR for anti-cheat titles |
