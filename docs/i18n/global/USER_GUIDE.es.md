# Guía del usuario de Steam Auto-Profiler

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Esta guía cubre la instalación completa, la orquestación de lanzamientos en pantalla plana y VR, el Centro de control `steam-auto-ui`, la sincronización de bibliotecas, el benchmarking y la solución de problemas para **Steam Auto-Profiler v2.0**.

Steam Auto-Profiler es un lanzador ligero y centro de control en Bash/Python para Linux que inspecciona un AppID de Steam (o un acceso directo de juego que no es de Steam), aplica un perfil adaptado al contexto con protecciones estrictas de controlador/escalador/anti-cheat e inicia el comando del juego existente. Nunca incluye ni inyecta un runtime Proton de terceros.

---

## Requisitos

- Sesión de escritorio Linux (KDE Plasma 6 / Wayland, GNOME, wlroots o X11), Bash 5+, Python 3.10+, Steam y utilidades estándar del sistema.
- Interfaz gráfica nativa opcional para el Centro de control: `PyQt6` o `PySide6` (recurre automáticamente a la TUI en `curses` de la biblioteca estándar sin dependencias adicionales).
- Cuadros de diálogo opcionales de lista de verificación previa al lanzamiento: `kdialog` o `zenity`.
- Benchmarking silencioso opcional de tiempos de fotograma (frametime): `mangohud`.
- Ayudante opcional de red por sesión: `tc`, `ip` y `ethtool` (`sudo` solo se requiere durante la instalación con `--with-net-boost`).

---

## Instalación y actualizaciones

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` copia los seis ejecutables (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` y `steam-auto-ui`) en `~/.local/bin`, instala la entrada de escritorio (`~/.local/share/applications/steam-auto-profiler.desktop`), crea `~/.config/steam-auto-profiler/profiles` y añade los preajustes predeterminados de vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Asegúrate de que `~/.local/bin` esté en `PATH`.

Las opciones del instalador se pueden combinar:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: instala `/usr/local/bin/steam-net-boost` (junto con copias a nivel de sistema del resto de scripts) y una regla `sudoers` estrictamente acotada sin contraseña para `steam-net-boost`.
- `--compat-cachy-run`: conserva cualquier `/usr/local/bin/cachy-run` existente como `/usr/local/bin/cachy-run.bak` (salvo que ya sea el shim de Steam Auto-Profiler) e instala un shim de reenvío hacia `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): instala y habilita el observador de systemd de usuario `steam-auto-profiler-sync.path` y su servicio `oneshot` correspondiente en todas las bibliotecas de Steam detectadas.
- `--uninstall`: elimina los binarios instalados, la entrada de escritorio, el ayudante de red/regla sudoers opcionales, el shim de compatibilidad y las unidades de usuario de systemd de sincronización automática.

Para actualizar un repositorio ya clonado:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Verifica el estado del sistema antes de sincronizar tus juegos:

```bash
steam-auto-run --doctor
```

---

## Canalización de lanzamiento de extremo a extremo

1. **Resolución de AppID:** Comprueba `SteamAppId`, `STEAM_COMPAT_APP_ID` y luego `GAMEID` (eliminando cualquier prefijo `umu-` para Lutris/Heroic/UMU).
2. **Detección de bibliotecas y accesos directos:** `steam-auto-detect` busca en las rutas raíz de Steam y bibliotecas secundarias declaradas en `libraryfolders.vdf`, lee `appmanifest_<APPID>.acf` o recurre en modo solo lectura al archivo binario `userdata/*/config/shortcuts.vdf`, y después ejecuta un `find` de una sola pasada hasta 10 niveles de profundidad (excluyendo `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Prioridad de clasificación en cinco niveles:**
   - **1. `competitive-anticheat`:** AppID competitivo conocido o runtime anti-cheat detectado (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE, etc.). Desactiva OptiScaler, MLFG, vkBasalt y DXVK asíncrono; activa baja latencia y QoS de red por sesión.
   - **2. `vr`:** Detección de `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` o indicadores `vr-run`/`-vr` en el acceso directo. Exporta `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** FidelityFX SDK 3.1+ modular (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Activa la actualización FSR4 a nivel de controlador (`PROTON_FSR4_UPGRADE=1` o `PROTON_FSR4_RDNA3_UPGRADE=1` en AMD RDNA 3).
   - **4. `legacy-upscaler`:** Bibliotecas heredadas DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) o DLLs de FSR 2/3.0. Marca `AUTO_OPTISCALER=1` y establece la guía `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Perfil seguro con Wine Wayland nativo y VRR de baja latencia.
4. **Limitación de tasa de refresco VRR:** Un valor explícito `VRR_CAP=<fps>` siempre prevalece (`VRR_CAP=0` desactiva el límite). De lo contrario, se consulta la frecuencia activa de la pantalla mediante `kscreen-doctor` (modo activo `*` de KDE Plasma 6 o `Hz` clásico), `wlr-randr` o `xrandr` y se aplica 1:1 de forma predeterminada (`240 FPS` en 240 Hz). Activa `VRR_MINUS_MARGIN=1` para el margen de seguridad VRR opcional de `-6%` (`hz * 94 / 100`, p. ej., `225 FPS` en 240 Hz). En sesiones de Gamescope, se omiten los límites DXVK/VKD3D salvo que `VRR_CAP` sea explícito.
5. **Protecciones de exclusión mutua:**
   - **FSR 4 / OptiScaler + vkBasalt:** Se fuerza `ENABLE_VKBASALT=0` siempre que `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` o `USE_OPTISCALER=1` estén activos (evita doble nitidez y recorte HDR10).
   - **MLFG + Baja latencia / Límites VRR:** `MLFG=1` (`USE_MLFG=1`) exporta `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, elimina `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` y `DXVK_FRAME_PACE`, y exporta `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` en AMD RDNA 3. Cuando `USE_MLFG=0` y el límite VRR está activo, se exporta `DXVK_FRAME_PACE=low-latency-vrr`.
   - **DX12 moderno + Safe DX12:** Exporta `PROTON_NATIVE_AGS=1` en AMD y `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` cuando `USE_SAFEDX12=0` (se omite limpiamente cuando `SAFEDX12=1`).
6. **Asignación de tokens de compatibilidad:** Las funciones gestionadas se añaden sin sobrescribir los valores previos del usuario tanto en `PROTON_ADD_CONFIG` como en `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **HDR automático en KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Cuando se habilita fuera de Gamescope con `DXVK_HDR=1` (o `USE_HDR=1`), consulta la salida principal habilitada mediante `kscreen-doctor -o`; si HDR está desactivado, lo activa antes del lanzamiento y restaura SDR mediante una trampa `EXIT`/`INT`/`TERM`.
8. **Benchmarking silencioso de frametimes (`BENCH=1`):** Ejecuta MangoHud en modo CSV oculto (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), analiza los frametimes al salir, añade `Avg FPS`, `1% Low FPS` y `P99 (ms)` a `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` y borra los CSV temporales.
9. **Autorrecuperación en Modo Seguro ante cierres rápidos:** Si un título Proton/Windows finaliza con código distinto de cero en menos de `20s` (configurable mediante `SAP_CRASH_THRESHOLD_SEC`) mientras están activas banderas experimentales de Wayland o DX12 (`USE_XWAYLAND=0` o `USE_SAFEDX12=0`), registra un `crash_hint` en `last-<APPID>.log` y `last-launch.log`, y pregunta (cuando la GUI está activa) si deseas guardar `USE_XWAYLAND=1` + `USE_SAFEDX12=1` para el próximo lanzamiento.
10. **Ciclo de vida del planificador y red:** Se ejecuta siguiendo la cadena `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (solo cuando `ananicy-cpp.service` está inactivo) -> ejecución directa, con soporte opcional para `PRIME=1` (`prime-run`). Si `USE_NET_OPT=1`, `steam-net-boost` ejecuta `on`/`off` con conteo de referencias y `flock`, preservando las jerarquías estáticas de root CAKE y HTB + leaf CAKE.

---

## Centro de control unificado (`steam-auto-ui`)

Inicia `steam-auto-ui` desde el menú de aplicaciones del escritorio, mediante `steam-auto-run --ui` o directamente:

```bash
steam-auto-ui                 # Detecta automáticamente la GUI Qt6 (PyQt6/PySide6) o la TUI curses
steam-auto-ui --gui           # Fuerza la ventana gráfica nativa Qt6
steam-auto-ui --tui           # Fuerza la TUI curses de stdlib (funciona por SSH)
steam-auto-ui --lang fi       # Inicia con un idioma de interfaz explícito (27 idiomas compatibles)
steam-auto-ui --check         # Ejecuta autoverificación headless (imprime diagnóstico en JSON)
```

`steam-auto-ui` detecta automáticamente la configuración regional del sistema desde `LC_ALL` / `LC_MESSAGES` / `LANG` y ofrece un menú desplegable de idioma en vivo en la GUI Qt6 (y la tecla rápida `L` en la TUI `curses`) para cambiar entre los 27 idiomas en tiempo de ejecución sin reiniciar.

### Cinco vistas sincronizadas

1. **Juegos y perfiles:** Tabla filtrable de títulos de Steam y entradas de solo lectura de accesos directos no-Steam en `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), insignia de SDK de escalado (`AUTO_UPSCALER_INFO`), validación de exclusión mutua en vivo sobre los 10 conmutadores de perfil + `VRR_CAP`, `Dry-Run Preview`, botón de acceso directo a `Benchmarks` y `Reset Profile`.
2. **Sistema y telemetría:** Lectura en vivo no bloqueante de `steam-auto-run --doctor`, estado de `scxctl get` / `sched_ext`, versiones instaladas de la pila (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), uso de caché de shaders (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), alertas de degradación git/AUR en `/var/log/pacman.log`, VRAM/uso/temperatura de la GPU, rendimiento LAN (`10:`) frente a WAN (`20:`/root) y `av_delay` de `tc -s qdisc`, y `vr-mode status`.
3. **Sincronización de biblioteca:** Banner de estado en vivo que detecta si Steam está en ejecución, más botones de un clic para `--report`, `--sanitize --dry-run`, `--sanitize` (bloqueado mientras Steam esté abierto) y `--migrate-cachy-run`.
4. **Registros y recuperación:** Explora `last-launch.log` y `last-<APPID>.log`, inspecciona alertas `crash_hint` y aplica el Modo Seguro en un clic (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarks:** Tabla comparativa filtrable lado a lado de las ejecuciones de frametime con `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Orquestación VR (`vr-run`)

Configura **Propiedades > General > Parámetros de lanzamiento** en Steam para títulos VR como:

```text
vr-run %command%
```

- Limpia variables heredadas de pantalla plana (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Selecciona automáticamente la GPU dedicada con mayor VRAM mediante `MESA_VK_DEVICE_SELECT` y establece `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` en GPUs AMD.
- Sondaje dinámico de rutas OpenXR/OpenVR de WiVRn y xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) y configuración de `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` y `LD_LIBRARY_PATH` sin sobrescribir ajustes explícitos del usuario.
- Gestiona `vr-mode on` / `vr-mode off` con conteo de referencias en `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (con `flock`) cuando `vr-mode` está instalado (`VR_AUTO_MODE=0` lo desactiva).
- Utiliza la misma cadena de planificadores compatible con `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> `exec` directo).
- Previsualiza las variables resueltas en cualquier momento con `vr-run --dry-run`.

`steam-auto-run` omite automáticamente SteamVR (`250820`) y los lanzamientos `-vr`/`--vr`, y `steam-auto-sync` asigna y preserva automáticamente `vr-run %command%` para juegos VR.

---

## Sincronización de biblioteca de Steam (`steam-auto-sync`)

Cierra Steam por completo antes de escribir en `localconfig.vdf`:

```bash
steam-auto-sync --report              # Auditoría de solo lectura de la biblioteca + shortcuts.vdf
steam-auto-sync --print-library-paths # Muestra todas las bibliotecas de Steam detectadas
steam-auto-sync --dry-run             # Previsualiza los cambios
steam-auto-sync                       # Inyecta steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Previsualiza la limpieza de opciones antiguas
steam-auto-sync --sanitize            # Limpia opciones desordenadas/huérfanas (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migra perfiles antiguos de cachy-run
steam-auto-sync --remove              # Elimina el envoltorio steam-auto-run
```

- Las copias de seguridad con marca de tiempo `localconfig.vdf.bak.*` se purgan automáticamente con `--keep-backups N` (predeterminado `10`; `0` las conserva todas).
- Excluye AppIDs concretos listándolos (uno por línea; se permiten comentarios con `#`) en `~/.config/steam-auto-profiler/ignore_appids.txt`.
- El observador de sincronización automática de systemd (`./install.sh --with-auto-sync` o `steam-auto-sync --install-systemd`) ejecuta `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` cuando cambian los manifiestos de Steam.

---

## Referencia de CLI y perfiles

### Comandos

| Propósito | Comando |
| --- | --- |
| Auditoría de estado del sistema | `steam-auto-run --doctor` (alias `--check-system`) |
| Iniciar Centro de control (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` o `steam-auto-run --ui` |
| Inspeccionar un juego (legible) | `steam-auto-run --inspect APPID` |
| Inspeccionar un juego (JSON) | `steam-auto-detect --inspect --json APPID` |
| Reconfigurar perfil interactivamente | `steam-auto-run --configure APPID` |
| Previsualizar entorno resuelto | `steam-auto-run --dry-run APPID` |
| Restablecer perfil guardado | `steam-auto-run --reset APPID` |
| Listar perfiles guardados | `steam-auto-run --list-profiles` |
| Mostrar el último registro de lanzamiento | `steam-auto-run --last-log [APPID]` |
| Previsualizar entorno de lanzamiento VR | `vr-run --dry-run` |
| Inspeccionar ayudante de red (solo lectura) | `steam-net-boost status [IFACE]` |

### Claves de perfil `.env` guardadas y anulaciones por variables de entorno

Los archivos de perfil residen en `~/.config/steam-auto-profiler/profiles/<APPID>.env` y aceptan un formato de lista blanca `KEY=VALUE` (las sustituciones de comandos de shell y las claves desconocidas se ignoran de forma segura):

| Clave `.env` | Variable de entorno | Efecto |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Fuerza XWayland en lugar de Wine Wayland nativo |
| `USE_FSR4=0` | `FSR4=0` | Desactiva la actualización FSR 4 a nivel de controlador (predeterminado `1`) |
| `USE_MLFG=1` | `MLFG=1` | Activa la generación de fotogramas (desactiva Anti-Lag, baja latencia y límites VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Activa el puente OptiScaler (bloqueado en `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Activa el enfoque vkBasalt (desactivado si FSR 4 u OptiScaler están activos) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Omite las banderas experimentales `VKD3D_CONFIG` y el token `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Activa QoS de red por sesión mediante `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Prefiere la emulación nativa SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Conserva `LD_PRELOAD` de la interfaz superpuesta de Steam |
| `USE_CEF_FIX=1` | `CEF=1` | Añade `--in-process-gpu` para lanzadores CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Desactiva NTSync para títulos antiguos |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Desactiva las decoraciones del gestor de ventanas |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Límite personalizado de FPS para DXVK/VKD3D (`0` desactiva el límite) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Aplica un margen de `-6%` respecto a la frecuencia del monitor (p. ej. `225 FPS` en 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Permite la inhibición de atajos en Wine Wayland (predeterminado `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Activa HDR automáticamente en KDE Plasma 6 al iniciar y restaura SDR al salir |
| — | `BENCH=1`, `BENCH_DURATION=60` | Ejecuta un benchmark CSV silencioso con MangoHud y guarda el resumen JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Oculta o fuerza la apertura del cuadro de lista `kdialog`/`zenity` previo al lanzamiento |
| — | `FSR_HUD=1` | Exporta las variables del indicador HUD para FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Añade `-vulkan` / envuelve con `prime-run` |
| — | `GAMEID=umu-<appid>` | Resuelve AppIDs de UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus y UMU

- **Lutris:** Activa las opciones avanzadas, selecciona `proton-cachyos-slr` (o tu compilación de Proton), desactiva el runtime de Lutris, prefiere las bibliotecas del sistema y establece el prefijo de comando en `steam-auto-run`.
- **Heroic / Faugus:** Selecciona `proton-cachyos-slr` y añade `steam-auto-run` como envoltorio/prefijo de comando.
- **UMU / Protonfixes:** Exporta `PROTON_VERB=waitforexitandrun` y `GAMEID=umu-<appid>` cuando sea necesario.

---

## Solución de problemas

- **Cierre rápido en Wayland o DX12:** Abre **Registros y recuperación** en `steam-auto-ui` (o ejecuta `steam-auto-run --last-log APPID`) y aplica el Modo Seguro (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), o lanza con `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Los títulos con anti-cheat no arrancan:** Usa `proton-cachyos-slr` (Steam Linux Runtime) y ejecuta `steam-auto-run --doctor` para comprobar EAC v2, `/dev/ntsync` y `vm.max_map_count`.
- **Steam revierte los parámetros de lanzamiento:** Cierra Steam por completo antes de ejecutar `steam-auto-sync` o `steam-auto-sync --sanitize`.
- **Límite VRR incorrecto o ausente:** Define `VRR_CAP=<fps>` explícitamente, `VRR_CAP=0` para desactivarlo o `VRR_MINUS_MARGIN=1` para un margen de `-6%`. En Gamescope, solo un `VRR_CAP` explícito exporta límites DXVK/VKD3D.
- **Comprobación de QoS de red:** Ejecuta `steam-net-boost status` (solo lectura sin privilegios). Instala el ayudante con privilegios usando `./install.sh --with-net-boost` si deseas QoS automático por sesión.

Consulta [ARCHITECTURE.md](../../ARCHITECTURE.md) para los detalles internos de diseño, [English User Guide](../../USER_GUIDE.md) para la versión canónica en inglés y [i18n Index](../README.md) para las 27 guías localizadas.
