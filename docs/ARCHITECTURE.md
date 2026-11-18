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
- Use the active compositor refresh rate to calculate a safe VRR ceiling.
- Preserve explicit user overrides while applying anti-cheat and crash-safety guardrails.
