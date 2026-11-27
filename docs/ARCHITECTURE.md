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
- **Actionable Upscaler SDK Info (`AUTO_UPSCALER_INFO`):** Emits human- and machine-readable (`--json`) guidance distinguishing native `PROTON_FSR4_UPGRADE=1` eligible titles from legacy upscaler titles that need `USE_OPTISCALER=1`.
- **Compat-Token Preview:** Computes `AUTO_PROTON_ADD_CONFIG` respecting saved `.env` profiles and runtime overrides (`SAFEDX12=1`, `FSR4=0`, `USE_FSR4=0`, anti-cheat MLFG guard).

---

## 2. Flatscreen Pre-Launch Orchestrator (`bin/steam-auto-run`)

- **Safe `.env` Loading:** Allowlist-only key parser (`load_profile_safe`) supporting CRLF and quoted values while rejecting shell command substitutions (`$(...)`, backticks, `;`) and unknown keys.
- **Discrete GPU & Hardware Detection:** Selects the highest-VRAM discrete GPU (`vram > 2 GiB` and `vram >= best_vram`, or non-`boot_vga` fallback) for `MESA_VK_DEVICE_SELECT`. RDNA 3 / RDNA 4 PCI ID probing runs only when `GPU_VENDOR=amd`.
- **VRR Frame Capping:** Probes active display refresh once (after profile load) via `kscreen-doctor` (Plasma 6 `*` active mode + legacy `Hz` fallback), `wlr-randr`, or `xrandr`. Applies 1:1 refresh by default, `-6%` when `VRR_MINUS_MARGIN=1`, and suppresses DXVK/VKD3D frame caps inside Gamescope unless `VRR_CAP` is explicit.
- **Mutual-Exclusion Invariants:**
  - `ENABLE_VKBASALT=0` whenever `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1`, or `USE_OPTISCALER=1`.
  - `USE_MLFG=1` enforces `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, unsets `DXVK_FRAME_RATE`/`VKD3D_FRAME_RATE`/`DXVK_FRAME_PACE`, and sets `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` on RDNA 3.
  - `competitive-anticheat` forces `USE_OPTISCALER=0`, `USE_MLFG=0`, `PROTON_DXVK_SAREK=0`, `PROTON_DXVK_GPLASYNC=0`, `PROTON_DXVK_LLASYNC=0`.
  - `USE_SAFEDX12=0` exports `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` and `vkd3dbindlesstb`; `SAFEDX12=1` omits both.
- **Compat-Token Mapping:** Appends managed tokens (`wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`) into both `PROTON_ADD_CONFIG` and `STEAM_COMPAT_CONFIG` without clobbering existing values. Retired variables (`PROTON_ENABLE_HDR`, `PROTON_VKREFLEX`, `PROTON_FSR3_UPGRADE`) are never emitted.
- **Auto KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** Detects the primary enabled output and current HDR state via `kscreen-doctor -o`; enables HDR if currently disabled and restores SDR cleanly in an `EXIT`/`INT`/`TERM` trap.
- **Silent Benchmarks (`BENCH=1`):** Runs MangoHud in `no_display` CSV mode and computes `Avg FPS`, `1% Low FPS`, and `P99 (ms)` into `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`.
- **Fast-Crash Safe Mode Auto-Recovery:** Records bounded launch logs (`last-<APPID>.log` & `last-launch.log`, 200 lines max). Non-zero Proton exits `< 20s` with Wayland or experimental DX12 active log a `crash_hint` and prompt to save `USE_XWAYLAND=1` + `USE_SAFEDX12=1`.
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

## 5. VDF Synchronizer (`bin/steam-auto-sync`) & Network Helper (`bin/steam-net-boost`)

- **`steam-auto-sync`:** Uses span-accurate VDF token editing to modify only `LaunchOptions` values in `localconfig.vdf` while leaving all other keys untouched. Serializes writes with `flock`, creates timestamped backups with `--keep-backups N` pruning, respects `XDG_CONFIG_HOME` across all subcommands (including `--migrate-cachy-run`), automatically assigns `vr-run %command%` to detected VR titles, and reads `shortcuts.vdf` strictly read-only in `--report`.
- **`steam-net-boost`:** Hardens `PATH` under `uid == 0`, validates interface names against `/sys/class/net/` (rejecting whitespace, shell metacharacters, and `..`), refuses symlink state directories in `on`, `off`, and `status`, guards session ref-counting with `flock`, detects and preserves static root CAKE, HTB + leaf CAKE hierarchies, and `wan-cake-shaper.service` / `cake-shaper.service`, and restores pre-existing root qdisc (`cake` vs `fq_codel`), EEE, and `txqueuelen` after the last session exits.

---

## Proton Runtime Compatibility Matrix

| Runtime | Steam Linux Runtime | Recommendation |
| --- | --- | --- |
| `proton-cachyos-slr` | SteamRT3 / SteamRT4 | Recommended for EAC/BattlEye and full CachyOS Wayland/FSR4/MLFG support |
| Valve Official Proton 10 / 11 / Experimental | SteamRT3 / SteamRT4 | Hardware-agnostic upstream baseline |
| Proton-EM 11 | Community CachyOS build | Supports native Wayland, FSR4/MLFG, and controller fixes |
| Proton-GE | Community build | Upstream-compatible defaults; prefer SLR for anti-cheat titles |
