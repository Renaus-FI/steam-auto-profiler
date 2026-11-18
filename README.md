# Steam Auto-Profiler

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

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

Inspect an installed title without launching it:

```bash
steam-auto-run --inspect 2357570
```

Set the Steam launch options to:

```text
steam-auto-run %command%
```

Preview batch integration and apply it after closing Steam:

```bash
steam-auto-sync --dry-run
steam-auto-sync
```

Inspect the entire Steam library without modifying `localconfig.vdf`:

```bash
steam-auto-sync --report
```

Use `./install.sh --with-net-boost` only if you want the optional session network helper
installed system-wide with an explicit sudoers rule. The network helper can use CAKE or
`fq_codel`, but it is not required for normal profile inspection or launching.

## Commands

- `steam-auto-detect [--inspect] [APPID]` - classify an AppID and print the result.
- `steam-auto-run [--inspect|--configure|--reset] [APPID]` - orchestrate a Steam launch.
- `steam-auto-sync [--dry-run|--remove]` - update Steam `localconfig.vdf` launch options.
- `steam-auto-net-boost [on|off|status]` - apply or restore optional network tuning.
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

Native Wayland defaults to `DXVK_HDR=1`; set `DXVK_NO_HDR=1` to disable HDR. No `PROTON_ENABLE_HDR` or
`PROTON_VKREFLEX` value is emitted. NVIDIA builds use `DXVK_NVAPI_VKREFLEX=1`.

Frame generation is mutually guarded: `USE_MLFG=0` exports both `PROTON_MLFG_UPGRADE=0` and
`MLFG_UPGRADE=0`. `USE_MLFG=1` on detected AMD RDNA3 exports
`DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`.

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
`VRR_CAP=<fps>`.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the proposed Steam/Proton integration
model.

## License

MIT
