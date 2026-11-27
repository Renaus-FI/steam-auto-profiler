# Кіраўніцтва карыстальніка Steam Auto-Profiler

> Арыгінальная дакументацыя: [English User Guide](../../USER_GUIDE.md) · Усе мовы: [i18n Index](../README.md)

Гэтае кіраўніцтва ахоплівае поўную ўстаноўку, аркестрацыю запуску плоскіх (flatscreen) і VR-гульняў, адзіны цэнтр кіравання `steam-auto-ui`, сінхранізацыю бібліятэкі Steam, бенчмаркінг і вырашэнне праблем для **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler — гэта лёгкі запускальнік і цэнтр кіравання на Bash/Python для Linux, які аналізуе Steam AppID (або старонняе спасыланне Non-Steam), прымяняе кантэкстна-залежны профіль са строгімі ахоўнымі абмежаваннямі для драйвераў, апскейлераў і антычытаў і запускае існуючую каманду гульні. Ён ніколі не пастаўляе і не ўкараняе староннія асяроддзі выканання Proton.

---

## Патрабаванні

- Сесія працоўнага стала Linux (KDE Plasma 6 / Wayland, GNOME, wlroots або X11), Bash 5+, Python 3.10+, Steam і стандартныя базавыя ўтыліты.
- Апцыянальны натыўны графічны інтэрфейс цэнтра кіравання: `PyQt6` або `PySide6` (пры адсутнасці аўтаматычна пераключаецца на TUI на базе стандартнай бібліятэкі `curses` без знешніх залежнасцей).
- Апцыянальныя дыялогі перадзапусковага чэк-ліста: `kdialog` або `zenity`.
- Апцыянальны схаваны бенчмаркінг часу кадра (frametime): `mangohud`.
- Апцыянальны сеткавы памочнік для гульнявых сесій: `tc`, `ip` і `ethtool` (`sudo` патрэбны толькі падчас устаноўкі са сцягам `--with-net-boost`).

---

## Устаноўка і абнаўленні

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` капіруе ўсе шэсць выконваемых файлаў (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` і `steam-auto-ui`) у `~/.local/bin`, усталёўвае ярлык працоўнага стала (`~/.local/share/applications/steam-auto-profiler.desktop`), стварае `~/.config/steam-auto-profiler/profiles` і дадае стандартныя прэсеты vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Пераканайцеся, што `~/.local/bin` ёсць у `PATH`.

Апцыянальныя сцягі ўсталёўшчыка можна камбінаваць:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: усталёўвае `/usr/local/bin/steam-net-boost` (а таксама сістэмныя копіі іншых скрыптоў) і вузкаабмежаванае правіла `sudoers` без пароля для `steam-net-boost`.
- `--compat-cachy-run`: захоўвае існуючы `/usr/local/bin/cachy-run` як `/usr/local/bin/cachy-run.bak` (калі гэта яшчэ не абгортка Steam Auto-Profiler) і ўсталёўвае перанакіравальную абгортку на `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): усталёўвае і ўключае карыстальніцкі юніт systemd `steam-auto-profiler-sync.path` і адпаведны oneshot-сэрвіс для ўсіх знойдзеных бібліятэк Steam.
- `--uninstall`: выдаляе ўсталяваныя бінарнікі, ярлык працоўнага стала, апцыянальны сеткавы памочнік і правіла `sudoers`, абгортку сумяшчальнасці і карыстальніцкія юніты systemd для аўтасінхранізацыі.

Каб абнавіць ужо кланаваны рэпазіторый:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Праверце гатоўнасць сістэмы перад сінхранізацыяй гульняў:

```bash
steam-auto-run --doctor
```

---

## Поўны канвеер запуску

1. **Вызначэнне AppID:** правярае `SteamAppId`, `STEAM_COMPAT_APP_ID`, затым `GAMEID` (выдаляючы прэфікс `umu-` для Lutris/Heroic/UMU).
2. **Пошук у бібліятэках і ярлыках:** `steam-auto-detect` скануе каранёвыя каталогі Steam і дадатковыя бібліятэкі з `libraryfolders.vdf`, чытае `appmanifest_<APPID>.acf` або ў рэжыме «толькі чытанне» звяртаецца да бінарнага `userdata/*/config/shortcuts.vdf`, пасля чаго выконвае аднапраходны `find` глыбінёй да 10 узроўняў (выключаючы `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Пяціўзроўневы прыярытэт класіфікацыі:**
   - **1. `competitive-anticheat`:** вядомы спаборніцкі AppID або выяўленае асяроддзе антычыта (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE і інш.). Адключае OptiScaler, MLFG, vkBasalt і асінхронны DXVK; уключае рэжым нізкай затрымкі і сеткавы QoS для сесіі.
   - **2. `vr`:** знойдзены `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` або сцягі ярлыка `vr-run`/`-vr`. Экспартуе `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** модульны FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Уключае абнаўленне да FSR 4 на ўзроўні драйвера (`PROTON_FSR4_UPGRADE=1` або `PROTON_FSR4_RDNA3_UPGRADE=1` на AMD RDNA 3).
   - **4. `legacy-upscaler`:** састарэлыя DLL для DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) або FSR 2/3.0. Задае `AUTO_OPTISCALER=1` і запаўняе падказку `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** бяспечны профіль з натыўным Wine Wayland і VRR з нізкай затрымкай.
4. **Абмежаванне частаты кадраў пад VRR:** яўнае значэнне `VRR_CAP=<fps>` заўсёды мае найвышэйшы прыярытэт (`VRR_CAP=0` адключае абмежаванне). У іншых выпадках актыўная частата абнаўлення дысплея вызначаецца праз `kscreen-doctor` (актыўны рэжым `*` у KDE Plasma 6 або стары вывад `Hz`), `wlr-randr` ці `xrandr` і па змаўчанні прымяняецца 1:1 (`240 FPS` на 240 Гц). Уключыце `VRR_MINUS_MARGIN=1` для апцыянальнага запасу VRR `-6%` (`hz * 94 / 100`, напрыклад `225 FPS` на 240 Гц). У сесіях Gamescope ліміты DXVK/VKD3D не задаюцца, калі `VRR_CAP` не ўказаны яўна.
5. **Абарона ад канфліктных параметраў (узаемнае выключэнне):**
   - **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` прымусова прымяняецца заўсёды, калі актыўныя `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` або `USE_OPTISCALER=1` (прадухіляе падвойнае павышэнне рэзкасці і кліпінг HDR10).
   - **MLFG + Low-Latency / ліміты VRR:** `MLFG=1` (`USE_MLFG=1`) экспартуе `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, скідае `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` і `DXVK_FRAME_PACE`, а на AMD RDNA 3 экспартуе `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. Калі `USE_MLFG=0` і абмежаванне VRR актыўнае, экспартуецца `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Сучасны DX12 + Safe DX12:** экспартуе `PROTON_NATIVE_AGS=1` на AMD і `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` пры `USE_SAFEDX12=0` (акуратна прапускаецца пры `SAFEDX12=1`).
6. **Супастаўленне compat-токенаў:** кіраваныя функцыі дадаюцца без перазапісу існуючых карыстальніцкіх значэнняў адразу ў `PROTON_ADD_CONFIG` і `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Аўтапераключэнне HDR у KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** калі ўключана па-за Gamescope разам з `DXVK_HDR=1` (або `USE_HDR=1`), правярае асноўны актыўны экран праз `kscreen-doctor -o`; калі HDR зараз выключаны, уключае яго перад запускам і вяртае SDR у апрацоўшчыку `EXIT`/`INT`/`TERM`.
8. **Схаваны бенчмаркінг часу кадра (`BENCH=1`):** запускае MangoHud у схаваным CSV-рэжыме (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), пасля выхаду разбірае frametime, дадае `Avg FPS`, `1% Low FPS` і `P99 (ms)` у `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` і выдаляе часовыя CSV-файлы.
9. **Аўтааднаўленне ў бяспечны рэжым пры хуткім збоі:** калі гульня Proton/Windows завяршаецца з ненулявым кодам менш чым за `20s` (наладжваецца праз `SAP_CRASH_THRESHOLD_SEC`), пакуль актыўныя эксперыментальныя сцягі Wayland або DX12 (`USE_XWAYLAND=0` або `USE_SAFEDX12=0`), запісвае `crash_hint` у `last-<APPID>.log` і `last-launch.log`, а пры актыўным GUI прапануе захаваць `USE_XWAYLAND=1` + `USE_SAFEDX12=1` для наступнага запуску.
10. **Планіроўшчык і жыццёвы цыкл сеткі:** запускае па ланцужку `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (толькі калі `ananicy-cpp.service` неактыўны) -> прамы запуск, з апцыянальным `PRIME=1` (`prime-run`). Пры `USE_NET_OPT=1` утыліта `steam-net-boost` выконвае `on`/`off` з падлікам спасылак і `flock`, захоўваючы статычны каранёвы CAKE і іерархіі HTB + ліставы CAKE.

---

## Адзіны цэнтр кіравання (`steam-auto-ui`)

Запускайце `steam-auto-ui` з меню праграм працоўнага стала, праз `steam-auto-run --ui` або напрамую:

```bash
steam-auto-ui                 # Аўтавызначэнне Qt6 GUI (PyQt6/PySide6) або curses TUI
steam-auto-ui --gui           # Прымусова адкрыць натыўнае акно Qt6 GUI
steam-auto-ui --tui           # Прымусова запусціць curses TUI са stdlib (працуе праз SSH)
steam-auto-ui --lang fi       # Запуск з яўным выбарам мовы інтэрфейсу (напр., --lang be; 27 моў)
steam-auto-ui --check         # Аўтаномная самаправерка (выводзіць JSON-дыягностыку)
```

`steam-auto-ui` аўтаматычна вызначае сістэмную лакаль з `LC_ALL` / `LC_MESSAGES` / `LANG` і прадастаўляе выпадаючы спіс выбару мовы ў Qt6 GUI (і гарачую клавішу `L` у `curses` TUI) для імгненнага пераключэння паміж усімі 27 мовамі без перазапуску.

### Пяць сінхранізаваных раздзелаў

1. **Гульні і профілі (Games & Profiles):** фільтраваная табліца гульняў Steam і запісаў Non-Steam `shortcuts.vdf` толькі для чытання (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), бэйдж SDK апскейлера (`AUTO_UPSCALER_INFO`), праверка ўзаемных выключэнняў у рэальным часе для ўсіх 10 пераключальнікаў профілю + `VRR_CAP`, папярэдні прагляд `Dry-Run Preview`, кнопка пераходу да `Benchmarks` і `Reset Profile`.
2. **Сістэма і тэлеметрыя (System & Telemetry):** неблакіруючы вывад у рэальным часе вынікаў `steam-auto-run --doctor`, стану `scxctl get` / `sched_ext`, версій усталяванага стэка (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), выкарыстання кэша шэйдараў (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), папярэджанняў пра даўнгрэйд git/AUR з `/var/log/pacman.log`, VRAM/загрузкі/тэмпературы GPU, прапускной здольнасці і `av_delay` з `tc -s qdisc` для LAN (`10:`) супраць WAN (`20:`/root), а таксама `vr-mode status`.
3. **Сінхранізацыя бібліятэкі (Library Sync):** жывы банер стану запушчанага Steam і запуск у адзін клік `--report`, `--sanitize --dry-run`, `--sanitize` (блакіруецца, пакуль Steam працуе) і `--migrate-cachy-run`.
4. **Логі і аднаўленне (Logs & Recovery):** прагляд `last-launch.log` і `last-<APPID>.log`, аналіз папярэджанняў `crash_hint` і прымяненне бяспечнага рэжыму Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) у адзін клік.
5. **Бенчмаркі (Benchmarks):** фільтраваная параўнальная табліца замераў часу кадра `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Аркестрацыя VR (`vr-run`)

У Steam адкрыйце **Уласцівасці > Агульныя > Параметры запуску** для VR-гульняў і задайце:

```text
vr-run %command%
```

- Ачышчае ўспадкаваныя flatscreen-перавызначэнні (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Аўтаматычна выбірае дыскрэтную відэакарту з найбольшым аб'ёмам VRAM праз `MESA_VK_DEVICE_SELECT` і задае `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` на GPU AMD.
- Дынамічна вызначае шляхі OpenXR/OpenVR для WiVRn і xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) і наладжвае `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` і `LD_LIBRARY_PATH`, не перазапісваючы яўныя перавызначэнні карыстальніка.
- Вядзе падлік спасылак для `vr-mode on` / `vr-mode off` у `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (з `flock`), калі ўсталяваны `vr-mode` (`VR_AUTO_MODE=0` адключае гэта).
- Працуе праз той жа ланцужок планіроўшчыкаў з улікам `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> прамы `exec`).
- Праглядзець выніковыя зменныя можна ў любы момант камандай `vr-run --dry-run`.

`steam-auto-run` аўтаматычна абыходзіць SteamVR (`250820`) і запускі з `-vr`/`--vr`, а `steam-auto-sync` аўтаматычна прызначае і захоўвае `vr-run %command%` для VR-гульняў.

---

## Сінхранізацыя бібліятэкі Steam (`steam-auto-sync`)

Цалкам закрыйце Steam перад запісам у `localconfig.vdf`:

```bash
steam-auto-sync --report              # Аўдыт бібліятэкі і shortcuts.vdf у рэжыме «толькі чытанне»
steam-auto-sync --print-library-paths # Паказаць усе знойдзеныя бібліятэкі Steam
steam-auto-sync --dry-run             # Папярэдні прагляд змен
steam-auto-sync                       # Дадаць steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Папярэдні прагляд ачысткі старых сцягоў
steam-auto-sync --sanitize            # Ачысціць лішнія/састарэлыя сцягі (аліяс: --clean)
steam-auto-sync --migrate-cachy-run   # Міграваць старыя профілі cachy-run
steam-auto-sync --remove              # Выдаліць абгортку steam-auto-run
```

- Рэзервовыя копіі `localconfig.vdf.bak.*` з пазнакай часу ачышчаюцца аўтаматычна параметрам `--keep-backups N` (па змаўчанні `10`; `0` захоўвае ўсе).
- Каб выключыць пэўныя AppID, пералічыце іх (па адным у радку, дазволены каментарыі `#`) у `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Назіральнік systemd для аўтасінхранізацыі (`./install.sh --with-auto-sync` або `steam-auto-sync --install-systemd`) запускае `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`, калі змяняюцца маніфесты Steam.

---

## Даведнік CLI і профіляў

### Каманды

| Прызначэнне | Каманда |
| --- | --- |
| Аўдыт гатоўнасці сістэмы | `steam-auto-run --doctor` (аліяс `--check-system`) |
| Запуск цэнтра кіравання (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` або `steam-auto-run --ui` |
| Інспекцыя гульні (чытэльны фармат) | `steam-auto-run --inspect APPID` |
| Інспекцыя гульні (JSON) | `steam-auto-detect --inspect --json APPID` |
| Інтэрактыўная перанастройка профілю | `steam-auto-run --configure APPID` |
| Папярэдні прагляд асяроддзя запуску | `steam-auto-run --dry-run APPID` |
| Скід захаванага профілю | `steam-auto-run --reset APPID` |
| Спіс захаваных профіляў | `steam-auto-run --list-profiles` |
| Паказаць апошні лог запуску | `steam-auto-run --last-log [APPID]` |
| Папярэдні прагляд VR-асяроддзя | `vr-run --dry-run` |
| Праверка сеткавага памочніка (толькі чытанне) | `steam-net-boost status [IFACE]` |

### Ключы `.env`-профіляў і перавызначэнні зменных асяроддзя

Файлы профіляў захоўваюцца ў `~/.config/steam-auto-profiler/profiles/<APPID>.env` і прымаюць дазволены фармат `KEY=VALUE` (падстаноўкі каманд абалонкі і невядомыя ключы бяспечна ігнаруюцца):

| Ключ `.env` | Зменная асяроддзя | Дзеянне |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Прымусова выкарыстоўваць XWayland замест натыўнага Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Адключыць абнаўленне да FSR 4 на ўзроўні драйвера (па змаўчанні `1`) |
| `USE_MLFG=1` | `MLFG=1` | Уключыць генерацыю кадраў (адключае Anti-Lag, нізкую затрымку і ліміты VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Уключыць мост OptiScaler (прымусова адключаны для `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Уключыць рэзкасць vkBasalt (адключаецца пры актыўных FSR 4 або OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Прапусціць эксперыментальныя сцягі `VKD3D_CONFIG` і токен `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Актываваць сеткавы QoS на час сесіі праз `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Аддаць перавагу натыўнаму SDL / эмуляцыі Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Захаваць `LD_PRELOAD` для аверлея Steam |
| `USE_CEF_FIX=1` | `CEF=1` | Дадаць `--in-process-gpu` для лаўнчараў на базе CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Адключыць NTSync для старых гульняў |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Адключыць дэкарацыі аконнага менеджара |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Карыстальніцкі ліміт кадраў DXVK/VKD3D (`0` адключае абмежаванне) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Прымяніць запас `-6%` ад частаты абнаўлення манітора (напр., `225 FPS` на 240 Гц) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Дазволіць перахоп гарачых клавіш у Wine Wayland (па змаўчанні `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Аўтаматычна ўключаць HDR у KDE Plasma 6 пры запуску і вяртаць SDR пры выхадзе |
| — | `BENCH=1`, `BENCH_DURATION=60` | Запусціць схаваны CSV-бенчмарк MangoHud і захаваць вынік у JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Схаваць або прымусова адкрыць перадзапусковы чэк-ліст `kdialog`/`zenity` |
| — | `FSR_HUD=1` | Экспартаваць зменныя індыкатараў HUD для FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Дадаць `-vulkan` / абгарнуць запуск праз `prime-run` |
| — | `GAMEID=umu-<appid>` | Вызначыць AppID для UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus і UMU

- **Lutris:** уключыце пашыраныя налады, выберыце `proton-cachyos-slr` (або вашу зборку Proton), адключыце Lutris runtime, уключыце прыярытэт сістэмных бібліятэк і задайце `steam-auto-run` у якасці прэфікса каманды.
- **Heroic / Faugus:** выберыце `proton-cachyos-slr` і дадайце `steam-auto-run` як абгортку / прэфікс каманды.
- **UMU / Protonfixes:** пры неабходнасці экспартуйце `PROTON_VERB=waitforexitandrun` і `GAMEID=umu-<appid>`.

---

## Вырашэнне праблем

- **Хуткі вылет на Wayland або DX12:** адкрыйце **Logs & Recovery** у `steam-auto-ui` (або выканайце `steam-auto-run --last-log APPID`) і прымяніце Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), альбо запусціце `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Гульні з антычытам не запускаюцца:** выкарыстоўвайце `proton-cachyos-slr` (Steam Linux Runtime) і выканайце `steam-auto-run --doctor`, каб праверыць EAC v2, `/dev/ntsync` і `vm.max_map_count`.
- **Steam скідае параметры запуску:** цалкам закрыйце Steam перад выкананнем `steam-auto-sync` або `steam-auto-sync --sanitize`.
- **Няправільнае або адсутнае абмежаванне VRR:** задайце `VRR_CAP=<fps>` яўна, `VRR_CAP=0` для адключэння або `VRR_MINUS_MARGIN=1` для запасу `-6%`. У Gamescope ліміты DXVK/VKD3D экспартуюцца толькі пры яўна зададзеным `VRR_CAP`.
- **Праверка сеткавага QoS:** выканайце `steam-net-boost status` (без правоў root, толькі чытанне). Усталюйце сістэмны памочнік камандай `./install.sh --with-net-boost`, калі патрэбны аўтаматычны QoS для сесій.

---

## Новае ў v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 і Steam Controller 2026)

- **Сцягі Mesa 27.0 / RDNA 4:** `TRANSFER_QUEUE=1` (`RADV_PERFTEST=sam,transfer_queue` без дублікатаў на RDNA 3/4), `NATIVE_ANTILAG=1` (натыўны `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, блакіруецца ў антычыце і MLFG) і `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Рэжым Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** эксперыментальны стэк без антычыту з `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1` і `WAYLANDDRV_RAWINPUT=1` (толькі ў натыўным Wayland па-за Gamescope).
- **Абарона Hunt: Showdown 1896 (`AppID 594650`):** прымусова ўсталёўвае `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, `USE_NET_OPT=1`; `--doctor` і `steam-auto-ui` правяраюць `config.vdf` на `Proton 11.0-2` / `Proton Hotfix`.
- **Steam Controller 2026 / Wireless Puck (`28de:{1302,1304,1005,1007}`):** 4 рэжымы (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` захоўвае Wayland + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`), запускае `steam://forceinputappid/<APPID>` з аўтаперападключэннем `udevadm` і скідае `steam://forceinputappid/0` пры выхадзе. Дадаткова: `steam-auto-run --reapply-input <APPID|0>` і `./install.sh --with-steam-controller`.

---

Гл. таксама [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) (унутраная архітэктура) і [i18n Index](../README.md) для ўсіх 27 лакалізаваных кіраўніцтваў.
