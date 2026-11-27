# Руководство пользователя Steam Auto-Profiler

> Оригинальная документация: [English User Guide](../../USER_GUIDE.md) · Все языки: [i18n Index](../README.md)

Это руководство охватывает полную установку, оркестрацию запуска плоских (flatscreen) и VR-игр, единый центр управления `steam-auto-ui`, синхронизацию библиотеки Steam, бенчмаркинг и устранение неполадок для **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler — это лёгкий запускающий инструмент и центр управления на Bash/Python для Linux, который анализирует Steam AppID (или сторонний ярлык Non-Steam), применяет контекстно-зависимый профиль со строгими защитными ограничениями для драйверов, апскейлеров и античитов, а затем запускает исходную команду игры. Он никогда не поставляет и не внедряет сторонние среды выполнения Proton.

---

## Требования

- Рабочий стол Linux (KDE Plasma 6 / Wayland, GNOME, wlroots или X11), Bash 5+, Python 3.10+, Steam и стандартные базовые утилиты.
- Опциональный нативный графический интерфейс центра управления: `PyQt6` или `PySide6` (при отсутствии автоматически переключается на TUI на базе стандартной библиотеки `curses` без внешних зависимостей).
- Опциональные диалоги предзапускового чек-листа: `kdialog` или `zenity`.
- Опциональный скрытый бенчмаркинг времени кадра (frametime): `mangohud`.
- Опциональный сетевой помощник для игровых сессий: `tc`, `ip` и `ethtool` (`sudo` требуется только во время установки с флагом `--with-net-boost`).

---

## Установка и обновления

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` копирует все шесть исполняемых файлов (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` и `steam-auto-ui`) в `~/.local/bin`, устанавливает ярлык рабочего стола (`~/.local/share/applications/steam-auto-profiler.desktop`), создаёт `~/.config/steam-auto-profiler/profiles` и добавляет стандартные пресеты vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Убедитесь, что `~/.local/bin` присутствует в `PATH`.

Опциональные флаги установщика можно комбинировать:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: устанавливает `/usr/local/bin/steam-net-boost` (а также системные копии остальных скриптов) и узкоограниченное правило `sudoers` без запроса пароля для `steam-net-boost`.
- `--compat-cachy-run`: сохраняет существующий `/usr/local/bin/cachy-run` как `/usr/local/bin/cachy-run.bak` (если это ещё не обёртка Steam Auto-Profiler) и устанавливает перенаправляющую обёртку на `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): устанавливает и включает пользовательский юнит systemd `steam-auto-profiler-sync.path` и соответствующий oneshot-сервис для всех обнаруженных библиотек Steam.
- `--uninstall`: удаляет установленные бинарники, ярлык рабочего стола, опциональный сетевой помощник и правило `sudoers`, обёртку совместимости и пользовательские юниты systemd для автосинхронизации.

Чтобы обновить уже клонированный репозиторий:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Проверьте готовность системы перед синхронизацией игр:

```bash
steam-auto-run --doctor
```

---

## Полный конвейер запуска

1. **Определение AppID:** проверяет `SteamAppId`, `STEAM_COMPAT_APP_ID`, затем `GAMEID` (удаляя префикс `umu-` для Lutris/Heroic/UMU).
2. **Поиск в библиотеках и ярлыках:** `steam-auto-detect` сканирует корневые каталоги Steam и дополнительные библиотеки из `libraryfolders.vdf`, читает `appmanifest_<APPID>.acf` или в режиме «только чтение» обращается к бинарному файлу `userdata/*/config/shortcuts.vdf`, после чего выполняет однопроходный `find` глубиной до 10 уровней (исключая `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Пятиуровневый приоритет классификации:**
   - **1. `competitive-anticheat`:** известный соревновательный AppID или обнаруженная среда античита (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE и др.). Отключает OptiScaler, MLFG, vkBasalt и асинхронный DXVK; включает режим низкой задержки и сетевой QoS для сессии.
   - **2. `vr`:** обнаружены `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` или флаги ярлыка `vr-run`/`-vr`. Экспортирует `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** модульный FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Включает обновление до FSR 4 на уровне драйвера (`PROTON_FSR4_UPGRADE=1` или `PROTON_FSR4_RDNA3_UPGRADE=1` на AMD RDNA 3).
   - **4. `legacy-upscaler`:** устаревшие DLL для DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) или FSR 2/3.0. Устанавливает `AUTO_OPTISCALER=1` и заполняет подсказку `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** безопасный профиль с нативным Wine Wayland и VRR с низкой задержкой.
4. **Ограничение FPS под частоту VRR:** явное значение `VRR_CAP=<fps>` всегда имеет наивысший приоритет (`VRR_CAP=0` отключает ограничение). В остальных случаях активная частота обновления дисплея определяется через `kscreen-doctor` (активный режим `*` в KDE Plasma 6 или устаревший вывод `Hz`), `wlr-randr` либо `xrandr` и по умолчанию применяется 1:1 (`240 FPS` на 240 Гц). Включите `VRR_MINUS_MARGIN=1` для опционального запаса VRR `-6%` (`hz * 94 / 100`, например `225 FPS` на 240 Гц). В сессиях Gamescope лимиты DXVK/VKD3D не задаются, если `VRR_CAP` не указан явно.
5. **Защита от конфликтующих параметров (взаимное исключение):**
   - **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` принудительно применяется всегда, когда активны `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` или `USE_OPTISCALER=1` (предотвращает двойное повышение резкости и клиппинг HDR10).
   - **MLFG + Low-Latency / лимиты VRR:** `MLFG=1` (`USE_MLFG=1`) экспортирует `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, сбрасывает `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` и `DXVK_FRAME_PACE`, а на AMD RDNA 3 экспортирует `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. Когда `USE_MLFG=0` и ограничение VRR активно, экспортируется `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Современный DX12 + Safe DX12:** экспортирует `PROTON_NATIVE_AGS=1` на AMD и `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` при `USE_SAFEDX12=0` (аккуратно опускается при `SAFEDX12=1`).
6. **Сопоставление compat-токенов:** управляемые функции добавляются без перезаписи существующих пользовательских значений сразу в `PROTON_ADD_CONFIG` и `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Автопереключение HDR в KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** если включено вне Gamescope вместе с `DXVK_HDR=1` (или `USE_HDR=1`), проверяет основной активный экран через `kscreen-doctor -o`; если HDR сейчас выключен, включает его перед запуском и возвращает SDR в обработчике `EXIT`/`INT`/`TERM`.
8. **Скрытый бенчмаркинг времени кадра (`BENCH=1`):** запускает MangoHud в скрытом CSV-режиме (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), по завершении игры разбирает frametime, дописывает `Avg FPS`, `1% Low FPS` и `P99 (ms)` в `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` и удаляет временные CSV-файлы.
9. **Автовосстановление в безопасный режим при быстром сбое:** если игра Proton/Windows завершается с ненулевым кодом быстрее чем за `20s` (настраивается через `SAP_CRASH_THRESHOLD_SEC`), пока активны экспериментальные флаги Wayland или DX12 (`USE_XWAYLAND=0` или `USE_SAFEDX12=0`), записывает `crash_hint` в `last-<APPID>.log` и `last-launch.log`, а при активном GUI предлагает сохранить `USE_XWAYLAND=1` + `USE_SAFEDX12=1` для следующего запуска.
10. **Планировщик и жизненный цикл сети:** выполняет запуск по цепочке `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (только если `ananicy-cpp.service` неактивен) -> прямой запуск, с опциональным `PRIME=1` (`prime-run`). При `USE_NET_OPT=1` утилита `steam-net-boost` запускает `on`/`off` с подсчётом ссылок и блокировкой `flock`, сохраняя статическую корневую дисциплину CAKE и иерархии HTB + листовой CAKE.

---

## Единый центр управления (`steam-auto-ui`)

Запускайте `steam-auto-ui` из меню приложений рабочего стола, командой `steam-auto-run --ui` или напрямую:

```bash
steam-auto-ui                 # Автоопределение Qt6 GUI (PyQt6/PySide6) или curses TUI
steam-auto-ui --gui           # Принудительный запуск нативного окна Qt6 GUI
steam-auto-ui --tui           # Принудительный запуск curses TUI из stdlib (работает по SSH)
steam-auto-ui --lang fi       # Запуск с явным выбором языка интерфейса (напр., --lang ru; 27 языков)
steam-auto-ui --check         # Автономная самодиагностика (выводит JSON-диагностику)
```

`steam-auto-ui` автоматически определяет системную локаль из `LC_ALL` / `LC_MESSAGES` / `LANG` и предоставляет выпадающий список выбора языка в Qt6 GUI (а также горячую клавишу `L` в `curses` TUI) для мгновенного переключения между всеми 27 языками без перезапуска.

### Пять синхронизированных разделов

1. **Игры и профили (Games & Profiles):** фильтруемая таблица игр Steam и записей Non-Steam `shortcuts.vdf` только для чтения (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), бейдж SDK апскейлера (`AUTO_UPSCALER_INFO`), проверка взаимных исключений в реальном времени для всех 10 переключателей профиля + `VRR_CAP`, предпросмотр `Dry-Run Preview`, кнопка перехода к `Benchmarks` и `Reset Profile`.
2. **Система и телеметрия (System & Telemetry):** неблокирующий вывод в реальном времени результатов `steam-auto-run --doctor`, статуса `scxctl get` / `sched_ext`, версий установленного стека (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), объёма кэша шейдеров (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), предупреждений о даунгрейде git/AUR из `/var/log/pacman.log`, VRAM/загрузки/температуры GPU, пропускной способности и `av_delay` из `tc -s qdisc` для LAN (`10:`) и WAN (`20:`/root), а также `vr-mode status`.
3. **Синхронизация библиотеки (Library Sync):** индикатор запущенного процесса Steam и запуск в один клик `--report`, `--sanitize --dry-run`, `--sanitize` (блокируется, пока Steam запущен) и `--migrate-cachy-run`.
4. **Логи и восстановление (Logs & Recovery):** просмотр `last-launch.log` и `last-<APPID>.log`, анализ предупреждений `crash_hint` и применение безопасного режима Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) в один клик.
5. **Бенчмарки (Benchmarks):** фильтруемая сравнительная таблица замеров времени кадра `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Оркестрация VR (`vr-run`)

В Steam откройте **Свойства > Общие > Параметры запуска** для VR-игр и укажите:

```text
vr-run %command%
```

- Очищает унаследованные flatscreen-переопределения (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Автоматически выбирает дискретную видеокарту с наибольшим объёмом VRAM через `MESA_VK_DEVICE_SELECT` и задаёт `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` для GPU AMD.
- Динамически определяет пути OpenXR/OpenVR для WiVRn и xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) и настраивает `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` и `LD_LIBRARY_PATH`, не перезаписывая явно заданные пользователем переменные.
- Ведёт подсчёт активных сессий для `vr-mode on` / `vr-mode off` в `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (с `flock`), если установлен `vr-mode` (`VR_AUTO_MODE=0` отключает это поведение).
- Использует ту же цепочку планировщиков с учётом `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> прямой `exec`).
- Посмотреть итоговые переменные окружения можно в любой момент командой `vr-run --dry-run`.

`steam-auto-run` автоматически пропускает SteamVR (`250820`) и запуски с `-vr`/`--vr`, а `steam-auto-sync` автоматически назначает и сохраняет `vr-run %command%` для VR-игр.

---

## Синхронизация библиотеки Steam (`steam-auto-sync`)

Полностью закройте Steam перед записью изменений в `localconfig.vdf`:

```bash
steam-auto-sync --report              # Аудит библиотеки и shortcuts.vdf в режиме «только чтение»
steam-auto-sync --print-library-paths # Показать все обнаруженные библиотеки Steam
steam-auto-sync --dry-run             # Предпросмотр изменений
steam-auto-sync                       # Прописать steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Предпросмотр очистки устаревших флагов
steam-auto-sync --sanitize            # Очистить лишние/устаревшие флаги (алиас: --clean)
steam-auto-sync --migrate-cachy-run   # Мигрировать старые профили cachy-run
steam-auto-sync --remove              # Удалить обёртку steam-auto-run
```

- Резервные копии `localconfig.vdf.bak.*` с отметкой времени автоматически очищаются с учётом `--keep-backups N` (по умолчанию `10`; `0` сохраняет все).
- Чтобы исключить конкретные AppID, перечислите их (по одному в строке, поддерживаются комментарии `#`) в `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Наблюдатель systemd для автосинхронизации (`./install.sh --with-auto-sync` или `steam-auto-sync --install-systemd`) запускает `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` при изменении манифестов Steam.

---

## Справочник CLI и профилей

### Команды

| Назначение | Команда |
| --- | --- |
| Аудит готовности системы | `steam-auto-run --doctor` (алиас `--check-system`) |
| Запуск центра управления (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` или `steam-auto-run --ui` |
| Инспекция игры (читаемый формат) | `steam-auto-run --inspect APPID` |
| Инспекция игры (JSON) | `steam-auto-detect --inspect --json APPID` |
| Интерактивная перенастройка профиля | `steam-auto-run --configure APPID` |
| Предпросмотр итогового окружения запуска | `steam-auto-run --dry-run APPID` |
| Сброс сохранённого профиля | `steam-auto-run --reset APPID` |
| Список сохранённых профилей | `steam-auto-run --list-profiles` |
| Показать последний лог запуска | `steam-auto-run --last-log [APPID]` |
| Предпросмотр VR-окружения запуска | `vr-run --dry-run` |
| Проверка сетевого помощника (только чтение) | `steam-net-boost status [IFACE]` |

### Ключи `.env`-профилей и переопределения переменных окружения

Файлы профилей хранятся в `~/.config/steam-auto-profiler/profiles/<APPID>.env` и принимают строго разрешённый формат `KEY=VALUE` (подстановки команд оболочки и неизвестные ключи безопасно игнорируются):

| Ключ `.env` | Переменная окружения | Действие |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Принудительно использовать XWayland вместо нативного Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Отключить обновление до FSR 4 на уровне драйвера (по умолчанию `1`) |
| `USE_MLFG=1` | `MLFG=1` | Включить генерацию кадров (отключает Anti-Lag, низкую задержку и лимиты VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Включить мост OptiScaler (принудительно отключён для `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Включить резкость vkBasalt (отключается при активных FSR 4 или OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Исключить экспериментальные флаги `VKD3D_CONFIG` и токен `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Активировать сетевой QoS на время сессии через `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Предпочитать нативный SDL / эмуляцию Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Сохранить `LD_PRELOAD` для оверлея Steam |
| `USE_CEF_FIX=1` | `CEF=1` | Добавить `--in-process-gpu` для лаунчеров на базе CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Отключить NTSync для старых игр |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Отключить декорации оконного менеджера |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Пользовательский лимит кадров DXVK/VKD3D (`0` отключает ограничение) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Применить запас `-6%` от частоты обновления монитора (напр., `225 FPS` на 240 Гц) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Разрешить перехват системных горячих клавиш в Wine Wayland (по умолчанию `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Автоматически включать HDR в KDE Plasma 6 при запуске и возвращать SDR при выходе |
| — | `BENCH=1`, `BENCH_DURATION=60` | Запустить скрытый CSV-бенчмарк MangoHud и сохранить сводку в JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Скрыть или принудительно открыть предзапусковой чек-лист `kdialog`/`zenity` |
| — | `FSR_HUD=1` | Экспортировать переменные индикаторов HUD для FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Добавить `-vulkan` / обернуть запуск через `prime-run` |
| — | `GAMEID=umu-<appid>` | Разрешить AppID для UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus и UMU

- **Lutris:** включите расширенные настройки, выберите `proton-cachyos-slr` (или вашу сборку Proton), отключите Lutris runtime, включите приоритет системных библиотек и укажите `steam-auto-run` в качестве префикса команды.
- **Heroic / Faugus:** выберите `proton-cachyos-slr` и добавьте `steam-auto-run` как обёртку / префикс команды.
- **UMU / Protonfixes:** при необходимости экспортируйте `PROTON_VERB=waitforexitandrun` и `GAMEID=umu-<appid>`.

---

## Устранение неполадок

- **Быстрый вылет на Wayland или DX12:** откройте **Logs & Recovery** в `steam-auto-ui` (или выполните `steam-auto-run --last-log APPID`) и примените Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), либо запустите `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Игры с античитом не запускаются:** используйте `proton-cachyos-slr` (Steam Linux Runtime) и выполните `steam-auto-run --doctor`, чтобы проверить EAC v2, `/dev/ntsync` и `vm.max_map_count`.
- **Steam сбрасывает параметры запуска:** полностью закройте Steam перед выполнением `steam-auto-sync` или `steam-auto-sync --sanitize`.
- **Неверный или отсутствующий лимит VRR:** задайте `VRR_CAP=<fps>` явно, `VRR_CAP=0` для отключения или `VRR_MINUS_MARGIN=1` для запаса `-6%`. В Gamescope лимиты DXVK/VKD3D экспортируются только при явно заданном `VRR_CAP`.
- **Проверка сетевого QoS:** выполните `steam-net-boost status` (без прав root, только чтение). Установите системный помощник командой `./install.sh --with-net-boost`, если нужен автоматический QoS для сессий.

---

## Новое в v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 и Steam Controller 2026)

- **Флаги Mesa 27.0 / RDNA 4:** `TRANSFER_QUEUE=1` (дедуплицированный `RADV_PERFTEST=sam,transfer_queue` на RDNA 3/4), `NATIVE_ANTILAG=1` (нативный `VK_AMD_anti_lag` без устаревшего слоя), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, блокируется в античите и MLFG) и `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Режим Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** экспериментальный стек для игр без античита с дедупликацией RADV-токенов, `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1` и `WAYLANDDRV_RAWINPUT=1` (только в нативном Wayland вне Gamescope).
- **Защита Hunt: Showdown 1896 (`AppID 594650`):** автоматически включает `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0` и `USE_NET_OPT=1`; `steam-auto-run --doctor` и `steam-auto-ui` проверяют `config/config.vdf` (`CompatToolMapping`) и рекомендуют официальный `Proton 11.0-2` или `Proton Hotfix`.
- **Steam Controller 2026 (`Triton`/`Proteus`) и Wireless Steam Puck (`28de:{1302,1304,1005,1007}`):**
  - 4 режима маршрутизации (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`, доступны в `steam-auto-ui` и клавишей `c` в TUI): `auto` выбирает `wayland-hdr` в Wayland или `xwayland` в X11.
  - `wayland-hdr` сохраняет нативный `winewayland.drv` + HDR10 (`USE_XWAYLAND=0`, `PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`) без лишнего `LD_PRELOAD`, экспортирует `PROTON_USE_SDL=0`, `PROTON_PREFER_SDL=0`, `PROTON_NO_STEAMINPUT=0` (без токена `sdlinput`), автоматически применяет `steam://forceinputappid/<APPID>` с фоновым отслеживанием переподключений через `udevadm` и сбрасывает раскладку (`steam://forceinputappid/0`) при выходе.
  - Для ручного обновления раскладки используйте `steam-auto-run --reapply-input <APPID|0>`, а для установки udev-правил (`/etc/udev/rules.d/61-steam-controller-2026.rules`) — `./install.sh --with-steam-controller`.

---

См. также [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) (внутреннее устройство) и [i18n Index](../README.md) для всех 27 локализованных руководств.
