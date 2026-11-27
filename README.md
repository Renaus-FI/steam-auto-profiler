# Steam Auto-Profiler

[![CI](https://github.com/Renaus-FI/steam-auto-profiler/actions/workflows/ci.yml/badge.svg)](https://github.com/Renaus-FI/steam-auto-profiler/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Context-aware heuristic game classifier and pre-launch orchestrator for Steam on Linux.**

Steam Auto-Profiler is a working reference prototype for Wayland/KDE/GNOME systems. It
inspects the local Steam installation, classifies a game into one of four profiles, and
adds safe launch defaults without requiring the user to maintain a long environment
variable string.

## Classification

| Priority | Class | Detection signal | Default behavior |
| --- | --- | --- | --- |
| 1 | `competitive-anticheat` | Known competitive AppID or anti-cheat runtime files | Disable OptiScaler and frame generation; enable online network profile |
| 2 | `native-fsr` | Native FSR 3.1+ / FSR 4 libraries | Prefer the driver-level FSR upgrade path |
| 3 | `legacy-upscaler` | DLSS, XeSS, or FSR 2 libraries | Mark the title for an optional upscaler bridge |
| 4 | `standard` | No anti-cheat or modern upscaler detected | Use a safe low-latency VRR profile |

The classifier checks Steam library folders and the current AppID manifest, then scans
the installed game directory to ten levels deep.

## Quick start

For the complete installation, automation, launch-option, troubleshooting, and
Lutris/Heroic reference, see the [User Guide](docs/USER_GUIDE.md).

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

Inspect an installed title without launching it:

```bash
steam-auto-run --inspect 2357570
```

Run a read-only CachyOS and Steam compatibility audit:

```bash
steam-auto-run --doctor
```

Set the Steam launch options for flatscreen titles to:

```text
steam-auto-run %command%
```

For VR titles (OpenXR / WiVRn / xrizer / SteamVR), use the dedicated VR launch orchestrator:

```text
vr-run %command%
```

`vr-run` scrubs flatscreen VRR caps, Wayland overrides, Anti-Lag, vkBasalt, and frame-generation
hooks, auto-selects the discrete GPU via `MESA_VK_DEVICE_SELECT`, dynamically detects WiVRn and
xrizer OpenXR/OpenVR paths without clobbering user overrides, and runs through the safe scheduler
chain. `steam-auto-sync` automatically preserves intentional `vr-run %command%` entries during sync
and `--sanitize`. Inspect resolved VR settings with `vr-run --dry-run`.

Preview batch integration and apply it after closing Steam:

```bash
steam-auto-sync --dry-run
steam-auto-sync
```

Clean legacy and orphan launch options in `localconfig.vdf`:

```bash
steam-auto-sync --sanitize
# Alias:
steam-auto-sync --clean
```

Migrate legacy cachy-run profiles and inspect the whole library:

```bash
steam-auto-sync --migrate-cachy-run
steam-auto-sync --report
```

`steam-auto-sync` discovers every configured Steam library. Use
`--print-library-paths` to inspect them, and `--keep-backups N` to retain the
most recent `localconfig.vdf` backups (`0` keeps all; default is 10).

Profiles are parsed as a small allowlisted `KEY=VALUE` format (CRLF and quoted
values are accepted); shell syntax and unknown keys are ignored. Use
`steam-auto-run --list-profiles` or `--last-log [APPID]` for local launch
administration.

Inspect the entire Steam library without modifying `localconfig.vdf`:

```bash
steam-auto-sync --report
```

## Lutris, Heroic, and umu-launcher

- Lutris: enable advanced options, set the Proton runner to `proton-cachyos-slr`, disable the Lutris runtime, prefer system libraries, and set the command prefix to `steam-auto-run`.
- Heroic: select `proton-cachyos-slr` as the Wine/Proton version and add `steam-auto-run` as the wrapper/command prefix.
- Set `PROTON_VERB=waitforexitandrun` in the environment table when Protonfixes or UMU needs the wait-and-run lifecycle.
- `steam-auto-run` and `steam-auto-detect` accept `GAMEID=umu-2357570`; the `umu-` prefix is removed when resolving the AppID.

Use `./install.sh --with-net-boost` only if you want the optional session network helper
installed system-wide with an explicit sudoers rule. The network helper can use CAKE or
`fq_codel`, but it is not required for normal profile inspection or launching.

Use `./install.sh --compat-cachy-run` to preserve an existing `/usr/local/bin/cachy-run`
as `.bak` and install a compatibility shim that delegates to `steam-auto-run`.

Use `./install.sh --with-auto-sync` to install a systemd user watcher that synchronizes
new Steam app manifests after Steam exits.

In Gamescope sessions, redundant DXVK/VKD3D frame pacing is suppressed unless
`VRR_CAP` is explicit. Native Linux launches omit Proton/Wine/DXVK/VKD3D variables.
By default, `VRR_CAP` follows the active monitor refresh rate directly (1:1),
so a 240 Hz display uses a 240 FPS cap. Set `VRR_CAP=<fps>` for a custom cap,
or `VRR_CAP=0` to disable capping. Set `VRR_MINUS_MARGIN=1` to enable the
optional -6% VRR headroom calculation instead.
The network helper exposes an unprivileged read-only `steam-net-boost status [IFACE]`,
recognizes static CAKE setups on both root qdiscs and LAN-exempted HTB hierarchies
(`wan-cake-shaper.service` / `cake-shaper.service`), and restores pre-existing root qdisc
(preserving `cake` instead of downgrading to `fq_codel`), EEE, and `txqueuelen` state after
all launch sessions exit.

## Commands

- `steam-auto-detect [--inspect] [APPID]` - classify an AppID and print the result.
- `steam-auto-run [--inspect|--configure|--reset|--doctor|--check-system] [APPID]` - orchestrate a Steam launch or audit the system.
- `vr-run [--dry-run] %command%` - orchestrate a VR launch with flatscreen override scrubbing and dynamic OpenXR/WiVRn/xrizer detection.
- `steam-auto-sync [--dry-run|--remove|--sanitize|--clean|--migrate-cachy-run|--report|--print-library-paths|--keep-backups N]` - update Steam `localconfig.vdf` launch options or inspect/migrate profiles.
- `steam-net-boost [on|off|status]` - apply, inspect (read-only), or restore optional network tuning.
- `steam-auto-detect --inspect --json [APPID]` - print a machine-readable classification report.

## Proton and Steam Linux Runtime compatibility

Steam Auto-Profiler exports only compatibility variables supported by the selected Proton build. It never vendors a Proton runtime or injects libraries:

| Runtime | Target use | Notes |
| --- | --- | --- |
| Valve Official Proton 10 / 11 / Experimental | Conservative upstream baseline | Hardware-agnostic; unknown or retired Proton-specific variables are not exported |
| `proton-cachyos-slr` | Recommended for EAC/BattlEye | Steam Linux Runtime (SteamRT3/SteamRT4) provides a stable loader and sandbox boundary for anti-cheat titles |
| Proton-EM 11 | CachyOS/Proton-EM-specific compatibility | Supports native Wayland, FSR4/MLFG and Proton-EM controller fixes |
| Proton-GE | Community compatibility build | Use upstream-compatible variables; anti-cheat titles still prefer a Steam Linux Runtime build |

For anti-cheat titles, `proton-cachyos-slr` is preferred over native, distro-bundled builds because it uses Steam's maintained runtime ABI and is the Steam/EAC/BattlEye launch integration target. Steam Auto-Profiler never enables async DXVK branches or OptiScaler for this class.

## Current Proton compatibility variables

Native Wayland defaults to `DXVK_HDR=1` and `WAYLANDDRV_SHORTCUT_INHIBIT=0` (overridable
per-profile or via environment, including in `competitive-anticheat`); set `DXVK_NO_HDR=1`
to disable HDR. No `PROTON_ENABLE_HDR` or `PROTON_VKREFLEX` value is emitted. NVIDIA builds
use `DXVK_NVAPI_VKREFLEX=1`.

Mutual-exclusion guards prevent driver and post-processing conflicts:
- **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` is enforced whenever `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1`, or `USE_OPTISCALER=1` to prevent double-sharpening and HDR10 clipping.
- **MLFG + Low-Latency / VRR Caps:** `USE_MLFG=1` (`MLFG=1`) exports `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, and unsets `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, and `DXVK_FRAME_PACE`. On detected AMD RDNA 3 it also sets `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. When `USE_MLFG=0` and VRR capping is active, `DXVK_FRAME_PACE=low-latency-vrr` is exported alongside the frame cap.
- **Modern Vulkan / DX12:** AMD GPUs export `PROTON_NATIVE_AGS=1`, and `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` is exported when `USE_SAFEDX12=0` (cleanly omitted when `SAFEDX12=1`).

`PROTON_ADD_CONFIG` is mapped into `STEAM_COMPAT_CONFIG` using these supported tokens:
`wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`,
`vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, and `vkreflex`.
Existing user values are preserved. Native upgrade variables use `PROTON_DLSS_UPGRADE=1`,
`PROTON_XESS_UPGRADE=1`, `PROTON_FFX3_UPGRADE=1`, and `PROTON_FFX4_UPGRADE=1`;
the retired `PROTON_FSR3_UPGRADE` name is never used.

## Requirements

The core scripts require Bash and standard Linux utilities. Steam and Proton provide the
game runtime; no third-party overlay or injection library is bundled. Optional GUI
dialogs use `kdialog` or `zenity` when available.

Environment overrides include `NO_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `NETOPT=1`, and
`VRR_CAP=<fps>` or `VRR_MINUS_MARGIN=1`.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the proposed Steam/Proton integration
model.

## Documentation & Translations

- [English User Guide](docs/USER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Major world-language guides](docs/i18n/global/README.md)
- [CIS / СНГ guides](docs/i18n/cis/README.md)
- [Central translation index](docs/i18n/README.md)

## License

MIT
