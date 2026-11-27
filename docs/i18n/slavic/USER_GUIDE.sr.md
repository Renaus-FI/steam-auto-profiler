# Кориснички водич за Steam Auto-Profiler

> 🌐 [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Овај водич покрива потпуну инсталацију, оркестрацију покретања стандардних и VR игара, контролни центар `steam-auto-ui`, синхронизацију библиотеке, бенчмаркинг и решавање проблема за **Steam Auto-Profiler v2.0**.

Steam Auto-Profiler је лагани Bash/Python покретач и контролни центар за Linux који проверава Steam AppID (или пречицу за игру ван Steam-а), примењује контекстно прилагођен профил са строгим заштитним правилима за драјвере, апскејлере и анти-чит системе и покреће постојећу команду игре. Никада не пакује нити убризгава спољно Proton окружење за извршавање.

---

## Захтеви

- Linux десктоп сесија (KDE Plasma 6 / Wayland, GNOME, wlroots или X11), Bash 5+, Python 3.10+, Steam и стандардни системски алати.
- Опциони нативни GUI контролног центра: `PyQt6` или `PySide6` (аутоматски се пребацује на `curses` TUI без спољних зависности из стандардне библиотеке).
- Опциони дијалози са контролном листом пре покретања: `kdialog` или `zenity`.
- Опционо тихо мерење времена фрејмова (frametime benchmarking): `mangohud`.
- Опциони мрежни помоћник за сесију: `tc`, `ip` и `ethtool` (`sudo` је потребан само током инсталације са `--with-net-boost`).

---

## Инсталација и ажурирања

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` копира свих шест извршних датотека (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` и `steam-auto-ui`) у `~/.local/bin`, инсталира десктоп пречицу (`~/.local/share/applications/steam-auto-profiler.desktop`), креира `~/.config/steam-auto-profiler/profiles` и додаје подразумеване vkBasalt пресете (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Уверите се да је `~/.local/bin` у променљивој `PATH`.

Опционе заставице инсталатера могу се комбиновати:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: инсталира `/usr/local/bin/steam-net-boost` (уз системске копије осталих скрипти) и уско ограничено sudoers правило без лозинке за `steam-net-boost`.
- `--compat-cachy-run`: чува постојећи `/usr/local/bin/cachy-run` као `/usr/local/bin/cachy-run.bak` (осим ако већ није Steam Auto-Profiler прослеђујући shim) и инсталира прослеђујући shim ка `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): инсталира и омогућава корисничку systemd јединицу `steam-auto-profiler-sync.path` и пратећи oneshot сервис за све пронађене Steam библиотеке.
- `--uninstall`: уклања инсталиране извршне датотеке, десктоп ставку, опциони мрежни помоћник/sudoers правило, слој компатибилности и корисничке systemd јединице за ауто-синхронизацију.

За ажурирање постојећег локалног репозиторијума:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Проверите спремност система пре синхронизације игара:

```bash
steam-auto-run --doctor
```

---

## Комплетан ланац покретања (End-to-End)

1. **Одређивање AppID-а:** Проверава редом `SteamAppId`, `STEAM_COMPAT_APP_ID`, затим `GAMEID` (уклањајући евентуални префикс `umu-` за Lutris/Heroic/UMU).
2. **Откривање библиотека и пречица:** `steam-auto-detect` претражује основне Steam директоријуме и секундарне библиотеке у `libraryfolders.vdf`, чита `appmanifest_<APPID>.acf`, или у режиму само за читање прелази на бинарни `userdata/*/config/shortcuts.vdf`, а затим извршава једнопролазни `find` до 10 нивоа дубине (изостављајући `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Петостепени приоритет класификације:**
   - **1. `competitive-anticheat`:** Познати такмичарски AppID или детектовани анти-чит runtime (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE итд.). Искључује OptiScaler, MLFG, vkBasalt и асинхрони DXVK; укључује ниску латенцију и мрежни QoS за сесију.
   - **2. `vr`:** Детектовани `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` или заставице пречице `vr-run`/`-vr`. Извози `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Модуларни FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Омогућава надоградњу на FSR4 на нивоу драјвера (`PROTON_FSR4_UPGRADE=1` или `PROTON_FSR4_RDNA3_UPGRADE=1` на AMD RDNA 3).
   - **4. `legacy-upscaler`:** Старије DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) или FSR 2/3.0 DLL библиотеке. Поставља `AUTO_OPTISCALER=1` и смернице у `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Безбедан нативни Wine Wayland + VRR профил ниске латенције.
4. **Ограничавање фрејмова за VRR:** Експлицитни `VRR_CAP=<fps>` увек има предност (`VRR_CAP=0` искључује ограничење). У супротном се активна фреквенција освежавања екрана очитава преко `kscreen-doctor` (активни `*` режим у KDE Plasma 6 или старији `Hz`), `wlr-randr` или `xrandr` и подразумевано примењује 1:1 (`240 FPS` на 240 Hz). Укључите `VRR_MINUS_MARGIN=1` за опциону `-6%` VRR безбедносну маргину (`hz * 94 / 100`, нпр. `225 FPS` на 240 Hz). У Gamescope сесијама DXVK/VKD3D ограничења се изостављају осим ако `VRR_CAP` није експлицитно задат.
5. **Заштитна правила међусобног искључивања:**
   - **FSR 4 / OptiScaler + vkBasalt:** Увек намеће `ENABLE_VKBASALT=0` када је активан `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` или `USE_OPTISCALER=1` (спречава двоструко изоштравање и HDR10 клипинг).
   - **MLFG + ниска латенција / VRR ограничења:** `MLFG=1` (`USE_MLFG=1`) извози `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, поништава `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` и `DXVK_FRAME_PACE`, и извози `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` на AMD RDNA 3. Када је `USE_MLFG=0` и VRR ограничење активно, извози се `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Модерни DX12 + Safe DX12:** На AMD-у извози `PROTON_NATIVE_AGS=1` и `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` када је `USE_SAFEDX12=0` (чисто изостављено када је `SAFEDX12=1`).
6. **Мапирање токена компатибилности:** Управљане опције се додају без преписивања постојећих корисничких вредности у обе променљиве `PROTON_ADD_CONFIG` и `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Аутоматски HDR у KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Када је укључен ван Gamescope-а уз `DXVK_HDR=1` (или `USE_HDR=1`), проверава примарни активни излаз преко `kscreen-doctor -o`; ако је HDR тренутно искључен, укључује га пре покретања и враћа SDR у `EXIT`/`INT`/`TERM` trap-у.
8. **Тихи frametime бенчмаркинг (`BENCH=1`):** Покреће MangoHud у скривеном CSV режиму (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), по изласку анализира времена фрејмова, додаје `Avg FPS`, `1% Low FPS` и `P99 (ms)` у `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` и брише привремене CSV датотеке.
9. **Аутоматски опоравак у Безбедни режим након брзог пада:** Ако Proton/Windows игра заврши са ненултим кодом за мање од `20s` (подесиво преко `SAP_CRASH_THRESHOLD_SEC`) док су активне експерименталне Wayland или DX12 заставице (`USE_XWAYLAND=0` или `USE_SAFEDX12=0`), уписује `crash_hint` у `last-<APPID>.log` и `last-launch.log`, а када је GUI активан нуди чување `USE_XWAYLAND=1` + `USE_SAFEDX12=1` за наредно покретање.
10. **Животни циклус планера и мреже:** Извршава се кроз ланац `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (само када `ananicy-cpp.service` није активан) -> директно покретање, уз опциони `PRIME=1` (`prime-run`). Ако је `USE_NET_OPT=1`, `steam-net-boost` позива референтно бројани `on`/`off` са `flock` уз очување статичних коренских CAKE и HTB + лисних CAKE хијерархија.

---

## Јединствени контролни центар (`steam-auto-ui`)

Покрените `steam-auto-ui` из менија апликација, преко `steam-auto-run --ui` или директно:

```bash
steam-auto-ui                 # Аутоматски бира Qt6 GUI (PyQt6/PySide6) или curses TUI
steam-auto-ui --gui           # Присиљава нативни Qt6 GUI прозор
steam-auto-ui --tui           # Присиљава stdlib curses TUI (ради преко SSH)
steam-auto-ui --lang fi       # Покреће са експлицитним језиком интерфејса (подржано 27 језика)
steam-auto-ui --check         # Извршава headless самопроверу (исписује JSON дијагностику)
```

`steam-auto-ui` аутоматски детектује системски локал из `LC_ALL` / `LC_MESSAGES` / `LANG` и нуди падајући мени за промену језика уживо у Qt6 GUI (и тастер `L` у `curses` TUI) ради тренутног пребацивања између свих 27 језика (укључујући `sr`) без поновног покретања.

### Пет синхронизованих приказа

1. **Игре и профили (Games & Profiles):** Филтрирајућа табела Steam игара и Non-Steam ставки само за читање из `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), значка Upscaler SDK (`AUTO_UPSCALER_INFO`), валидација међусобног искључивања уживо за свих 10 прекидача профила + `VRR_CAP`, `Dry-Run Preview`, дугме за прелазак на `Benchmarks` и `Reset Profile`.
2. **Систем и телеметрија (System & Telemetry):** Неблокирајући приказ уживо за `steam-auto-run --doctor`, стање `scxctl get` / `sched_ext`, верзије инсталираног стека (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), заузеће кеша шејдера (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), упозорења о downgrade-у git/AUR пакета из `/var/log/pacman.log`, VRAM/оптерећење/температура GPU-а, проток и `av_delay` из `tc -s qdisc` за LAN (`10:`) наспрам WAN (`20:`/root) и `vr-mode status`.
3. **Синхронизација библиотеке (Library Sync):** Упозоравајући банер уживо када је Steam покренут, плус акције једним кликом за `--report`, `--sanitize --dry-run`, `--sanitize` (одбијено док Steam ради) и `--migrate-cachy-run`.
4. **Логови и опоравак (Logs & Recovery):** Преглед `last-launch.log` и `last-<APPID>.log`, провера `crash_hint` упозорења и примена Безбедног режима једним кликом (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Бенчмаркови (Benchmarks):** Филтрирајућа упоредна табела `BENCH=1` мерења фрејмова (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR оркестрација (`vr-run`)

У Steam-у поставите **Properties > General > Launch Options** за VR наслове на:

```text
vr-run %command%
```

- Уклања наслеђене поставке за равне екране (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Аутоматски бира дискретну GPU са највише VRAM-а преко `MESA_VK_DEVICE_SELECT` и поставља `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` на AMD GPU-овима.
- Динамички открива WiVRn и xrizer OpenXR/OpenVR путање (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) и конфигурише `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` и `LD_LIBRARY_PATH` без преписивања експлицитних корисничких променљивих.
- Референтно броји `vr-mode on` / `vr-mode off` у `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (са `flock`) када је `vr-mode` инсталиран (`VR_AUTO_MODE=0` искључује ову функцију).
- Извршава се кроз исти ланац планера који уважава `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> директан `exec`).
- Израчунате променљиве можете прегледати у било ком тренутку помоћу `vr-run --dry-run`.

`steam-auto-run` аутоматски заобилази SteamVR (`250820`) и покретања са `-vr`/`--vr`, док `steam-auto-sync` аутоматски додељује и чува `vr-run %command%` за VR наслове.

---

## Синхронизација Steam библиотеке (`steam-auto-sync`)

Потпуно затворите Steam пре уписа у `localconfig.vdf`:

```bash
steam-auto-sync --report              # Ревизија библиотеке и shortcuts.vdf само за читање
steam-auto-sync --print-library-paths # Приказује све откривене Steam библиотеке
steam-auto-sync --dry-run             # Преглед измена
steam-auto-sync                       # Убацује steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Преглед чишћења старих заставица
steam-auto-sync --sanitize            # Чисти неуредне/заостале заставице (алијас: --clean)
steam-auto-sync --migrate-cachy-run   # Мигрира старе cachy-run профиле
steam-auto-sync --remove              # Уклања steam-auto-run омотач
```

- Резервне копије са временском ознаком `localconfig.vdf.bak.*` аутоматски се скраћују опцијом `--keep-backups N` (подразумевано `10`; `0` чува све).
- Конкретне AppID-ове можете искључити навођењем (један по реду, дозвољени су `#` коментари) у `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Systemd посматрач ауто-синхронизације (`./install.sh --with-auto-sync` или `steam-auto-sync --install-systemd`) покреће `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` приликом промене Steam манифеста.

---

## Референца за CLI и профиле

### Команде

| Намена | Команда |
| --- | --- |
| Провера спремности система | `steam-auto-run --doctor` (алијас `--check-system`) |
| Покретање Контролног центра (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` или `steam-auto-run --ui` |
| Инспекција игре (читљиво за људе) | `steam-auto-run --inspect APPID` |
| Инспекција игре (JSON) | `steam-auto-detect --inspect --json APPID` |
| Интерактивна измена профила | `steam-auto-run --configure APPID` |
| Преглед разрешеног окружења за покретање | `steam-auto-run --dry-run APPID` |
| Ресетовање сачуваног профила | `steam-auto-run --reset APPID` |
| Листа сачуваних профила | `steam-auto-run --list-profiles` |
| Приказ последњег лога покретања | `steam-auto-run --last-log [APPID]` |
| Преглед VR окружења за покретање | `vr-run --dry-run` |
| Провера мрежног помоћника (само за читање) | `steam-net-boost status [IFACE]` |

### Кључеви сачуваних `.env` профила и променљиве окружења

Датотеке профила налазе се у `~/.config/steam-auto-profiler/profiles/<APPID>.env` и прихватају искључиво дозвољен списак уноса у формату `KEY=VALUE` (супституције shell команди и непознати кључеви се безбедно игноришу):

| `.env` кључ | Env замена | Ефекат |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Присиљава XWayland уместо нативног Wine Wayland-а |
| `USE_FSR4=0` | `FSR4=0` | Искључује FSR 4 надоградњу на нивоу драјвера (подразумевано `1`) |
| `USE_MLFG=1` | `MLFG=1` | Укључује генерисање фрејмова (искључује Anti-Lag, ниску латенцију и VRR лимите) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Укључује OptiScaler мост (блокиран за `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Укључује vkBasalt изоштравање (искључено када је активан FSR 4 или OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Изоставља експерименталне `VKD3D_CONFIG` заставице и токен `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Активира мрежни QoS сесије преко `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Преферира нативну SDL / Steam Input емулацију |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Чува Steam Overlay `LD_PRELOAD` |
| `USE_CEF_FIX=1` | `CEF=1` | Додаје `--in-process-gpu` за CEF покретаче |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Искључује NTSync за старије наслове |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Искључује декорације менаџера прозора |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Прилагођени DXVK/VKD3D лимит фрејмова (`0` искључује ограничење) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Примењује `-6%` маргину у односу на освежавање монитора (нпр. `225 FPS` на 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Дозвољава блокирање пречица под Wine Wayland-ом (подразумевано `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Аутоматски укључује HDR у KDE Plasma 6 при покретању и враћа SDR при изласку |
| — | `BENCH=1`, `BENCH_DURATION=60` | Покреће тихи MangoHud CSV бенчмарк и чува JSON резиме |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Потискује или поново отвара `kdialog`/`zenity` контролну листу пре покретања |
| — | `FSR_HUD=1` | Извози променљиве HUD индикатора за FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Додаје `-vulkan` / омотава са `prime-run` |
| — | `GAMEID=umu-<appid>` | Одређује AppID за UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus и UMU

- **Lutris:** Укључите напредне опције, изаберите `proton-cachyos-slr` (или своју верзију Proton-а), искључите Lutris runtime, преферирајте системске библиотеке и поставите префикс команде на `steam-auto-run`.
- **Heroic / Faugus:** Изаберите `proton-cachyos-slr` и додајте `steam-auto-run` као wrapper / префикс команде.
- **UMU / Protonfixes:** По потреби извезите `PROTON_VERB=waitforexitandrun` и `GAMEID=umu-<appid>`.

---

## Решавање проблема

- **Брз пад на Wayland-у или DX12:** Отворите **Logs & Recovery** у `steam-auto-ui` (или покрените `steam-auto-run --last-log APPID`) и примените Безбедни режим (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), или покрените `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Анти-чит игре се не покрећу:** Користите `proton-cachyos-slr` (Steam Linux Runtime) и покрените `steam-auto-run --doctor` да проверите EAC v2, `/dev/ntsync` и `vm.max_map_count`.
- **Steam враћа старе опције покретања:** Потпуно затворите Steam пре покретања `steam-auto-sync` или `steam-auto-sync --sanitize`.
- **Погрешан или непостојећи VRR лимит:** Поставите експлицитно `VRR_CAP=<fps>`, `VRR_CAP=0` да га искључите или `VRR_MINUS_MARGIN=1` за `-6%` маргину. У Gamescope-у само експлицитни `VRR_CAP` извози DXVK/VKD3D лимите.
- **Провера мрежног QoS-а:** Покрените `steam-net-boost status` (без root привилегија, само за читање). Инсталирајте root помоћник преко `./install.sh --with-net-boost` ако желите аутоматски мрежни QoS за сесију.

Погледајте и [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) и [i18n Index](../README.md) са свих 27 локализованих водича.
