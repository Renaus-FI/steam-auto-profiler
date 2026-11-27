# Ръководство за потребителя на Steam Auto-Profiler

> 🌐 [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Това ръководство обхваща пълната инсталация, оркестрацията за стартиране на стандартни и VR игри, контролния център `steam-auto-ui`, синхронизацията на библиотеката, бенчмаркинга и отстраняването на проблеми за **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler е лек Bash/Python стартер и контролен център за Linux, който проверява Steam AppID (или пряк път към игра извън Steam), прилага контекстно-съобразен профил със строги защитни правила за драйвери, ъпскейлъри и античийт системи и стартира съществуващата команда на играта. Никога не пакетира и не инжектира външна Proton среда за изпълнение.

---

## Изисквания

- Linux десктоп сесия (KDE Plasma 6 / Wayland, GNOME, wlroots или X11), Bash 5+, Python 3.10+, Steam и стандартни системни инструменти.
- Незадължителен нативен GUI контролен център: `PyQt6` или `PySide6` (автоматично преминава към `curses` TUI без външни зависимости от стандартната библиотека).
- Незадължителни диалози с контролен списък преди стартиране: `kdialog` или `zenity`.
- Незадължително тихо измерване на времето за кадър (frametime benchmarking): `mangohud`.
- Незадължителен мрежов помощник за сесията: `tc`, `ip` и `ethtool` (`sudo` е необходимо само по време на инсталация с `--with-net-boost`).

---

## Инсталация и актуализации

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` копира всички шест изпълними файла (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` и `steam-auto-ui`) в `~/.local/bin`, инсталира десктоп прекия път (`~/.local/share/applications/steam-auto-profiler.desktop`), създава `~/.config/steam-auto-profiler/profiles` и добавя стандартни vkBasalt пресети (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Уверете се, че `~/.local/bin` е включена в `PATH`.

Незадължителните флагове на инсталатора могат да се комбинират:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: инсталира `/usr/local/bin/steam-net-boost` (плюс системни копия на останалите скриптове) и тясно ограничено правило в sudoers без парола за `steam-net-boost`.
- `--compat-cachy-run`: запазва съществуващия `/usr/local/bin/cachy-run` като `/usr/local/bin/cachy-run.bak` (освен ако вече не е препращащият shim на Steam Auto-Profiler) и инсталира препращащ shim към `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): инсталира и активира потребителската systemd единица `steam-auto-profiler-sync.path` и съответната oneshot услуга за всички открити библиотеки на Steam.
- `--uninstall`: премахва инсталираните изпълними файлове, десктоп прекия път, незадължителния мрежов помощник/sudoers правилото, слоя за съвместимост и потребителските systemd единици за автосинхронизация.

За актуализиране на съществуващо локално копие:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Проверете готовността на системата преди синхронизиране на игрите:

```bash
steam-auto-run --doctor
```

---

## Пълен конвейер за стартиране (End-to-End)

1. **Определяне на AppID:** Проверява последователно `SteamAppId`, `STEAM_COMPAT_APP_ID`, след това `GAMEID` (премахвайки евентуален префикс `umu-` за Lutris/Heroic/UMU).
2. **Откриване на библиотеки и преки пътища:** `steam-auto-detect` претърсва основните папки на Steam и вторичните библиотеки в `libraryfolders.vdf`, чете `appmanifest_<APPID>.acf` или преминава в режим само за четене към двоичния `userdata/*/config/shortcuts.vdf`, след което извършва еднократно търсене с `find` до 10 нива дълбочина (пропускайки `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Петстепенна йерархия на класификация:**
   - **1. `competitive-anticheat`:** Известно състезателно AppID или засечена античийт среда (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE и др.). Изключва OptiScaler, MLFG, vkBasalt и асинхронен DXVK; включва ниска латентност и мрежов QoS за сесията.
   - **2. `vr`:** Засечени `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` или флагове на прекия път `vr-run`/`-vr`. Експортира `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Модулен FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Активира FSR4 надграждане на ниво драйвер (`PROTON_FSR4_UPGRADE=1` или `PROTON_FSR4_RDNA3_UPGRADE=1` при AMD RDNA 3).
   - **4. `legacy-upscaler`:** По-стари DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) или FSR 2/3.0 DLL библиотеки. Задава `AUTO_OPTISCALER=1` и насоки в `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Безопасен нативен Wine Wayland + VRR профил с ниска латентност.
4. **Ограничаване на кадрите за VRR:** Изрично зададено `VRR_CAP=<fps>` винаги има приоритет (`VRR_CAP=0` изключва ограничението). В противен случай активната честота на опресняване се определя чрез `kscreen-doctor` (активен `*` режим в KDE Plasma 6 или по-стария `Hz`), `wlr-randr` или `xrandr` и по подразбиране се прилага 1:1 (`240 FPS` на 240 Hz). Активирайте `VRR_MINUS_MARGIN=1` за незадължителния `-6%` VRR резерв (`hz * 94 / 100`, напр. `225 FPS` на 240 Hz). В Gamescope сесии лимитите за DXVK/VKD3D се пропускат, освен ако `VRR_CAP` не е зададен изрично.
5. **Защитни правила за взаимно изключване:**
   - **FSR 4 / OptiScaler + vkBasalt:** Винаги налага `ENABLE_VKBASALT=0`, когато е активно `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` или `USE_OPTISCALER=1` (предотвратява двойно изостряне и изрязване при HDR10).
   - **MLFG + ниска латентност / VRR лимити:** `MLFG=1` (`USE_MLFG=1`) експортира `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, премахва `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` и `DXVK_FRAME_PACE`, и експортира `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` при AMD RDNA 3. Когато `USE_MLFG=0` и VRR лимитът е активен, се експортира `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Модерен DX12 + Safe DX12:** Експортира `PROTON_NATIVE_AGS=1` при AMD и `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, когато `USE_SAFEDX12=0` (изчистено пропуснато при `SAFEDX12=1`).
6. **Картографиране на токени за съвместимост:** Управляваните функции се добавят, без да презаписват съществуващи потребителски стойности, едновременно в `PROTON_ADD_CONFIG` и `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Автоматичен HDR за KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Когато е включен извън Gamescope заедно с `DXVK_HDR=1` (или `USE_HDR=1`), проверява основния активен дисплей чрез `kscreen-doctor -o`; ако HDR е изключен, го активира преди стартиране и възстановява SDR чрез `EXIT`/`INT`/`TERM` trap.
8. **Тих frametime бенчмаркинг (`BENCH=1`):** Стартира MangoHud в скрит CSV режим (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), анализира времената за кадър при изход, добавя `Avg FPS`, `1% Low FPS` и `P99 (ms)` в `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` и изтрива временните CSV файлове.
9. **Автоматично възстановяване в Безопасен режим след бърз срив:** Ако Proton/Windows заглавие приключи с ненулев код за по-малко от `20s` (настройваемо чрез `SAP_CRASH_THRESHOLD_SEC`), докато са активни експериментални Wayland или DX12 флагове (`USE_XWAYLAND=0` или `USE_SAFEDX12=0`), записва `crash_hint` в `last-<APPID>.log` и `last-launch.log`, а при активен GUI предлага да запази `USE_XWAYLAND=1` + `USE_SAFEDX12=1` за следващото стартиране.
10. **Жизнен цикъл на диспечера и мрежата:** Преминава през веригата `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (само когато `ananicy-cpp.service` не е активна) -> директно изпълнение, с незадължителен `PRIME=1` (`prime-run`). При `USE_NET_OPT=1` `steam-net-boost` изпълнява `on`/`off` с броене на сесиите и `flock`, като запазва статичните коренови CAKE и HTB + листови CAKE йерархии.

---

## Единен контролен център (`steam-auto-ui`)

Стартирайте `steam-auto-ui` от менюто с приложения, чрез `steam-auto-run --ui` или директно:

```bash
steam-auto-ui                 # Автоматично открива Qt6 GUI (PyQt6/PySide6) или curses TUI
steam-auto-ui --gui           # Принудително стартира нативен Qt6 GUI прозорец
steam-auto-ui --tui           # Принудително стартира stdlib curses TUI (работи през SSH)
steam-auto-ui --lang fi       # Стартира с изричен език на интерфейса (поддържат се 27 езика)
steam-auto-ui --check         # Изпълнява headless самопроверка (извежда JSON диагностика)
```

`steam-auto-ui` автоматично разпознава системния локал от `LC_ALL` / `LC_MESSAGES` / `LANG` и предлага падащо меню за смяна на езика в реално време в Qt6 GUI (и клавиша `L` в `curses` TUI) за превключване между всички 27 езика (включително `bg`) без рестартиране.

### Пет синхронизирани изгледа

1. **Игри и профили (Games & Profiles):** Филтрируема таблица със Steam заглавия и записи извън Steam само за четене от `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), значка за Upscaler SDK (`AUTO_UPSCALER_INFO`), валидация на живо за взаимно изключване на всички 10 превключвателя на профила + `VRR_CAP`, `Dry-Run Preview`, бутон за преход към `Benchmarks` и `Reset Profile`.
2. **Система и телеметрия (System & Telemetry):** Неблокиращо отчитане на живо от `steam-auto-run --doctor`, състояние на `scxctl get` / `sched_ext`, инсталирани версии на стека (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), използване на шейдър кеша (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), предупреждения за downgrade на git/AUR пакети от `/var/log/pacman.log`, VRAM/натоварване/температура на GPU, пропускателна способност и `av_delay` от `tc -s qdisc` за LAN (`10:`) спрямо WAN (`20:`/root) и `vr-mode status`.
3. **Синхронизация на библиотеката (Library Sync):** Предупредителен банер на живо при работещ Steam плюс бутони с едно кликване за `--report`, `--sanitize --dry-run`, `--sanitize` (отказано, докато Steam работи) и `--migrate-cachy-run`.
4. **Логове и възстановяване (Logs & Recovery):** Преглед на `last-launch.log` и `last-<APPID>.log`, проверка на предупрежденията `crash_hint` и прилагане на Безопасен режим с едно кликване (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Бенчмаркове (Benchmarks):** Филтрируема сравнителна таблица на `BENCH=1` измерванията (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR оркестрация (`vr-run`)

В Steam задайте **Properties > General > Launch Options** за VR заглавия на:

```text
vr-run %command%
```

- Почиства наследените настройки за плосък екран (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Автоматично избира дискретната видеокарта с най-много VRAM чрез `MESA_VK_DEVICE_SELECT` и задава `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` при AMD GPU.
- Динамично открива OpenXR/OpenVR пътищата на WiVRn и xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) и конфигурира `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` и `LD_LIBRARY_PATH`, без да презаписва изрични потребителски настройки.
- Управлява с броене на референции `vr-mode on` / `vr-mode off` в `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (с `flock`), когато е инсталиран `vr-mode` (`VR_AUTO_MODE=0` го изключва).
- Изпълнява се през същата верига на диспечера, съобразена с `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> директен `exec`).
- Можете да прегледате изчислените променливи по всяко време с `vr-run --dry-run`.

`steam-auto-run` автоматично пропуска SteamVR (`250820`) и стартирания с `-vr`/`--vr`, а `steam-auto-sync` автоматично задава и запазва `vr-run %command%` за VR заглавия.

---

## Синхронизация на Steam библиотеката (`steam-auto-sync`)

Затворете Steam напълно преди запис в `localconfig.vdf`:

```bash
steam-auto-sync --report              # Одит на библиотеката и shortcuts.vdf само за четене
steam-auto-sync --print-library-paths # Показва всички открити библиотеки на Steam
steam-auto-sync --dry-run             # Преглед на промените
steam-auto-sync                       # Инжектира steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Преглед на почистването на стари флагове
steam-auto-sync --sanitize            # Почиства объркани/осиротели флагове (псевдоним: --clean)
steam-auto-sync --migrate-cachy-run   # Мигрира стари cachy-run профили
steam-auto-sync --remove              # Премахва обвивката steam-auto-run
```

- Резервните копия с времеви отпечатък `localconfig.vdf.bak.*` се почистват автоматично чрез `--keep-backups N` (по подразбиране `10`; `0` запазва всички).
- Можете да изключите конкретни AppID, като ги запишете (по едно на ред, позволени са `#` коментари) в `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Systemd наблюдателят за автосинхронизация (`./install.sh --with-auto-sync` или `steam-auto-sync --install-systemd`) стартира `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` при промяна на Steam манифестите.

---

## Справочник за CLI и профили

### Команди

| Предназначение | Команда |
| --- | --- |
| Одит на системната готовност | `steam-auto-run --doctor` (псевдоним `--check-system`) |
| Стартиране на Контролния център (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` или `steam-auto-run --ui` |
| Инспекция на игра (четима за човек) | `steam-auto-run --inspect APPID` |
| Инспекция на игра (JSON) | `steam-auto-detect --inspect --json APPID` |
| Интерактивна промяна на профил | `steam-auto-run --configure APPID` |
| Преглед на изчислената среда за стартиране | `steam-auto-run --dry-run APPID` |
| Нулиране на запазен профил | `steam-auto-run --reset APPID` |
| Списък със запазени профили | `steam-auto-run --list-profiles` |
| Показване на последния лог от стартиране | `steam-auto-run --last-log [APPID]` |
| Преглед на VR средата за стартиране | `vr-run --dry-run` |
| Проверка на мрежовия помощник (само за четене) | `steam-net-boost status [IFACE]` |

### Ключове в запазените `.env` профили и променливи на средата

Файловете с профили се намират в `~/.config/steam-auto-profiler/profiles/<APPID>.env` и приемат само разрешен списък от ключове във формат `KEY=VALUE` (командни субституции на shell и непознати ключове се игнорират безопасно):

| `.env` ключ | Env заместване | Ефект |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Принудително използва XWayland вместо нативен Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Изключва FSR 4 надграждането на ниво драйвер (по подразбиране `1`) |
| `USE_MLFG=1` | `MLFG=1` | Включва генериране на кадри (изключва Anti-Lag, ниска латентност и VRR лимити) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Включва OptiScaler мост (блокиран за `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Включва изостряне чрез vkBasalt (изключва се при активен FSR 4 или OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Пропуска експерименталните `VKD3D_CONFIG` флагове и токена `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Активира мрежов QoS за сесията чрез `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Предпочита нативна SDL / Steam Input емулация |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Запазва `LD_PRELOAD` за Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Добавя `--in-process-gpu` за CEF стартери |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Изключва NTSync за по-стари заглавия |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Изключва декорациите на прозоречния мениджър |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Персонален лимит на кадрите за DXVK/VKD3D (`0` изключва ограничението) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Прилага `-6%` резерв спрямо честотата на монитора (напр. `225 FPS` на 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Позволява прихващане на клавишни комбинации под Wine Wayland (по подразбиране `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Автоматично включва HDR в KDE Plasma 6 при стартиране и възстановява SDR при изход |
| — | `BENCH=1`, `BENCH_DURATION=60` | Изпълнява тих CSV бенчмарк с MangoHud и записва JSON обобщение |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Потиска или принудително отваря диалога `kdialog`/`zenity` преди стартиране |
| — | `FSR_HUD=1` | Експортира HUD индикаторни променливи за FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Добавя `-vulkan` / стартира чрез `prime-run` |
| — | `GAMEID=umu-<appid>` | Разпознава AppID за UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus и UMU

- **Lutris:** Включете разширените настройки, изберете `proton-cachyos-slr` (или вашата Proton версия), изключете Lutris runtime, предпочетете системните библиотеки и задайте `steam-auto-run` като префикс на командата.
- **Heroic / Faugus:** Изберете `proton-cachyos-slr` и добавете `steam-auto-run` като wrapper / префикс на командата.
- **UMU / Protonfixes:** При необходимост експортирайте `PROTON_VERB=waitforexitandrun` и `GAMEID=umu-<appid>`.

---

## Отстраняване на проблеми

- **Бърз срив под Wayland или DX12:** Отворете раздела **Logs & Recovery** в `steam-auto-ui` (или изпълнете `steam-auto-run --last-log APPID`) и приложете Безопасен режим (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), или стартирайте с `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Игрите с античийт не стартират:** Използвайте `proton-cachyos-slr` (Steam Linux Runtime) и изпълнете `steam-auto-run --doctor`, за да проверите EAC v2, `/dev/ntsync` и `vm.max_map_count`.
- **Steam връща старите опции за стартиране:** Затворете Steam напълно преди да изпълните `steam-auto-sync` или `steam-auto-sync --sanitize`.
- **Грешен или липсващ VRR лимит:** Задайте изрично `VRR_CAP=<fps>`, `VRR_CAP=0` за изключване или `VRR_MINUS_MARGIN=1` за `-6%` резерв. В Gamescope само изрично зададен `VRR_CAP` експортира DXVK/VKD3D лимити.
- **Проверка на мрежовия QoS:** Изпълнете `steam-net-boost status` (без root права, само за четене). Инсталирайте root помощника чрез `./install.sh --with-net-boost`, ако желаете автоматичен мрежов QoS за сесията.

---

## Новото във v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 и Steam Controller 2026)

- **Флагове Mesa 27.0 / RDNA 4:** `TRANSFER_QUEUE=1` (дедупликиран `RADV_PERFTEST=sam,transfer_queue` за RDNA 3/4), `NATIVE_ANTILAG=1` (нативен `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, блокиран при античийт и MLFG) и `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** експериментален стек за игри без античийт (`VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, `WAYLANDDRV_RAWINPUT=1` само в нативен Wayland извън Gamescope).
- **Защита Hunt: Showdown 1896 (`AppID 594650`):** налага `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0` и `USE_NET_OPT=1`; `--doctor` и `steam-auto-ui` проверяват `config.vdf` за `Proton 11.0-2` или `Proton Hotfix`.
- **Steam Controller 2026 / Wireless Puck (`28de:{1302,1304,1005,1007}`):** 4 режима (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` запазва нативен Wayland + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`, без `sdlinput`), прилага `steam://forceinputappid/<APPID>` с `udevadm` наблюдател за повторно свързване и нулира `steam://forceinputappid/0` при изход. Ръчно: `steam-auto-run --reapply-input <APPID|0>`; udev: `./install.sh --with-steam-controller`.

---

Вижте също [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) и [i18n Index](../README.md) за всички 27 локализирани ръководства.
