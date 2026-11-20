# Steam Auto-Profiler User Guide

This guide covers installation, daily operation, library synchronization, launch
overrides, and third-party launchers. The scripts require Bash, Python 3, Steam,
and a Linux desktop session; GUI configuration additionally needs `kdialog` or
`zenity`.

## Installation and updates

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git ~/steam-auto-profiler
cd ~/steam-auto-profiler
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` installs the optional CAKE/fq_codel helper and its narrow
sudoers rule. `--compat-cachy-run` installs a delegating `/usr/local/bin/cachy-run`
shim and preserves an existing copy as `.bak`. `--with-auto-sync` installs a
systemd user path/service pair watching Steam's `steamapps` directory. It is
safe to omit any optional flag.

Update an existing checkout with:

```bash
cd ~/steam-auto-profiler
git fetch origin
git reset --hard origin/main
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Remove installed binaries and the auto-sync units with:

```bash
cd ~/steam-auto-profiler && ./install.sh --uninstall
```

## System readiness

```bash
steam-auto-run --doctor
```

The doctor reports kernel and `/dev/ntsync` availability, AMD/Intel pstate,
sched-ext/scx status, `ananicy-cpp` versus GameMode conflicts, EAC Linux v2
readiness (`eac-status` when installed), `vm.max_map_count`, NVMe scheduler,
duplicate `environment.d` and `sysctl.d` settings, Ethernet EEE, CAKE/fq_codel,
and installed Proton compatibility tools including `proton-cachyos-slr`.
Warnings are diagnostics, not automatic system modifications.

## Automating the Steam library

Close Steam before a write operation, then preview and apply:

```bash
steam-auto-sync --report
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
```

`--sanitize` backs up each `localconfig.vdf`, preserves engine arguments such as
`-dx12`, moves supported environment flags into per-game profiles, removes stale
managed entries, and leaves `steam-auto-run %command%`. Use
`--migrate-cachy-run` for legacy profiles and `--remove` to remove the wrapper.
The installed systemd watcher runs the equivalent sanitize command and waits up
to five minutes for Steam to exit:

```bash
steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300
```

The watcher and manual synchronization cover every Steam library returned by
`steam-auto-sync --print-library-paths`, including secondary SSD/NVMe libraries.
Use `--keep-backups N` to retain the newest `N` timestamped
`localconfig.vdf.bak.*` backups per Steam profile (`0` keeps all; the default is
10).

Install the same watcher directly from an installed binary with:

```bash
steam-auto-sync --install-systemd
```

## Launch modes

Use `steam-auto-run %command%` in Steam launch options. The first launch can show
a checklist; selecting “Save profile” writes
`~/.config/steam-auto-profiler/profiles/<APPID>.env`, and later launches are
silent. For zero-click behavior:

```bash
mkdir -p ~/.config/environment.d
grep -qxF 'NO_GUI=1' ~/.config/environment.d/gaming.conf 2>/dev/null ||
  echo 'NO_GUI=1' >> ~/.config/environment.d/gaming.conf
```

Open a saved game's checklist at any time with `steam-auto-run --configure APPID`.
Without a graphical display it writes the detected defaults and exits successfully.
Use `steam-auto-run --dry-run APPID` to print the classification, hardware summary,
compatibility tokens, and sorted exported launch variables without starting a game.
Use `steam-auto-run --list-profiles` to list saved profiles and resolved game names,
and `steam-auto-run --last-log [APPID]` to inspect the bounded last-launch record.
The log includes launch variables, Gamescope state, the wrapped command, and the
exit code.

## Command cheat sheet

| Purpose | Command |
| --- | --- |
| System audit | `steam-auto-run --doctor` |
| Inspect one game | `steam-auto-run --inspect APPID` |
| JSON inspection | `steam-auto-detect --inspect --json APPID` |
| Configure one game | `steam-auto-run --configure APPID` |
| Preview one launch | `steam-auto-run --dry-run APPID` |
| List saved profiles | `steam-auto-run --list-profiles` |
| Read launch diagnostics | `steam-auto-run --last-log [APPID]` |
| Reset a profile | `steam-auto-run --reset APPID` |
| Library report | `steam-auto-sync --report` |
| Preview sanitization | `steam-auto-sync --sanitize --dry-run` |
| Apply sanitization | `steam-auto-sync --sanitize` |
| Remove wrapper | `steam-auto-sync --remove` |
| Migrate cachy-run profiles | `steam-auto-sync --migrate-cachy-run` |
| Inspect network boost | `sudo steam-net-boost status [IFACE]` |

## Per-game overrides

Place an override before the wrapper, for example
`MLFG=1 FSR_HUD=1 steam-auto-run %command%`.

| Variable | Effect |
| --- | --- |
| `FORCE_GUI=1` | Reopen the checklist |
| `NO_GUI=1` | Never show dialogs |
| `XWAYLAND=1` | Force XWayland |
| `MLFG=1` | Enable frame generation |
| `OPTISCALER=1` | Enable OptiScaler |
| `SHARPEN=1` / `VIVID=1` | Enable sharpening/preset |
| `NETOPT=1` | Enable network profile |
| `SDL=1` | Prefer native SDL/Steam Input |
| `GST=1` / `CEF=1` | Enable launcher compatibility fixes |
| `SAFEDX12=1` | Avoid the bundled DXVK/VKD3D compatibility token |
| `FSR_HUD=1` | Show the FSR/DLSS indicator |
| `VULKAN=1` | Add `-vulkan` |
| `KEEP_OVERLAY=1` | Preserve Steam Overlay preload |
| `NO_NTSYNC=1` | Disable NTSync |
| `NO_DECORATION=1` | Disable window decorations |
| `VRR_CAP=120` | Set a custom frame cap |

Inside Gamescope, the profiler does not add DXVK/VKD3D frame caps unless
`VRR_CAP` is explicitly set. Native Linux titles also avoid Proton, Wine, DXVK,
and VKD3D variables while retaining discrete-GPU selection and native scheduler
network hooks.

## Lutris, Heroic, Faugus, and umu

Set `steam-auto-run` as the command prefix/wrapper and use the desired Proton
runner. The `cachy-run` shim is also supported. For UMU-based launchers, pass
`GAMEID=umu-<APPID>`; the wrapper strips `umu-` when resolving the profile:

```text
GAMEID=umu-2357570 steam-auto-run %command%
```

## Русская краткая шпаргалка

Установка: `./install.sh --with-auto-sync --with-net-boost --compat-cachy-run`.
Проверка системы: `steam-auto-run --doctor`. Отчёт библиотеки:
`steam-auto-sync --report`. Перед изменением параметров закройте Steam и выполните
`steam-auto-sync --sanitize --dry-run`, затем `steam-auto-sync --sanitize`.
Для полной тишины добавьте `NO_GUI=1` в
`~/.config/environment.d/gaming.conf`. Настройка игры:
`steam-auto-run --configure APPID`; просмотр без запуска:
`steam-auto-run --dry-run APPID`; сброс:
`steam-auto-run --reset APPID`. В Lutris/Heroic/Faugus используйте
`steam-auto-run` как префикс, а для UMU передайте `GAMEID=umu-APPID`.
