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

The installer copies the four commands to `~/.local/bin`, creates `~/.config/steam-auto-profiler/profiles`, and adds default vkBasalt presets. Make sure `~/.local/bin` is in `PATH`.

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
8. **Apply launch variables and scheduling.** The wrapper exports Wayland/HDR, low-latency DXVK/VKD3D, frame-generation, upscaler, Steam Input, overlay, and compatibility variables as appropriate. It uses `game-performance`, then `powerprofilesctl launch -p performance --`, and `gamemoderun` only when it will not conflict with `ananicy-cpp`.
9. **Start and monitor the launch.** Native Linux titles omit Proton/Wine/DXVK/VKD3D variables. The wrapper launches the supplied command and writes a bounded last-launch record.
10. **Restore optional network state.** If QoS is enabled, `steam-net-boost` activates per-session state for the selected interface. CAKE/fq_codel, tx queue length, and NIC EEE state are restored after the last launch session exits.

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
| Inspect network helper | `sudo steam-net-boost status [IFACE]` |

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
| `SAFEDX12=1` | Disable the bundled DXVK/VKD3D compatibility token. |
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
