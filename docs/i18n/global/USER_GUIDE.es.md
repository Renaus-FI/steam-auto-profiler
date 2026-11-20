# Guía de usuario de Steam Auto-Profiler

Esta guía resume la instalación y el uso completo. Para los detalles técnicos, consulte [la guía inglesa](../../USER_GUIDE.md).

## Instalación

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` instala el ayudante opcional de QoS de red. `--compat-cachy-run` conserva `/usr/local/bin/cachy-run` como `.bak` e instala el shim de compatibilidad. `--with-auto-sync` instala el watcher systemd del usuario. `--uninstall` elimina los componentes instalados.

## Funcionamiento

`steam-auto-detect` busca el AppID en los manifiestos y bibliotecas de Steam, revisa el directorio de juego hasta diez niveles y aplica clasificación por prioridad: (1) `competitive-anticheat`, (2) FSR/FidelityFX nativo (`native-fsr4` o `native-fsr`), (3) upscaler heredado `legacy-upscaler`, y (4) `standard`.

`steam-auto-run` resuelve `SteamAppId`, `STEAM_COMPAT_APP_ID` y después `GAMEID`; elimina el prefijo `umu-`. Puede mostrar `kdialog` o `zenity` y guardar opciones por AppID en `~/.config/steam-auto-profiler/profiles/<APPID>.env`. Los perfiles usan `KEY=VALUE`, y las claves desconocidas o sintaxis de shell se ignoran.

Los ajustes compatibles se escriben en `PROTON_ADD_CONFIG` y `STEAM_COMPAT_CONFIG`. Se conservan los valores existentes y se pueden usar tokens como `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire` y `vkreflex`.

## Steam y automatización

En las opciones de lanzamiento de Steam:

```text
steam-auto-run %command%
```

Para UMU: `GAMEID=umu-2357570 steam-auto-run %command%`.

Cierre Steam antes de modificar `localconfig.vdf`:

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` es alias de `--sanitize`; `--remove` elimina el wrapper; `--print-library-paths` lista las bibliotecas; `--keep-backups N` conserva N copias (`0` conserva todas).

El watcher usa `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`. También puede instalarse con `steam-auto-sync --install-systemd`.

## Comandos y ajustes

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles` y `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Variables útiles: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1` y `NO_NTSYNC=1`.

`VRR_CAP` tiene prioridad. Sin él, se consulta `kscreen-doctor`, `wlr-randr` o `xrandr`; una frecuencia mayor de 60 Hz genera un límite del 94 %. En Gamescope no se exportan límites DXVK/VKD3D salvo que `VRR_CAP` esté definido.

## Red y solución de problemas

Si `NETOPT=1` o se selecciona `netopt`, `steam-net-boost` activa CAKE o `fq_codel`, desactiva temporalmente EEE y ajusta tx queue length. Al salir el último proceso de juego, restaura el estado anterior.

Consulte `sudo steam-net-boost status [IFACE]`. Ante cambios de Steam, cierre Steam por completo. Para perfiles erróneos use `FORCE_GUI=1` o `--reset APPID`. Para lanzamientos anti-cheat use `proton-cachyos-slr` y compruebe el sistema con `--doctor`.
