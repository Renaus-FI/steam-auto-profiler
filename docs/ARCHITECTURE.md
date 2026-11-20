# Native Context-Aware Profiling in Steam and Proton

## Goal

Give desktop Linux and SteamOS users a safe, context-aware launch experience without
requiring them to copy launch strings from forums or combine conflicting environment
variables.

## Steam client

Steam could replace raw launch environment strings with structured per-AppID settings:

- Display backend: Automatic Wayland, HDR, or XWayland fallback
- Frame pacing: Automatic VRR cap, frame generation, or uncapped
- Controller pipeline: Steam Input or direct SDL input
- Network priority: Multiplayer QoS or off
- Profile persistence: Steam Cloud or the existing `localconfig.vdf`

## Steam Linux Runtime

Before launching Proton, the runtime could run a lightweight game classifier:

- Detect Easy Anti-Cheat, BattlEye, Ricochet, ACE, and other guardrail runtimes.
- Detect native FSR, legacy DLSS/XeSS/FSR libraries, and third-party CEF launchers.
- Disable third-party Vulkan and DLL hooks for anti-cheat titles.
- Keep a deterministic precedence order for conflicting launch options.

## Proton and graphics drivers

Proton and Mesa/Vulkan could resolve settings centrally:

- Enforce mutual exclusion between frame generation and low-latency VRR frame caps.
- Disable external sharpening when an upscaler bridge is active.
- Use the active compositor refresh rate directly for the VRR ceiling, with an opt-in -6% margin via `VRR_MINUS_MARGIN=1`.
- Preserve explicit user overrides while applying anti-cheat and crash-safety guardrails.

## Proton compatibility matrix

| Build | Steam Linux Runtime | Hardware-agnostic recommendation |
| --- | --- | --- |
| Valve Official Proton 10 / 11 / Experimental | SteamRT3/SteamRT4 compatible | Baseline upstream behavior; avoid CachyOS-only environment variables |
| `proton-cachyos-slr` | Steam Linux Runtime | Recommended for EAC/BattlEye, due to the SteamRT ABI and runtime boundary |
| Proton-EM 11 | Community CachyOS build | Full Wayland/controller, FSR4/MLFG and native DLL upgrade support |
| Proton-GE | Community build | Preserves upstream-compatible variables; do not assume CachyOS-only flags |

`proton-cachyos-slr` is strongly preferred for Easy Anti-Cheat and BattlEye titles because a
maintained Steam Linux Runtime is less likely to conflict with guardrails and launch services
than a native distro build. Anti-cheat classification forces OptiScaler and all async DXVK
branches off while preserving only synchronous low-latency DXVK/VKD3D paths.

## Compat-token mapping

The launcher maps selected features into both `PROTON_ADD_CONFIG` and `STEAM_COMPAT_CONFIG`.
The shared token set is `wayland`, `sdlinput`, `nativeags`, `noopwr`,
`vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`,
`pipewire`, `fsr4`, `mlfg`, and `vkreflex`. Existing user token lists remain intact.

Retired variables are never emitted. `PROTON_ENABLE_HDR` was removed and HDR is auto-detected
by Wine Wayland; `DXVK_NO_HDR=1` remains the explicit off switch. `PROTON_VKREFLEX` was
removed in favor of `DXVK_NVAPI_VKREFLEX=1`. `PROTON_FSR3_UPGRADE` was renamed
`PROTON_FFX3_UPGRADE`.

## Scheduler and anti-cheat safety

Launches use `game-performance` first, then `powerprofilesctl launch -p performance --`.
`gamemoderun` is used only when `ananicy-cpp.service` is inactive. If both schedulers are
present and `ananicy-cpp` is active, the game is launched directly to avoid competing process
niceness policies.

## System doctor and external launchers

`steam-auto-run --doctor` performs a read-only readiness audit: kernel/NTSync, CPU P-State and
sched-ext, GameMode/ananicy conflicts, EAC v2 tooling, memory-map limits, NVMe I/O schedulers,
shader-cache environment settings, and installed Proton compatibility tools.

Steam and UMU launch paths share the AppID resolver: `SteamAppId`, `STEAM_COMPAT_APP_ID`, then
numeric `GAMEID` (with an optional `umu-` prefix). Lutris and Heroic can use `steam-auto-run`
as a command prefix with `proton-cachyos-slr`; `PROTON_VERB=waitforexitandrun` supports the
UMU/Protonfixes lifecycle.
