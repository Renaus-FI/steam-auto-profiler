# Посібник користувача Steam Auto-Profiler

> Оригінальна документація: [English User Guide](../../USER_GUIDE.md) · Усі мови: [i18n Index](../README.md)

Цей посібник охоплює повне встановлення, оркестрацію запуску плоских (flatscreen) і VR-ігор, єдиний центр керування `steam-auto-ui`, синхронізацію бібліотеки Steam, бенчмаркінг і вирішення проблем для **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler — це легкий запускач і центр керування на Bash/Python для Linux, який аналізує Steam AppID (або сторонній ярлик Non-Steam), застосовує контекстно-залежний профіль із жорсткими захисними обмеженнями для драйверів, апскейлерів та античитів і запускає наявну команду гри. Він ніколи не постачає й не впроваджує сторонні середовища виконання Proton.

---

## Вимоги

- Сесія робочого столу Linux (KDE Plasma 6 / Wayland, GNOME, wlroots або X11), Bash 5+, Python 3.10+, Steam і стандартні базові утиліти.
- Опціональний нативний графічний інтерфейс центру керування: `PyQt6` або `PySide6` (за відсутності автоматично переходить на TUI на базі стандартної бібліотеки `curses` без зовнішніх залежностей).
- Опціональні діалоги передзапускового чек-листа: `kdialog` або `zenity`.
- Опціональний прихований бенчмаркінг часу кадру (frametime): `mangohud`.
- Опціональний мережевий помічник для ігрових сесій: `tc`, `ip` і `ethtool` (`sudo` потрібен лише під час встановлення з прапорцем `--with-net-boost`).

---

## Встановлення та оновлення

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` копіює всі шість виконуваних файлів (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` і `steam-auto-ui`) до `~/.local/bin`, встановлює ярлик робочого столу (`~/.local/share/applications/steam-auto-profiler.desktop`), створює `~/.config/steam-auto-profiler/profiles` і додає стандартні пресети vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Переконайтеся, що `~/.local/bin` є у `PATH`.

Опціональні прапорці інсталятора можна поєднувати:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: встановлює `/usr/local/bin/steam-net-boost` (а також системні копії інших скриптів) і вузькообмежене правило `sudoers` без пароля для `steam-net-boost`.
- `--compat-cachy-run`: зберігає наявний `/usr/local/bin/cachy-run` як `/usr/local/bin/cachy-run.bak` (якщо це ще не обгортка Steam Auto-Profiler) та встановлює перенаправляючу обгортку на `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): встановлює та вмикає користувацький юніт systemd `steam-auto-profiler-sync.path` і відповідний oneshot-сервіс для всіх виявлених бібліотек Steam.
- `--uninstall`: видаляє встановлені бінарники, ярлик робочого столу, опціональний мережевий помічник і правило `sudoers`, обгортку сумісності та користувацькі юніти systemd для автосинхронізації.

Щоб оновити наявну копію репозиторію:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Перевірте готовність системи перед синхронізацією ігор:

```bash
steam-auto-run --doctor
```

---

## Повний конвеєр запуску

1. **Визначення AppID:** перевіряє `SteamAppId`, `STEAM_COMPAT_APP_ID`, а потім `GAMEID` (видаляючи префікс `umu-` для Lutris/Heroic/UMU).
2. **Пошук у бібліотеках і ярликах:** `steam-auto-detect` сканує кореневі каталоги Steam та додаткові бібліотеки з `libraryfolders.vdf`, читає `appmanifest_<APPID>.acf` або в режимі «лише читання» звертається до бінарного `userdata/*/config/shortcuts.vdf`, після чого виконує однопрохідний `find` глибиною до 10 рівнів (відсікаючи `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **П'ятирівневий пріоритет класифікації:**
   - **1. `competitive-anticheat`:** відомий змагальний AppID або виявлене середовище античиту (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE тощо). Вимикає OptiScaler, MLFG, vkBasalt і асинхронний DXVK; вмикає режим низької затримки та мережевий QoS для сесії.
   - **2. `vr`:** виявлено `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` або прапорці ярлика `vr-run`/`-vr`. Експортує `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** модульний FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Вмикає оновлення до FSR 4 на рівні драйвера (`PROTON_FSR4_UPGRADE=1` або `PROTON_FSR4_RDNA3_UPGRADE=1` на AMD RDNA 3).
   - **4. `legacy-upscaler`:** застарілі DLL для DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) або FSR 2/3.0. Встановлює `AUTO_OPTISCALER=1` і формує підказку `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** безпечний профіль із нативним Wine Wayland і VRR із низькою затримкою.
4. **Обмеження частоти кадрів під VRR:** явне значення `VRR_CAP=<fps>` завжди має пріоритет (`VRR_CAP=0` вимикає обмеження). Інакше активна частота оновлення дисплея визначається через `kscreen-doctor` (активний режим `*` у KDE Plasma 6 або застарілий вивід `Hz`), `wlr-randr` або `xrandr` і типово застосовується 1:1 (`240 FPS` на 240 Гц). Увімкніть `VRR_MINUS_MARGIN=1` для опціонального запасу VRR `-6%` (`hz * 94 / 100`, наприклад `225 FPS` на 240 Гц). У сесіях Gamescope обмеження DXVK/VKD3D не задаються, якщо `VRR_CAP` не вказано явно.
5. **Захист від конфліктуючих параметрів (взаємне виключення):**
   - **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` примусово застосовується щоразу, коли активні `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` або `USE_OPTISCALER=1` (запобігає подвійному підвищенню різкості та кліпінгу HDR10).
   - **MLFG + Low-Latency / обмеження VRR:** `MLFG=1` (`USE_MLFG=1`) експортує `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, скидає `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` і `DXVK_FRAME_PACE`, а на AMD RDNA 3 експортує `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. Коли `USE_MLFG=0` і обмеження VRR активне, експортується `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Сучасний DX12 + Safe DX12:** експортує `PROTON_NATIVE_AGS=1` на AMD і `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` за `USE_SAFEDX12=0` (коректно пропускається при `SAFEDX12=1`).
6. **Зіставлення compat-токенів:** керовані функції додаються без перезапису наявних користувацьких значень одночасно до `PROTON_ADD_CONFIG` та `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Автоперемикання HDR у KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** коли увімкнено поза Gamescope разом із `DXVK_HDR=1` (або `USE_HDR=1`), перевіряє основний активний екран через `kscreen-doctor -o`; якщо HDR наразі вимкнено, вмикає його перед запуском і відновлює SDR в обробнику `EXIT`/`INT`/`TERM`.
8. **Прихований бенчмаркінг часу кадру (`BENCH=1`):** запускає MangoHud у прихованому CSV-режимі (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), після завершення гри аналізує frametime, додає `Avg FPS`, `1% Low FPS` і `P99 (ms)` до `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` і видаляє тимчасові CSV-файли.
9. **Автовідновлення в безпечний режим після швидкого збою:** якщо гра Proton/Windows завершується з ненульовим кодом менш ніж за `20s` (налаштовується через `SAP_CRASH_THRESHOLD_SEC`), коли активні експериментальні прапорці Wayland або DX12 (`USE_XWAYLAND=0` або `USE_SAFEDX12=0`), записує `crash_hint` у `last-<APPID>.log` і `last-launch.log`, а за активного GUI пропонує зберегти `USE_XWAYLAND=1` + `USE_SAFEDX12=1` для наступного запуску.
10. **Планувальник і життєвий цикл мережі:** виконує запуск ланцюжком `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (лише коли `ananicy-cpp.service` неактивний) -> прямий запуск, з опціональним `PRIME=1` (`prime-run`). Якщо `USE_NET_OPT=1`, `steam-net-boost` виконує `on`/`off` із підрахунком посилань і `flock`, зберігаючи статичний кореневий CAKE та ієрархії HTB + листовий CAKE.

---

## Єдиний центр керування (`steam-auto-ui`)

Запускайте `steam-auto-ui` із меню програм робочого столу, через `steam-auto-run --ui` або напряму:

```bash
steam-auto-ui                 # Автовизначення Qt6 GUI (PyQt6/PySide6) або curses TUI
steam-auto-ui --gui           # Примусово відкрити нативне вікно Qt6 GUI
steam-auto-ui --tui           # Примусово запустити curses TUI зі stdlib (працює через SSH)
steam-auto-ui --lang fi       # Запуск із явним вибором мови інтерфейсу (напр., --lang uk; 27 мов)
steam-auto-ui --check         # Автономна самоперевірка (виводить JSON-діагностику)
```

`steam-auto-ui` автоматично визначає системну локаль із `LC_ALL` / `LC_MESSAGES` / `LANG` і надає випадаючий список вибору мови у Qt6 GUI (та гарячу клавішу `L` у `curses` TUI) для миттєвого перемикання між усіма 27 мовами без перезапуску.

### П'ять синхронізованих розділів

1. **Ігри та профілі (Games & Profiles):** фільтрована таблиця ігор Steam і записів Non-Steam `shortcuts.vdf` лише для читання (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), бейдж SDK апскейлера (`AUTO_UPSCALER_INFO`), перевірка взаємних виключень наживо для всіх 10 перемикачів профілю + `VRR_CAP`, попередній перегляд `Dry-Run Preview`, кнопка переходу до `Benchmarks` і `Reset Profile`.
2. **Система та телеметрія (System & Telemetry):** неблокувальний вивід наживо результатів `steam-auto-run --doctor`, стану `scxctl get` / `sched_ext`, версій встановленого стеку (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), обсягу кешу шейдерів (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), попереджень про даунгрейд git/AUR із `/var/log/pacman.log`, VRAM/завантаження/температури GPU, пропускної здатності та `av_delay` із `tc -s qdisc` для LAN (`10:`) проти WAN (`20:`/root), а також `vr-mode status`.
3. **Синхронізація бібліотеки (Library Sync):** живий банер стану запущеного Steam і запуск в один клік `--report`, `--sanitize --dry-run`, `--sanitize` (блокується, доки Steam працює) та `--migrate-cachy-run`.
4. **Логи та відновлення (Logs & Recovery):** перегляд `last-launch.log` і `last-<APPID>.log`, перевірка сповіщень `crash_hint` і застосування безпечного режиму Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) в один клік.
5. **Бенчмарки (Benchmarks):** фільтрована порівняльна таблиця прогонів часу кадру `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Оркестрація VR (`vr-run`)

У Steam відкрийте **Властивості > Загальні > Параметри запуску** для VR-ігор і задайте:

```text
vr-run %command%
```

- Очищає успадковані flatscreen-перевизначення (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Автоматично обирає дискретну відеокарту з найбільшим обсягом VRAM через `MESA_VK_DEVICE_SELECT` і встановлює `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` на GPU AMD.
- Динамічно визначає шляхи OpenXR/OpenVR для WiVRn та xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) і налаштовує `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` та `LD_LIBRARY_PATH`, не перезаписуючи явні перевизначення користувача.
- Веде підрахунок посилань для `vr-mode on` / `vr-mode off` у `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (із `flock`), якщо встановлено `vr-mode` (`VR_AUTO_MODE=0` вимикає це).
- Працює через той самий ланцюжок планувальників з урахуванням `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> прямий `exec`).
- Попередньо переглянути визначені змінні можна будь-коли командою `vr-run --dry-run`.

`steam-auto-run` автоматично обходить SteamVR (`250820`) і запуски з `-vr`/`--vr`, а `steam-auto-sync` автоматично призначає та зберігає `vr-run %command%` для VR-ігор.

---

## Синхронізація бібліотеки Steam (`steam-auto-sync`)

Повністю закрийте Steam перед записом до `localconfig.vdf`:

```bash
steam-auto-sync --report              # Аудит бібліотеки та shortcuts.vdf у режимі «лише читання»
steam-auto-sync --print-library-paths # Показати всі виявлені бібліотеки Steam
steam-auto-sync --dry-run             # Попередній перегляд змін
steam-auto-sync                       # Додати steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Попередній перегляд очищення застарілих прапорців
steam-auto-sync --sanitize            # Очистити зайві/застарілі прапорці (аліас: --clean)
steam-auto-sync --migrate-cachy-run   # Мігрувати старі профілі cachy-run
steam-auto-sync --remove              # Видалити обгортку steam-auto-run
```

- Резервні копії `localconfig.vdf.bak.*` із мітками часу очищаються автоматично параметром `--keep-backups N` (типово `10`; `0` зберігає всі).
- Щоб виключити певні AppID, перелічіть їх (по одному в рядку, дозволено коментарі `#`) у `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Спостерігач systemd для автосинхронізації (`./install.sh --with-auto-sync` або `steam-auto-sync --install-systemd`) запускає `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`, коли змінюються маніфести Steam.

---

## Довідник CLI та профілів

### Команди

| Призначення | Команда |
| --- | --- |
| Аудит готовності системи | `steam-auto-run --doctor` (аліас `--check-system`) |
| Запуск центру керування (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` або `steam-auto-run --ui` |
| Інспекція гри (читабельний формат) | `steam-auto-run --inspect APPID` |
| Інспекція гри (JSON) | `steam-auto-detect --inspect --json APPID` |
| Інтерактивне переналаштування профілю | `steam-auto-run --configure APPID` |
| Попередній перегляд середовища запуску | `steam-auto-run --dry-run APPID` |
| Скидання збереженого профілю | `steam-auto-run --reset APPID` |
| Список збережених профілів | `steam-auto-run --list-profiles` |
| Показати останній лог запуску | `steam-auto-run --last-log [APPID]` |
| Попередній перегляд VR-середовища | `vr-run --dry-run` |
| Перевірка мережевого помічника (лише читання) | `steam-net-boost status [IFACE]` |

### Ключі `.env`-профілів і перевизначення змінних середовища

Файли профілів зберігаються у `~/.config/steam-auto-profiler/profiles/<APPID>.env` і приймають дозволений формат `KEY=VALUE` (підстановки команд оболонки та невідомі ключі безпечно ігноруються):

| Ключ `.env` | Змінна середовища | Дія |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Примусово використовувати XWayland замість нативного Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Вимкнути оновлення до FSR 4 на рівні драйвера (типово `1`) |
| `USE_MLFG=1` | `MLFG=1` | Увімкнути генерацію кадрів (вимикає Anti-Lag, низьку затримку та ліміти VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Увімкнути міст OptiScaler (примусово вимкнено для `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Увімкнути різкість vkBasalt (вимикається за активних FSR 4 або OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Пропустити експериментальні прапорці `VKD3D_CONFIG` і токен `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Активувати мережевий QoS на час сесії через `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Надати перевагу нативному SDL / емуляції Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Зберегти `LD_PRELOAD` для оверлея Steam |
| `USE_CEF_FIX=1` | `CEF=1` | Додати `--in-process-gpu` для лаунчерів на базі CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Вимкнути NTSync для старих ігор |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Вимкнути декорації віконного менеджера |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Власне обмеження кадрів DXVK/VKD3D (`0` вимикає обмеження) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Застосувати запас `-6%` від частоти оновлення монітора (напр., `225 FPS` на 240 Гц) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Дозволити перехоплення гарячих клавіш у Wine Wayland (типово `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Автоматично вмикати HDR у KDE Plasma 6 під час запуску й повертати SDR при виході |
| — | `BENCH=1`, `BENCH_DURATION=60` | Запустити прихований CSV-бенчмарк MangoHud і зберегти підсумок у JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Приховати або примусово відкрити передзапусковий чек-лист `kdialog`/`zenity` |
| — | `FSR_HUD=1` | Експортувати змінні індикаторів HUD для FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Додати `-vulkan` / обгорнути запуск через `prime-run` |
| — | `GAMEID=umu-<appid>` | Визначити AppID для UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus та UMU

- **Lutris:** увімкніть розширені параметри, виберіть `proton-cachyos-slr` (або вашу збірку Proton), вимкніть Lutris runtime, увімкніть перевагу системних бібліотек і задайте `steam-auto-run` як префікс команди.
- **Heroic / Faugus:** виберіть `proton-cachyos-slr` і додайте `steam-auto-run` як обгортку / префікс команди.
- **UMU / Protonfixes:** за потреби експортуйте `PROTON_VERB=waitforexitandrun` і `GAMEID=umu-<appid>`.

---

## Вирішення проблем

- **Швидкий виліт на Wayland або DX12:** відкрийте **Logs & Recovery** у `steam-auto-ui` (або виконайте `steam-auto-run --last-log APPID`) та застосуйте Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), або запустіть `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Ігри з античитом не запускаються:** використовуйте `proton-cachyos-slr` (Steam Linux Runtime) і виконайте `steam-auto-run --doctor`, щоб перевірити EAC v2, `/dev/ntsync` і `vm.max_map_count`.
- **Steam скидає параметри запуску:** повністю закрийте Steam перед виконанням `steam-auto-sync` або `steam-auto-sync --sanitize`.
- **Неправильне або відсутнє обмеження VRR:** задайте `VRR_CAP=<fps>` явно, `VRR_CAP=0` для вимкнення або `VRR_MINUS_MARGIN=1` для запасу `-6%`. У Gamescope обмеження DXVK/VKD3D експортуються лише за явно заданого `VRR_CAP`.
- **Перевірка мережевого QoS:** виконайте `steam-net-boost status` (без прав root, лише читання). Встановіть системний помічник командою `./install.sh --with-net-boost`, якщо потрібен автоматичний QoS для сесій.

---

## Нове у v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 та Steam Controller 2026)

- **Прапорці Mesa 27.0 / RDNA 4:** `TRANSFER_QUEUE=1` (дедуплікований `RADV_PERFTEST=sam,transfer_queue` для RDNA 3/4), `NATIVE_ANTILAG=1` (нативний `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, заблоковано в античиті та MLFG) і `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Режим Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** експериментальний стек для ігор без античиту з `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1` і `WAYLANDDRV_RAWINPUT=1` (лише у нативному Wayland поза Gamescope).
- **Захист Hunt: Showdown 1896 (`AppID 594650`):** примусово вмикає `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, `USE_NET_OPT=1`, а `--doctor` та `steam-auto-ui` перевіряють `config.vdf` на `Proton 11.0-2` або `Proton Hotfix`.
- **Steam Controller 2026 (`Triton`/`Proteus`) і Wireless Steam Puck (`28de:{1302,1304,1005,1007}`):** 4 режими (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` зберігає нативний Wayland + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`, без `sdlinput`), автоматично надсилає `steam://forceinputappid/<APPID>` із фоновим `udevadm`-перепідключенням і скидає `steam://forceinputappid/0` на виході. Ручний запуск: `steam-auto-run --reapply-input <APPID|0>`; udev-правила: `./install.sh --with-steam-controller`.

---

Див. також [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) (внутрішня архітектура) та [i18n Index](../README.md) для всіх 27 локалізованих посібників.
