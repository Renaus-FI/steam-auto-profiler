# Steam Auto-Profiler

[![CI](https://github.com/Renaus-FI/steam-auto-profiler/actions/workflows/ci.yml/badge.svg)](https://github.com/Renaus-FI/steam-auto-profiler/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Renaus-FI/steam-auto-profiler/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Renaus-FI/steam-auto-profiler/security/code-scanning)
[![Release](https://img.shields.io/badge/Release-v2.4.1-brightgreen.svg)](https://github.com/Renaus-FI/steam-auto-profiler/releases/tag/v2.4.1)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Context-aware heuristic game classifier, VR/flatscreen pre-launch orchestrator, and unified Qt6/TUI control center for Steam on Linux.**

Steam Auto-Profiler inspects your local Steam libraries and Non-Steam `shortcuts.vdf` entries, classifies each title with deterministic priority rules, enforces driver/upscaler/anti-cheat mutual-exclusion guardrails, and launches flatscreen and VR games cleanly without hand-maintained launch option strings.

---

## Highlights

- **100% Zero-Touch Smart Automatic AFMF Routing (`v2.4.0`, `afmf-linux`):** Automatically activates user-space `VK_LAYER_AFMF` (`AFMF_ENABLE=1`, `AFMF_PACING=1`, `AFMF_PRESENT_MODE=auto`, `AFMF_GAMESCOPE=1` under Gamescope) ONLY when `afmf-linux` is installed on the host and the title is a 3D non-anticheat, non-VR game without built-in native Frame Generation (`AUTO_HAS_NATIVE_FG=0`, `AUTO_IS_TOOL_OR_2D=0`). Automatically halves `DXVK_FRAME_RATE` / `VKD3D_FRAME_RATE` (`floor(VRR_CAP / 2)`, e.g. `120 FPS` base -> `240 FPS` output on 240 Hz VRR), keeps native RADV Anti-Lag low-latency active, mutually excludes `MLFG=1`, hard-locks off (`DISABLE_AFMF=1`) on `competitive-anticheat`, `AppID 594650`, `vr`, and `vr-run`, and auto-disables permanently in Stage 1 `< 20s` crash self-healing.
- **100% Zero-Touch Silent Flatscreen Orchestration (`steam-auto-run`):** Click Play & Forget — silent launches by default (`NO_GUI=1`, zero interrupting `kdialog`/`zenity` popups; interactive dialogs on demand via `FORCE_GUI=1` or `--configure <APPID>`), native Wine Wayland + HDR (`DXVK_HDR=1`, `WAYLANDDRV_SHORTCUT_INHIBIT=0`), XWayland `SDL_VIDEODRIVER=x11` + `SDL_VIDEO_DRIVER=x11` isolation, automatic monitor-refresh VRR capping (`240 FPS` 1:1 on 240 Hz, `120 FPS` half-cap when AFMF active, optional `-6%` headroom `225 FPS` / `112 FPS` via `VRR_MINUS_MARGIN=1`, automatic Gamescope bypass), `PROTON_ADD_CONFIG` / `STEAM_COMPAT_CONFIG` token mapping, and `ananicy-cpp`-aware scheduler chaining.
- **Dedicated VR Launch Orchestrator (`vr-run`):** Scrubs flatscreen VRR/Wayland/Anti-Lag/vkBasalt/MLFG/AFMF overrides (`unset AFMF_ENABLE`, `DISABLE_AFMF=1`), auto-selects the discrete GPU (`MESA_VK_DEVICE_SELECT`), probes WiVRn & xrizer OpenXR/OpenVR paths for Steam Linux Runtime pass-through, and manages ref-counted `vr-mode on/off` sessions (`VR_AUTO_MODE=1`).
- **Unified Qt6 GUI & `curses` TUI Control Center (`steam-auto-ui`):** Five live views (Games & Profiles, System & Telemetry, Library Sync, Logs & Recovery, Benchmarks), 27 built-in UI languages with live runtime switching (`--lang <code>`), smart-default pre-population (`AUTO_OPTISCALER`, `AUTO_HDR_SWITCH`, Mesa 27/RADV), non-blocking background workers, and clean instant window/SIGINT shutdown.
- **Non-Steam Shortcuts (`shortcuts.vdf`):** Safely parsed read-only across `steam-auto-detect`, `steam-auto-sync --report`, and `steam-auto-ui` with per-shortcut `.env` profile support and `vr-run` preservation.
- **Auto-OptiScaler & Upscaler DLL SDK Hints (`AUTO_OPTISCALER=1`, `AUTO_UPSCALER_INFO`):** Distinguishes FidelityFX 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amdxcffx64.dll` -> native `PROTON_FSR4_UPGRADE=1`) from legacy FSR 2 / DLSS / XeSS DLLs, automatically activating `USE_OPTISCALER=1` (`PROTON_USE_OPTISCALER=1`, `PROTON_OPTISCALER_STREAMLINE=1`, `ENABLE_VKBASALT=0`) on AMD RDNA 3/4 non-anticheat Proton titles while keeping anti-cheat / `594650` / native Linux hard-locked off.
- **Automatic KDE Plasma 6 HDR Switch (`AUTO_HDR_SWITCH=1` by default on Wayland):** Automatically enables HDR on the primary output via `kscreen-doctor` before non-XWayland, non-Gamescope launches when `DXVK_HDR=1` and desktop HDR is disabled, restores SDR cleanly on exit, and performs a zero-flicker no-op when desktop HDR is already active (opt out via `AUTO_HDR_SWITCH=0` or `DXVK_NO_HDR=1`).
- **Silent Frametime Benchmarks (`BENCH=1`):** Runs hidden MangoHud CSV logging (`no_display`), computes `Avg FPS`, `1% Low FPS`, and `P99 (ms)` into `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`, and compares runs side-by-side in `steam-auto-ui`.
- **Silent Two-Stage Self-Healing Fast-Crash Recovery:** Replaces blocking crash dialogs with non-blocking progressive self-healing on Proton exits `< 20s` (with optional `notify-send`): Stage 1 disables experimental flags (`USE_AFMF=0`, `USE_OPTISCALER=0`, `USE_BLEEDING_EDGE=0`, `USE_REFLEX_LAYER=0`, `USE_TRANSFER_QUEUE=0`, `USE_VK_VIDEO_DECODE=0`); Stage 2 escalates repeated fast crashes to `USE_SAFEDX12=1` + `USE_XWAYLAND=1`, tracking `RECOVERY_STAGE` in `$XDG_STATE_HOME/steam-auto-profiler/` and auto-resetting after a healthy `>= 20s` run or `--reset <APPID>`.
- **Automatic Mesa Upgrade Shader Cache Cleanup (`steam-auto-clean-shaders` & `--with-mesa-hook`):** Portable cleaner (`--dry-run`, `--user <username>`) and optional pacman post-transaction hook (`95-steam-auto-profiler-mesa-shaders.hook`) triggered on `mesa` / `mesa-git` / `lib32-mesa` / `lib32-mesa-git` upgrades that safely clears Mesa/RADV/Vulkan/Qt, Steam `shadercache/*`, and DXVK/VKD3D/DirectX/Unreal caches while strictly preserving `PrismLauncher` shaderpacks and never disrupting running Steam processes.
- **HTB + CAKE Network QoS Protection (`steam-net-boost`):** Recognizes static root CAKE, LAN-exempted HTB + leaf CAKE hierarchies, and `wan-cake-shaper.service` / `cake-shaper.service`; restores pre-existing qdisc, EEE, and `txqueuelen` atomically with `flock`.

---

## Classification Priority

| Priority | Class | Detection Signal | Default Behavior |
| --- | --- | --- | --- |
| 1 | `competitive-anticheat` | Known competitive AppID or anti-cheat runtime files (EAC, BattlEye, Ricochet, ACE, etc.) | Disables OptiScaler, MLFG, vkBasalt, and async DXVK; enables low-latency and session network QoS |
| 2 | `vr` | VR runtimes/manifests (`openvr_api.dll`, `openxr_loader.dll`, `*.vrmanifest`, or `vr-run` shortcut) | Exports `AUTO_IS_VR=1`; `steam-auto-sync` assigns and preserves `vr-run %command%` automatically |
| 3 | `native-fsr4` / `native-fsr` | Modular FidelityFX SDK 3.1+ / `amdxcffx64.dll` | Prefers native driver-level `PROTON_FSR4_UPGRADE=1` / `PROTON_FSR4_RDNA3_UPGRADE=1` |
| 4 | `legacy-upscaler` | DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline, or FSR 2/3.0 DLLs | Auto-enables `USE_OPTISCALER=1` on AMD RDNA 3/4 (opt-out via `OPTISCALER=0` / `CONSERVATIVE=1`) and upstream `PROTON_*_UPGRADE=1` fallback |
| 5 | `standard` | No anti-cheat, VR, or modern upscaler detected | Uses safe native Wayland + low-latency VRR profile |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

Optional installer flags can be combined:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync --with-steam-controller --with-mesa-hook
```

- `--with-net-boost`: installs `/usr/local/bin/steam-net-boost` + scoped passwordless sudoers rule.
- `--compat-cachy-run`: preserves `/usr/local/bin/cachy-run` as `.bak` and installs a forwarding shim.
- `--with-auto-sync`: installs and enables the systemd user `steam-auto-profiler-sync.path` watcher.
- `--with-steam-controller`: installs `/etc/udev/rules.d/61-steam-controller-2026.rules` for Steam Controller 2026 (`Triton`/`Proteus`) and Wireless Steam Puck (`28de:{1302,1304,1005,1007}`) with `uaccess`/`uucp` `hidraw` + `ttyACM*` permissions, `ModemManager` ignore, and zero-latency disabled USB selective suspend.
- `--with-mesa-hook`: installs `/usr/local/bin/steam-auto-clean-shaders` and `/etc/pacman.d/hooks/95-steam-auto-profiler-mesa-shaders.hook` to automatically wipe stale Mesa/RADV/Steam shader caches on `mesa` / `mesa-git` / `lib32-mesa` / `lib32-mesa-git` upgrades.
- `--uninstall`: cleanly removes all installed binaries, desktop entry, shim, sudoers rule, udev rules, Mesa pacman hook, and user units.

### 2. Audit & Launch Templates

```bash
# Read-only CachyOS / Linux gaming readiness audit
steam-auto-run --doctor

# Inspect any Steam AppID or Non-Steam shortcut without launching
steam-auto-run --inspect 2357570
steam-auto-detect --inspect --json 2357570

# Open the unified Control Center (auto-selects Qt6 GUI or curses TUI)
steam-auto-ui
steam-auto-ui --gui --lang fi
steam-auto-ui --tui
steam-auto-ui --check
```

**Steam Launch Options Templates:**

```text
# Standard / Competitive flatscreen games
steam-auto-run %command%

# VR titles (OpenXR / WiVRn / xrizer / SteamVR)
vr-run %command%

# Frame generation (automatically disables Anti-Lag, AFMF & VRR caps)
MLFG=1 steam-auto-run %command%

# Opt out of automatic afmf-linux frame generation on a specific title
AFMF=0 steam-auto-run %command%

# Silent 60s MangoHud frametime benchmark + Auto KDE Plasma 6 HDR
BENCH=1 AUTO_HDR_SWITCH=1 steam-auto-run %command%

# Optional -6% VRR safety margin (e.g. 225 FPS on 240 Hz)
VRR_MINUS_MARGIN=1 steam-auto-run %command%

# Baseline conservative mode (disables all v2.2 experimental defaults)
CONSERVATIVE=1 steam-auto-run %command%

# Lutris / Heroic / UMU Launcher
GAMEID=umu-2357570 steam-auto-run %command%
```

### 3. Batch Library Sync (Close Steam First)

```bash
steam-auto-sync --report              # Read-only table (Steam + Non-Steam shortcuts)
steam-auto-sync --dry-run             # Preview launch option updates
steam-auto-sync                       # Apply steam-auto-run / vr-run across libraries
steam-auto-sync --sanitize --dry-run  # Preview cleanup of legacy/orphan flags
steam-auto-sync --sanitize            # Clean messy launch strings (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migrate ~/.config/cachy-run/profiles/*.env
```

---

## Architecture & Guardrails

Steam Auto-Profiler consists of seven focused tools in `bin/`:

| Tool | Role |
| --- | --- |
| `steam-auto-run` | Zero-touch silent flatscreen orchestrator, `--doctor`, `--ui`, `--last-log`, `--list-profiles`, `BENCH=1`, `AUTO_HDR_SWITCH=1` (default on Wayland), two-stage silent self-healing |
| `vr-run` | Dedicated VR orchestrator, flatscreen override scrubbing, dGPU selection, WiVRn/xrizer probing, ref-counted `vr-mode` |
| `steam-auto-ui` | Unified PyQt6/PySide6 GUI & stdlib `curses` TUI control center with 27-language live i18n and live stack/GPU/QoS telemetry |
| `steam-auto-detect` | Single-pass game directory & `shortcuts.vdf` heuristic classifier (`AUTO_CLASS`, `AUTO_OPTISCALER`, `AUTO_IS_VR`, `AUTO_UPSCALER_INFO`, `--json`) |
| `steam-auto-sync` | `flock`-protected VDF span editor for `localconfig.vdf`, VR auto-assignment, `--sanitize`, `--migrate-cachy-run`, `--keep-backups N` |
| `steam-net-boost` | Optional `flock`-protected session QoS helper (`on`/`off`/`status`) preserving static root CAKE and HTB + CAKE hierarchies |
| `steam-auto-clean-shaders` | Safe Mesa/RADV/Vulkan/Qt/Steam/DXVK/VKD3D/Unreal shader cache cleaner (`--dry-run`, `--user`, `--hook`) preserving `PrismLauncher` shaderpacks |

Key built-in mutual-exclusion rules:
- **FSR 4 / OptiScaler vs vkBasalt:** `ENABLE_VKBASALT=0` is enforced whenever `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1`, or `USE_OPTISCALER=1` (prevents double-sharpening and HDR10 clipping).
- **MLFG vs Low-Latency / VRR Caps:** `MLFG=1` sets `ENABLE_LAYER_MESA_ANTI_LAG=0`, `LOW_LATENCY_LAYER=0`, `LOW_LATENCY_LAYER_REFLEX=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, unsets `DXVK_FRAME_RATE` / `VKD3D_FRAME_RATE` / `DXVK_FRAME_PACE`, and adds `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` on AMD RDNA 3.
- **Smart Experimental-by-Default Matrix (`v2.2.0` — Mesa 27.0 / RDNA 4 & Proton-CachyOS 11.0):**
  - **Driver-Level AMD RADV Defaults (Safe across ALL classes including `competitive-anticheat`):**
    - `USE_TRANSFER_QUEUE=1` (`TRANSFER_QUEUE=0|1`): automatically enabled on AMD RDNA 3/4 GPUs, exporting deduplicated `RADV_PERFTEST=sam,transfer_queue` (dedicated SDMA queue).
    - `USE_NATIVE_ANTILAG=1` (`NATIVE_ANTILAG=0|1`): automatically enabled on AMD GPUs (when `USE_MLFG=0`), using Mesa 26.3+/27.0 driver-native `VK_AMD_anti_lag` (`ENABLE_LAYER_MESA_ANTI_LAG=0`) instead of the legacy external Vulkan layer.
    - `USE_VK_VIDEO_DECODE=1` (`VK_VIDEO_DECODE=0|1`): automatically enabled on AMD GPUs, exporting deduplicated `RADV_EXPERIMENTAL=video_decode` (and migrating legacy `RADV_PERFTEST=video_decode`).
  - **Ultra Bleeding-Edge Default (`USE_BLEEDING_EDGE=1` / `BLEEDING_EDGE=0|1`):** Automatically enabled for non-anticheat Proton titles (`AUTO_CLASS != competitive-anticheat`, `AUTO_NATIVE_LINUX == 0`, `APPID != 594650`), activating `VKD3D_CONFIG="descriptor_heap,dxr12,force_bindless_texel_buffer"`, `VKD3D_FEATURE_LEVEL="12_2"`, `VKD3D_SHADER_MODEL="6_8"`, `PROTON_FSR4_UPGRADE=1` on RDNA 4 (`PROTON_FSR4_RDNA3_UPGRADE=1` on RDNA 3), `PROTON_NATIVE_AGS=1` on AMD, `PROTON_USE_WOW64=1` (`wow64`), `PROTON_MEDIA_FORCE_GST=1`, and `WAYLANDDRV_RAWINPUT=1` (strictly scoped to native Wayland outside Gamescope). Hard-blocked (`=0`) on `competitive-anticheat`, `AppID 594650`, and native Linux games.
  - **Smart Reflex -> Anti-Lag 2 Auto-Activation (`USE_REFLEX_LAYER=1` / `REFLEX_LAYER=0|1`):** `steam-auto-detect` detects `sl.reflex.dll`, `sl.interposer.dll`, and `nvngx_dlss*.dll` (`AUTO_HAS_REFLEX=1`) and automatically enables Proton-CachyOS `LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1` (`lowlatencylayer` token, `ENABLE_LAYER_MESA_ANTI_LAG=0`) on AMD non-anticheat Proton titles; disabled automatically under `MLFG=1` and hard-blocked (`=0`) in `competitive-anticheat` / native Linux games.
  - **Auto-OptiScaler & Auto-HDR Defaults (`v2.3.0`):** On AMD RDNA 3/4, `legacy-upscaler` Proton titles automatically activate `USE_OPTISCALER=1` (`PROTON_USE_OPTISCALER=1`, `PROTON_OPTISCALER_STREAMLINE=1`, `ENABLE_VKBASALT=0`); on KDE Plasma 6 Wayland with `kscreen-doctor` and `DXVK_HDR=1`, `AUTO_HDR_SWITCH=1` activates automatically (no-op if HDR is already on, auto-toggle + SDR restore if off).
  - **Zero-Touch Smart Auto-AFMF (`v2.4.0`):** When user-space `afmf-linux` (`VK_LAYER_AFMF`, env-gated via `AFMF_ENABLE=1`) is installed, `steam-auto-detect` computes `AUTO_HAS_NATIVE_FG`, `AUTO_IS_TOOL_OR_2D`, and `AUTO_AFMF=1` automatically for eligible 3D titles. `steam-auto-run` defaults `USE_AFMF` to `AUTO_AFMF`, sets `AFMF_ENABLE=1`, `AFMF_PACING=1`, `AFMF_PRESENT_MODE=auto` (+ `AFMF_GAMESCOPE=1` under Gamescope), halves `DXVK_FRAME_RATE` / `VKD3D_FRAME_RATE` (`floor(VRR_CAP / 2)`), keeps native RADV Anti-Lag low-latency enabled (`ENABLE_LAYER_MESA_ANTI_LAG=0`), mutually excludes `MLFG=1`, and hard-locks `DISABLE_AFMF=1` on `competitive-anticheat`, `AppID 594650`, `vr`, and `vr-run`.
  - **Explicit `=0` Opt-Out, `CONSERVATIVE=1` & Legacy `.env` Inheritance:** Every toggle supports explicit `=0` opt-out via env var (`AFMF=0`, `OPTISCALER=0`, `AUTO_HDR_SWITCH=0`, `BLEEDING_EDGE=0`, `TRANSFER_QUEUE=0`, `NATIVE_ANTILAG=0`, `REFLEX_LAYER=0`, `VK_VIDEO_DECODE=0`) or per-game `.env` (`USE_*=0`), `CONSERVATIVE=1` (`USE_CONSERVATIVE=1`) disables all experimental defaults at once, and older `.env` files missing newer keys inherit the smart defaults automatically. `USE_MLFG` and `USE_XWAYLAND` remain opt-in (`=0`) by default.
- **Hunt: Showdown 1896 (`AppID 594650`) Compatibility Guard & Diagnostics:** Automatically enforces `competitive-anticheat`, `USE_XWAYLAND=1` (`PROTON_ENABLE_WAYLAND=0`), `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, and `USE_NET_OPT=1`; `--doctor` and `steam-auto-ui` also inspect Steam `config/config.vdf` `CompatToolMapping` for `594650` and warn when unset or mapped to `proton-cachyos*` (advising Valve's `Proton 11.0-2` or `Proton Hotfix`).
- **Steam Controller (2026, `Triton`/`Proteus`) & Wireless Steam Puck (`28de:{1302,1304,1005,1007}`) Next-Gen Routing:**
  - `USE_STEAM_CONTROLLER=auto` (default; selectable across `Auto`, `Wayland + HDR`, `XWayland`, and `Off` in `steam-auto-ui` across all 27 languages, with legacy `1`/`0` compatibility) detects connected Valve 2026 hardware via `/sys/bus/usb/devices/*` and selects **`wayland-hdr`** on Wayland sessions (or `xwayland` on X11).
  - **`wayland-hdr`** keeps native `winewayland.drv` + OLED HDR10 (`USE_XWAYLAND=0`, `PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`) without forcing `LD_PRELOAD` overlay overhead, explicitly exports `PROTON_USE_SDL=0`, `PROTON_PREFER_SDL=0`, `PROTON_NO_STEAMINPUT=0` (omitting `sdlinput`), automatically runs `steam steam://forceinputappid/<APPID>` with a background `udevadm` mid-game sleep/reconnect watcher so full Steam Input layouts (paddles L4/R4/L5/R5, trackpads, gyro) stay locked, and resets to desktop layout (`steam://forceinputappid/0`) on exit. Use `steam-auto-run --reapply-input <APPID|0>` for manual re-triggering, or `xwayland` as a fallback for engines requiring XWayland Steam Input.
- **Modern DX12 vs Safe DX12:** Exports `PROTON_NATIVE_AGS=1` on AMD and `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` by default; `SAFEDX12=1` omits experimental VKD3D flags and `vkd3dbindlesstb`.
- **Compat-Token Mapping & Retired Flag Purge:** Maps managed features into both `PROTON_ADD_CONFIG` and `STEAM_COMPAT_CONFIG` (`wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `lowlatencylayer`, `localshadercache`, `pipewire`, `fsr4`, `wow64`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`) while purging retired Proton/Wine variables (`PROTON_ENABLE_HDR`, `PROTON_VKREFLEX`, `PROTON_MEDIA_USE_GST`, `PROTON_FSR3_UPGRADE`, `PROTON_VKD3D_HEAP`, `WINEPULSE_FAST_POLLING`).

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for the full technical specification.

---

## Languages & Documentation

All guides are complete, up-to-date practical references covering Steam Auto-Profiler, and `steam-auto-ui` supports all 27 languages natively via `--lang <code>` or the in-app language switcher.

| Region / Group | Languages | Index / Guides |
| --- | --- | --- |
| **Canonical English** | English (`en`) | [User Guide](docs/USER_GUIDE.md) · [Architecture](docs/ARCHITECTURE.md) · [Master i18n Index](docs/i18n/README.md) |
| **Nordic / Featured** | Finnish (`fi`) | [Nordic Index](docs/i18n/nordic/README.md) · [Suomi (fi)](docs/i18n/nordic/USER_GUIDE.fi.md) |
| **CIS / СНГ** | Russian (`ru`), Ukrainian (`uk`), Belarusian (`be`), Kazakh (`kk`), Uzbek (`uz`), Armenian (`hy`), Azerbaijani (`az`), Kyrgyz (`ky`), Tajik (`tg`) | [CIS Index](docs/i18n/cis/README.md) · [ru](docs/i18n/cis/USER_GUIDE.ru.md) · [uk](docs/i18n/cis/USER_GUIDE.uk.md) · [be](docs/i18n/cis/USER_GUIDE.be.md) · [kk](docs/i18n/cis/USER_GUIDE.kk.md) · [uz](docs/i18n/cis/USER_GUIDE.uz.md) · [hy](docs/i18n/cis/USER_GUIDE.hy.md) · [az](docs/i18n/cis/USER_GUIDE.az.md) · [ky](docs/i18n/cis/USER_GUIDE.ky.md) · [tg](docs/i18n/cis/USER_GUIDE.tg.md) |
| **Slavic** | Polish (`pl`), Czech (`cs`), Slovak (`sk`), Bulgarian (`bg`), Serbian (`sr`), Croatian (`hr`), Slovenian (`sl`) *(plus East Slavic links)* | [Slavic Index](docs/i18n/slavic/README.md) · [pl](docs/i18n/slavic/USER_GUIDE.pl.md) · [cs](docs/i18n/slavic/USER_GUIDE.cs.md) · [sk](docs/i18n/slavic/USER_GUIDE.sk.md) · [bg](docs/i18n/slavic/USER_GUIDE.bg.md) · [sr](docs/i18n/slavic/USER_GUIDE.sr.md) · [hr](docs/i18n/slavic/USER_GUIDE.hr.md) · [sl](docs/i18n/slavic/USER_GUIDE.sl.md) |
| **Major Global** | Spanish (`es`), German (`de`), French (`fr`), Portuguese (`pt`), Italian (`it`), Japanese (`ja`), Korean (`ko`), Simplified Chinese (`zh-CN`), Turkish (`tr`) | [Global Index](docs/i18n/global/README.md) · [es](docs/i18n/global/USER_GUIDE.es.md) · [de](docs/i18n/global/USER_GUIDE.de.md) · [fr](docs/i18n/global/USER_GUIDE.fr.md) · [pt](docs/i18n/global/USER_GUIDE.pt.md) · [it](docs/i18n/global/USER_GUIDE.it.md) · [ja](docs/i18n/global/USER_GUIDE.ja.md) · [ko](docs/i18n/global/USER_GUIDE.ko.md) · [zh-CN](docs/i18n/global/USER_GUIDE.zh-CN.md) · [tr](docs/i18n/global/USER_GUIDE.tr.md) |

## License

MIT — see [LICENSE](LICENSE). Security disclosures follow [SECURITY.md](SECURITY.md).
