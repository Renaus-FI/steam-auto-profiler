# Steam Auto-Profiler User Guide

This guide covers the complete installation, zero-touch silent flatscreen & VR launch orchestration, `steam-auto-ui` Control Center, library synchronization, benchmarking, Steam Controller 2026 Wayland+HDR routing, v2.4 zero-touch smart defaults (Smart Auto-AFMF via user-space `afmf-linux`, Auto-OptiScaler, Auto KDE Plasma 6 HDR, Mesa 27.0 / RADV / Proton-CachyOS 11.0 stack, silent two-stage fast-crash self-healing, automatic Mesa shader cache cleanup), `CONSERVATIVE=1` opt-out, and troubleshooting workflow for **Steam Auto-Profiler v2.4**.

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

`./install.sh` copies all seven executables (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run`, `steam-auto-ui`, and `steam-auto-clean-shaders`) into `~/.local/bin`, installs the desktop entry (`~/.local/share/applications/steam-auto-profiler.desktop`), creates `~/.config/steam-auto-profiler/profiles`, and adds default vkBasalt presets (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Ensure `~/.local/bin` is in `PATH`.

Optional installer flags may be combined:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync --with-steam-controller --with-mesa-hook
```

- `--with-net-boost`: installs `/usr/local/bin/steam-net-boost` (plus system copies of the other scripts) and a narrowly scoped passwordless sudoers rule for `steam-net-boost`.
- `--compat-cachy-run`: preserves an existing `/usr/local/bin/cachy-run` as `/usr/local/bin/cachy-run.bak` (unless it is already the Steam Auto-Profiler shim) and installs a forwarding shim to `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): installs and enables the systemd user `steam-auto-profiler-sync.path` watcher and matching oneshot service across all discovered Steam libraries.
- `--with-steam-controller`: installs `/etc/udev/rules.d/61-steam-controller-2026.rules` for Steam Controller 2026 (`Triton`/`Proteus`) and Wireless Steam Puck (`28de:{1302,1304,1005,1007}`) with `uaccess`/`uucp` `hidraw` + `ttyACM*` firmware permissions, `ID_MM_DEVICE_IGNORE=1` (`ModemManager` ignore), and zero-latency disabled USB selective suspend (`power/control=on`, `power/autosuspend=-1`).
- `--with-mesa-hook`: installs `/usr/local/bin/steam-auto-clean-shaders` and `/etc/pacman.d/hooks/95-steam-auto-profiler-mesa-shaders.hook` triggered on `Upgrade` of `mesa`, `mesa-git`, `lib32-mesa`, and `lib32-mesa-git` so Mesa updates wipe stale shader caches automatically.
- `--uninstall`: removes installed binaries, desktop entry, optional network helper/sudoers rule, Steam Controller udev rules, Mesa pacman hook, compatibility shim, and systemd user auto-sync units.

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
   - **Smart Experimental-by-Default Matrix (`v2.2.0` — Mesa 27.0 / RDNA 4 & Reflex -> Anti-Lag 2):**
     - **Driver-Level AMD RADV Defaults (Safe on ALL classes including `competitive-anticheat`):** `USE_TRANSFER_QUEUE=1` (AMD RDNA 3/4 -> deduplicated `RADV_PERFTEST=sam,transfer_queue`), `USE_NATIVE_ANTILAG=1` (AMD, when `USE_MLFG=0` -> Mesa 26.3+/27.0 native `VK_AMD_anti_lag` with `ENABLE_LAYER_MESA_ANTI_LAG=0`), and `USE_VK_VIDEO_DECODE=1` (AMD -> deduplicated `RADV_EXPERIMENTAL=video_decode`, migrating legacy `RADV_PERFTEST=video_decode`).
     - **Ultra Bleeding-Edge Default (`USE_BLEEDING_EDGE=1` / `BLEEDING_EDGE=0|1`):** Enabled by default on non-anticheat Proton titles (`AUTO_CLASS != competitive-anticheat`, `AUTO_NATIVE_LINUX == 0`, `APPID != 594650`), exporting `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1` on RDNA 4 (`PROTON_FSR4_RDNA3_UPGRADE=1` on RDNA 3), `PROTON_NATIVE_AGS=1` on AMD, `PROTON_USE_WOW64=1` (`wow64`), `PROTON_MEDIA_FORCE_GST=1`, and `WAYLANDDRV_RAWINPUT=1` (exported **only** when `USE_XWAYLAND=0` and `GAMESCOPE_SESSION=0`, explicitly unset otherwise). Hard-blocked (`=0`) in `competitive-anticheat`, `AppID 594650`, and native Linux games. (Explicit `BLEEDING_EDGE=1` also remains supported.)
     - **Smart Reflex -> Anti-Lag 2 Auto-Activation (`USE_REFLEX_LAYER=1` / `REFLEX_LAYER=0|1`):** Automatically activates `LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1` (`lowlatencylayer` token, `ENABLE_LAYER_MESA_ANTI_LAG=0`) on AMD non-anticheat Proton games shipping `sl.reflex.dll`, `sl.interposer.dll`, or `nvngx_dlss*.dll` (`AUTO_HAS_REFLEX=1`). Automatically disabled when `MLFG=1` and hard-blocked (`=0`) on `competitive-anticheat` and native Linux games.
     - **Auto-OptiScaler (`AUTO_OPTISCALER=1` on AMD RDNA 3/4 `legacy-upscaler`):** Automatically activates `USE_OPTISCALER=1` (`PROTON_USE_OPTISCALER=1`, `PROTON_OPTISCALER_STREAMLINE=1`, `ENABLE_VKBASALT=0`) on AMD RDNA 3/4 non-anticheat Proton titles shipping DLSS/XeSS/FSR 2 DLLs without native FSR 3.1+, and mutually excludes `USE_AFMF=1` (`DISABLE_AFMF=1`) so OptiScaler and `VK_LAYER_AFMF` never stack on the swapchain. Hard-locked off on `competitive-anticheat`, `AppID 594650`, `AppID 2483190`, `AppID 548430`, and native Linux; opt out anytime via `OPTISCALER=0`, `USE_OPTISCALER=0`, or `CONSERVATIVE=1`.
     - **Unreal Engine 4/5 & RDNA 4 Compute-Ring Stability Guards (`v2.4.3`, `AUTO_ENGINE_UE=1`):** Detects UE4/UE5 layouts (`*-Win64-Shipping.exe`, `Engine/Binaries/Win64`, `*.pak` / `*.ucas` / `*.utoc`), defaults `USE_TRANSFER_QUEUE=0` and `USE_BLEEDING_EDGE=0` on AMD RADV unless explicitly requested (keeping `PROTON_FSR4_UPGRADE=1`, `RADV_PERFTEST=sam`, and safe `VKD3D_CONFIG` defaults), and applies dedicated RDNA 4 compute-ring hang guards to Forza Horizon 6 (`2483190`) and Deep Rock Galactic (`548430`).
     - **Zero-Touch Smart Auto-AFMF (`v2.4.0`, `AUTO_AFMF=1`):** When user-space `afmf-linux` (`VK_LAYER_AFMF`, env-gated via `enable_environment: {"AFMF_ENABLE": "1"}`) is installed under `~/.local/share/vulkan/implicit_layer.d/` + `~/.local/lib/`, `steam-auto-detect` scans for built-in Frame Generation libraries (`amd_fidelityfx_framegeneration*.dll`, `ffx_fsr3fg*.dll`, `ffx_frameinterpolation*.dll`, `nvngx_dlssg.dll`, `sl.dlss_g.dll`, `libxefg*.dll`, `xefg*.dll`, OptiScaler FG -> `AUTO_HAS_NATIVE_FG=1`) and Steam tools / 2D / Electron-only apps (`AUTO_IS_TOOL_OR_2D=1`). Eligible 3D non-anticheat, non-VR titles automatically activate `USE_AFMF=1` (`AFMF_ENABLE=1`, `AFMF_PACING=1`, `AFMF_PRESENT_MODE=auto`, `AFMF_GAMESCOPE=1` under Gamescope), halve `DXVK_FRAME_RATE` / `VKD3D_FRAME_RATE` to `floor(VRR_CAP / 2)` (e.g. `120 FPS` base on 240 Hz VRR), keep native RADV low-latency Anti-Lag enabled (`ENABLE_LAYER_MESA_ANTI_LAG=0`), mutually exclude `MLFG=1`, and hard-lock `DISABLE_AFMF=1` on `competitive-anticheat`, `AppID 594650`, `vr`, and `vr-run`. Opt out anytime via `AFMF=0`, `USE_AFMF=0`, or `CONSERVATIVE=1`.
     - **Explicit `=0` Opt-Out, `CONSERVATIVE=1` & Profile Inheritance:** Any shorthand (`AFMF=0`, `OPTISCALER=0`, `AUTO_HDR_SWITCH=0`, `BLEEDING_EDGE=0`, `TRANSFER_QUEUE=0`, `NATIVE_ANTILAG=0`, `REFLEX_LAYER=0`, `VK_VIDEO_DECODE=0`) or `.env` key (`USE_*=0`) cleanly overrides smart `=1` defaults; `CONSERVATIVE=1` (`USE_CONSERVATIVE=1`) disables all experimental defaults at once; older `.env` files missing newer keys inherit smart defaults automatically. `USE_MLFG` and `USE_XWAYLAND` remain opt-in (`=0`) by default.
     - **Zero-Touch Silent Launches & XWayland SDL Isolation (`v2.3.0`):** `NO_GUI=1` is the default so games without a saved `.env` launch immediately with zero interrupting `kdialog`/`zenity` dialogs (opt in via `FORCE_GUI=1` or `steam-auto-run --configure <APPID>`, or use `steam-auto-ui`). Under `USE_XWAYLAND=1`, both `SDL_VIDEODRIVER=x11` and `SDL_VIDEO_DRIVER=x11` are explicitly exported to prevent inherited `SDL_VIDEO_DRIVER=wayland` from leaking into XWayland games such as AppID `594650`.
   - **Hunt: Showdown 1896 (`AppID 594650`) Compatibility Guard:** Enforces `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, and `USE_NET_OPT=1` without conflicting with `USE_STEAM_CONTROLLER`. Both `steam-auto-run --doctor` and `steam-auto-ui` inspect Steam `config/config.vdf` `CompatToolMapping` for `594650` and warn if unset or set to `proton-cachyos*` (recommending Valve's `Proton 11.0-2` or `Proton Hotfix`).
   - **Steam Controller 2026 & Wireless Steam Puck (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`):**
     - `auto` (default): detects Valve 2026 hardware (`28de:{1302,1304,1005,1007}`) via `/sys/bus/usb/devices/*` and selects `wayland-hdr` on Wayland sessions (or `xwayland` on X11).
     - `wayland-hdr`: preserves native `winewayland.drv` + OLED HDR10 (`USE_XWAYLAND=0`, `PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`) without forcing `LD_PRELOAD` overlay overhead, exports `PROTON_USE_SDL=0`, `PROTON_PREFER_SDL=0`, `PROTON_NO_STEAMINPUT=0` (omitting `sdlinput`), launches a background watcher that applies `steam steam://forceinputappid/<APPID>` (~3s + ~8s confirmation nudge) and monitors `udevadm monitor --udev --subsystem-match=hidraw --subsystem-match=usb` (debounced >= 2s) to re-apply on mid-game controller sleep/reconnect, and resets `steam://forceinputappid/0` in the unified `EXIT`/`INT`/`TERM` trap.
     - `xwayland`: fallback forcing `USE_XWAYLAND=1`, `USE_KEEP_OVERLAY=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0` (omitting `sdlinput`) for engines requiring XWayland Steam Input.
     - `off` (`0`): disables all Steam Controller routing overrides. Legacy `USE_STEAM_CONTROLLER=1` maps to `wayland-hdr` on Wayland or `xwayland` on X11.
   - **Modern DX12 + Safe DX12:** Exports `PROTON_NATIVE_AGS=1` on AMD and `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` when `USE_SAFEDX12=0` (cleanly omitted when `SAFEDX12=1`).
6. **Compat-Token Mapping & Retired Flag Purge:** Managed features are appended without clobbering existing user values into both `PROTON_ADD_CONFIG` and `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `lowlatencylayer`, `localshadercache`, `pipewire`, `fsr4`, `wow64`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`. Retired Proton/Wine variables (`PROTON_ENABLE_HDR`, `PROTON_VKREFLEX`, `PROTON_MEDIA_USE_GST`, `PROTON_FSR3_UPGRADE`, `PROTON_VKD3D_HEAP`, `WINEPULSE_FAST_POLLING`) are purged on launch and stripped during `steam-auto-sync --sanitize`.
7. **Auto KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1` by default on Wayland):** Enabled automatically for non-XWayland, non-Gamescope launches when `kscreen-doctor` is available and `DXVK_HDR=1` (or `USE_HDR=1`). Probes the primary enabled output via `kscreen-doctor -o`: if desktop HDR is already enabled, performs a zero-flicker no-op; if disabled, enables HDR before launch and restores SDR in the unified `EXIT`/`INT`/`TERM` trap. Opt out with `AUTO_HDR_SWITCH=0` or `DXVK_NO_HDR=1`.
8. **Silent Frametime Benchmarking (`BENCH=1`):** Runs MangoHud in hidden CSV mode (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), parses frametimes on exit, appends `Avg FPS`, `1% Low FPS`, and `P99 (ms)` to `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`, and removes temporary CSVs.
9. **Silent Escalating 3-Stage Self-Healing Crash Recovery (`v2.4.3`):** Automatically catches both fast/delayed crashes (`< 60s` non-zero exit, configurable via `SAP_CRASH_THRESHOLD_SEC`, so UE4 `CrashReportClient.exe` delays are never missed) AND kernel `amdgpu` GPU-hang / ring-timeout events (`journalctl`), Wine/Proton segfault coredumps (`coredumpctl`), or `CrashReportClient` / `VkResult` / `EXCEPTION_ACCESS_VIOLATION` signatures (even when Steam's `reaper`/`proton` wrapper returns `exit_code=0`). Escalates deterministically per AppID (visible in `--inspect` and `steam-auto-sync --report`):
   - **Failure 1 -> Stage 1 (`SAFE_LAYERS`):** persists `USE_AFMF=0`, `USE_OPTISCALER=0`, `USE_BLEEDING_EDGE=0`, `USE_REFLEX_LAYER=0`, `USE_TRANSFER_QUEUE=0`, `USE_VK_VIDEO_DECODE=0`, purges the game's Steam shader caches (`mesa_shader_cache_sf`, `VKD3D_shader_cache`, `DXVK_state_cache`, `radv_builtin_shaders`), and records `RECOVERY_STAGE=1` / `RECOVERY_MODE=SAFE_LAYERS` in `$XDG_STATE_HOME/steam-auto-profiler/recovery-<APPID>.state`.
   - **Failure 2 -> Stage 2 (`CONSERVATIVE_XWAYLAND`):** escalates to `CONSERVATIVE=1`, `USE_SAFEDX12=1`, `USE_XWAYLAND=1`, `PROTON_ENABLE_WAYLAND=0`, `PROTON_USE_WOW64=0`, `PROTON_FSR4_UPGRADE=0`, `RADV_PERFTEST=sam` (`RECOVERY_STAGE=2`).
   - **Failure 3+ -> Stage 3 (`SAFE_BASELINE`):** persists `USE_SAFE_BASELINE=1` and strips optional Proton/DXVK/VKD3D overrides down to minimal clean Proton defaults (`RECOVERY_STAGE=3`).
   - The consecutive crash counter resets automatically after a clean session (`>= 120s`, `exit_code=0`, zero crash signals) while **preserving** the working `.env` recovery profile override that made the game succeed. Use `steam-auto-run --reset <APPID>` (or **Reset Profile** in `steam-auto-ui`) to wipe both the `.env` profile and recovery state. Steam Controller 2026 Desktop layout restoration (`steam://forceinputappid/413080` + `0`) runs unconditionally in the `EXIT` trap on every crash.
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

1. **Games & Profiles:** Filterable table of Steam titles and read-only Non-Steam `shortcuts.vdf` entries (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), Upscaler SDK badge (`AUTO_UPSCALER_INFO`), smart-default pre-population & live mutual-exclusion validation across all 17 profile controls (including `AFMF Frame Generation (afmf-linux)` with automatic lock/tooltip on `competitive-anticheat`/`vr`, `Transfer Queue`, `Native RADV Anti-Lag`, `Reflex -> Anti-Lag 2`, `Vulkan Video Decode`, `Ultra Bleeding-Edge`, and the 4-mode `Steam Controller 2026 / Puck Routing` selector: `Auto`, `Wayland + HDR`, `XWayland`, `Off`) + `VRR_CAP`, `Dry-Run Preview`, `Benchmarks` jump button, and `Reset Profile` (immediately reloading smart defaults and Dry-Run output).
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

- Scrubs inherited flatscreen overrides (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`, `AFMF_ENABLE`, `AFMF_GAMESCOPE`, `AFMF_PACING`, `AFMF_PRESENT_MODE`) and explicitly exports `DISABLE_AFMF=1`.
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
| Clean Mesa/Steam shader caches | `steam-auto-clean-shaders [--dry-run] [--user USER]` |
| Inspect network helper (read-only) | `steam-net-boost status [IFACE]` |

### Saved `.env` Profile Keys & Environment Overrides

Profile files live at `~/.config/steam-auto-profiler/profiles/<APPID>.env` and accept an allowlisted `KEY=VALUE` format (shell command substitutions and unknown keys are safely ignored):

| `.env` Key | Env Override | Effect |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Force XWayland instead of native Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Disable driver-level FSR 4 upgrade (default `1`) |
| `USE_MLFG=1` | `MLFG=1` | Enable frame generation (disables Anti-Lag, AFMF, low-latency, and VRR frame caps) |
| `USE_AFMF=0\|1` | `AFMF=0\|1` | User-space `afmf-linux` (`VK_LAYER_AFMF`) frame generation (auto `1` on eligible 3D non-AC/non-VR titles without native FG; halves VRR cap to `floor(VRR_CAP / 2)`; mutually exclusive with `MLFG=1`; hard-locked off on anti-cheat / `594650` / VR) |
| `USE_OPTISCALER=0\|1` | `OPTISCALER=0\|1` | OptiScaler bridge (auto `1` on AMD RDNA 3/4 `legacy-upscaler` titles; guarded off for `competitive-anticheat`) |
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
| `AUTO_HDR_SWITCH=0\|1` | `AUTO_HDR_SWITCH=1` (`=0` opts out) | Auto-enable KDE Plasma 6 HDR on launch and restore SDR on exit (default `1` on Wayland when `kscreen-doctor` & `DXVK_HDR=1`) |
| `USE_TRANSFER_QUEUE=0\|1` | `TRANSFER_QUEUE=0\|1` | RDNA 3/4 SDMA queue `RADV_PERFTEST=sam,transfer_queue` (default `1` on AMD RDNA 3/4; `0` opts out) |
| `USE_NATIVE_ANTILAG=0\|1` | `NATIVE_ANTILAG=0\|1` | Mesa 26.3+/27.0 native RADV `VK_AMD_anti_lag` (`ENABLE_LAYER_MESA_ANTI_LAG=0`; default `1` on AMD) |
| `USE_REFLEX_LAYER=0\|1` | `REFLEX_LAYER=0\|1` | Proton-CachyOS `LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1` (auto `1` on AMD non-anticheat titles with Reflex/Streamline/DLSS DLLs; blocked in anti-cheat / MLFG) |
| `USE_VK_VIDEO_DECODE=0\|1` | `VK_VIDEO_DECODE=0\|1` | Mesa 27.0 Vulkan video decode via `RADV_EXPERIMENTAL=video_decode` (default `1` on AMD; `0` opts out) |
| `USE_BLEEDING_EDGE=0\|1` | `BLEEDING_EDGE=0\|1` | Ultra Bleeding-Edge Mesa 27 / VKD3D `12_2` / SM `6_8` / WoW64 / GStreamer / RawInput stack (default `1` on non-anticheat Proton titles; hard-blocked on anti-cheat / `594650` / native Linux) |
| `USE_CONSERVATIVE=1` | `CONSERVATIVE=1` | Master opt-out disabling all experimental defaults (`USE_AFMF`, `USE_OPTISCALER`, `USE_BLEEDING_EDGE`, `USE_TRANSFER_QUEUE`, `USE_NATIVE_ANTILAG`, `USE_REFLEX_LAYER`, `USE_VK_VIDEO_DECODE`) |
| `USE_STEAM_CONTROLLER=auto\|wayland-hdr\|xwayland\|off` | `STEAM_CONTROLLER=...` | Route Steam Controller 2026 / Puck (`28de:{1302,1304,1005,1007}`): `wayland-hdr` keeps native Wayland+HDR + `forceinputappid` & reconnect watcher; `xwayland` fallback; `off` disables (legacy `1`/`0` supported) |
| — | `BENCH=1`, `BENCH_DURATION=60` | Run silent MangoHud CSV benchmark and save JSON summary |
| — | `NO_GUI=0\|1` / `FORCE_GUI=1` | Silent launch is default (`NO_GUI=1`); set `FORCE_GUI=1` or `NO_GUI=0` to open the pre-launch `kdialog`/`zenity` checklist |
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
