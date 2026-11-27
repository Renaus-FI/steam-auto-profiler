# Steam Auto-Profiler — Дастури корбар

> [English User Guide](../../USER_GUIDE.md) · [i18n Index](../README.md)

Ин дастур насби пурра, идоракунии оғози бозиҳои экрани муқаррарӣ (flatscreen) ва VR, Маркази идоракунии `steam-auto-ui`, ҳамоҳангсозии китобхона, санҷиши самаранокӣ (benchmarking) ва бартараф кардани мушкилотро барои **Steam Auto-Profiler v2.0** фаро мегирад.

Steam Auto-Profiler як оғозкунанда ва маркази идоракунии сабуки Bash/Python барои Linux мебошад, ки Steam AppID (ё миёнбури ғайри-Steam)-ро месанҷад, профили мувофиқи вазъро бо маҳдудиятҳои қатъии драйвер/миқёссоз (upscaler)/античит татбиқ мекунад ва фармони мавҷудаи бозиро иҷро менамояд. Он ҳеҷ гоҳ муҳити Proton-и тарафи сеюмро ворид ё ҳамроҳ намекунад.

---

## Талабот

- Сессияи мизи кории Linux (KDE Plasma 6 / Wayland, GNOME, wlroots ё X11), Bash 5+, Python 3.10+, Steam ва абзорҳои асосии система.
- Интерфейси графикии ихтиёрии Маркази идоракунӣ (GUI): `PyQt6` ё `PySide6` (дар сурати набудан ба таври худкор ба режими `curses` TUI-и китобхонаи стандартӣ бидуни вобастагиҳои иловагӣ мегузарад).
- Тирезаҳои ихтиёрии рӯйхати санҷиш пеш аз оғоз: `kdialog` ё `zenity`.
- Санҷиши ихтиёрии хомӯшонаи вақти кадр (frametime): `mangohud`.
- Ёрдамчии ихтиёрии шабакаи сессия: `tc`, `ip` ва `ethtool` (`sudo` танҳо ҳангоми насби `--with-net-boost` лозим аст).

---

## Насб ва навсозиҳо

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` ҳамаи шаш файли иҷрошавандаро (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` ва `steam-auto-ui`) ба `~/.local/bin` нусхабардорӣ мекунад, миёнбури мизи кориро (`~/.local/share/applications/steam-auto-profiler.desktop`) насб менамояд, ҷузвдони `~/.config/steam-auto-profiler/profiles`-ро месозад ва танзимоти пешфарзи vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`)-ро илова мекунад. Боварӣ ҳосил кунед, ки `~/.local/bin` дар `PATH` мавҷуд аст.

Парчамҳои ихтиёрии насбкунандаро якҷоя истифода бурдан мумкин аст:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: `/usr/local/bin/steam-net-boost` (ва нусхаҳои системавии скриптҳои дигар) инчунин қоидаи маҳдуди бепароли sudoers-ро барои `steam-net-boost` насб мекунад.
- `--compat-cachy-run`: `/usr/local/bin/cachy-run`-и мавҷударо ҳамчун `/usr/local/bin/cachy-run.bak` нигоҳ медорад (агар он аллакай гузаронандаи Steam Auto-Profiler набошад) ва shim-и равонакунандаро ба `steam-auto-run` насб мекунад.
- `--with-auto-sync` (`--enable-auto-sync`): нозири корбарии systemd `steam-auto-profiler-sync.path` ва хидмати якдафъаинаи мувофиқро барои ҳамаи китобхонаҳои ёфтшудаи Steam насб ва фаъол мекунад.
- `--uninstall`: файлҳои иҷрошавандаи насбшуда, миёнбури мизи корӣ, ёрдамчии ихтиёрии шабака/қоидаи sudoers, shim-и мувофиқат ва воҳидҳои корбарии systemd auto-sync-ро нест мекунад.

Барои навсозии нусхаи мавҷуда:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Пеш аз ҳамоҳангсозии бозиҳо омодагии системаро санҷед:

```bash
steam-auto-run --doctor
```

---

## Занҷираи пурраи оғозкунӣ

1. **Муайянкунии AppID:** Пайдарпай `SteamAppId`, `STEAM_COMPAT_APP_ID` ва сипас `GAMEID`-ро месанҷад (пешванди `umu-`-ро барои Lutris/Heroic/UMU тоза мекунад).
2. **Кашфи китобхона ва миёнбурҳо:** `steam-auto-detect` решаҳои Steam ва китобхонаҳои иловагиро дар `libraryfolders.vdf` меҷӯяд, `appmanifest_<APPID>.acf`-ро мехонад ё дар режими танҳо-хониш ба файли бинарии `userdata/*/config/shortcuts.vdf` муроҷиат мекунад; сипас як даври `find`-ро то умқи 10 сатҳ иҷро менамояд (бо сарфи назар кардани ҷузвдонҳои `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Афзалияти таснифи панҷсатҳа:**
   - **1. `competitive-anticheat`:** AppID-и маъруфи рақобатӣ ё модули античити ошкоршуда (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE ва ғ.). OptiScaler, MLFG, vkBasalt ва DXVK-и асинхрониро хомӯш мекунад; таъхири кам ва QoS-и шабакавии сессияро фаъол месозад.
   - **2. `vr`:** Ошкор шудани `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` ё парчамҳои миёнбури `vr-run`/`-vr`. `AUTO_IS_VR=1`-ро содир мекунад.
   - **3. `native-fsr4` / `native-fsr`:** FidelityFX SDK 3.1+ модулӣ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Навсозии сатҳи драйвери FSR 4-ро фаъол мекунад (`PROTON_FSR4_UPGRADE=1` ё `PROTON_FSR4_RDNA3_UPGRADE=1` дар AMD RDNA 3).
   - **4. `legacy-upscaler`:** Файлҳои кӯҳнаи DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) ё FSR 2/3.0 DLL. `AUTO_OPTISCALER=1`-ро қайд карда, маълумоти роҳнамои `AUTO_UPSCALER_INFO`-ро мегузорад.
   - **5. `standard`:** Профили бехатари аслии Wine Wayland + VRR бо таъхири кам.
4. **Маҳдудкунии басомади навсозии VRR:** Арзиши ошкоро гузошташудаи `VRR_CAP=<fps>` ҳамеша афзалият дорад (`VRR_CAP=0` маҳдудкуниро хомӯш мекунад). Дар акси ҳол басомади экрани фаъол тавассути `kscreen-doctor` (режими фаъоли `*` дар KDE Plasma 6 ё `Hz`-и анъанавӣ), `wlr-randr` ё `xrandr` санҷида шуда, ба таври пешфарз 1:1 татбиқ мегардад (`240 FPS` дар экрани 240 Гс). Барои захираи ихтиёрии бехатарии `-6%` VRR (`hz * 94 / 100`, мас. `225 FPS` дар 240 Гс) `VRR_MINUS_MARGIN=1`-ро фаъол созед. Дар сессияҳои Gamescope маҳдудиятҳои DXVK/VKD3D гузошта намешаванд, агар `VRR_CAP` ошкоро таъин нашуда бошад.
5. **Қоидаҳои муҳофизатии истиснои мутақобила:**
   - **FSR 4 / OptiScaler + vkBasalt:** Ҳар гоҳ `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` ё `USE_OPTISCALER=1` фаъол бошад, `ENABLE_VKBASALT=0` ҳатман таъин мешавад (аз тезкунии дукарата ва буридашавии HDR10 пешгирӣ мекунад).
   - **MLFG + Таъхири кам / Маҳдудиятҳои VRR:** `MLFG=1` (`USE_MLFG=1`) тағйирёбандаҳои `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`-ро содир мекунад, `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` ва `DXVK_FRAME_PACE`-ро пок мекунад ва дар AMD RDNA 3 `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`-ро содир менамояд. Вақте ки `USE_MLFG=0` аст ва маҳдудияти VRR фаъол мебошад, `DXVK_FRAME_PACE=low-latency-vrr` содир карда мешавад.
   - **DX12-и муосир + Safe DX12:** Дар AMD `PROTON_NATIVE_AGS=1` ва вақте `USE_SAFEDX12=0` аст `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`-ро содир мекунад (вақте `SAFEDX12=1` бошад, ба таври тоза партофта мешавад).
6. **Харитасозии токенҳои мувофиқат (compat-tokens):** Имкониятҳои идорашаванда бидуни нест кардани арзишҳои мавҷудаи корбар ба ҳар ду тағйирёбандаи `PROTON_ADD_CONFIG` ва `STEAM_COMPAT_CONFIG` илова мешаванд: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **KDE Plasma 6 HDR-и худкор (`AUTO_HDR_SWITCH=1`):** Ҳангоми фаъол будан берун аз Gamescope бо `DXVK_HDR=1` (ё `USE_HDR=1`), баромади асосии фаъолро тавассути `kscreen-doctor -o` месанҷад; агар HDR хомӯш бошад, пеш аз оғоз онро фаъол месозад ва ҳангоми баромад тавассути `EXIT`/`INT`/`TERM` trap режими SDR-ро барқарор мекунад.
8. **Санҷиши хомӯшонаи вақти кадр (`BENCH=1`):** MangoHud-ро дар режими пинҳонии CSV иҷро мекунад (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), ҳангоми баромад вақти кадрҳоро таҳлил мекунад, `Avg FPS`, `1% Low FPS` ва `P99 (ms)`-ро ба `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` илова мекунад ва файлҳои муваққатии CSV-ро нест месозад.
9. **Барқарорсозии худкори Режими бехатар (Safe Mode) ҳангоми шикасти зуд:** Агар бозии Proton/Windows бо коди ғайрисифрӣ дар камтар аз `20s` (танзимшаванда бо `SAP_CRASH_THRESHOLD_SEC`) ҳангоми фаъол будани парчамҳои таҷрибавии Wayland ё DX12 (`USE_XWAYLAND=0` ё `USE_SAFEDX12=0`) баста шавад, ба `last-<APPID>.log` ва `last-launch.log` қайди `crash_hint` менависад ва (ҳангоми фаъол будани GUI) барои оғози навбатӣ захира кардани `USE_XWAYLAND=1` + `USE_SAFEDX12=1`-ро пешниҳод мекунад.
10. **Давраи ҳаёти нақшасоз ва шабака:** Тавассути занҷираи `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (танҳо вақте ки `ananicy-cpp.service` фаъол нест) -> иҷрои мустақим кор мекунад, бо дастгирии ихтиёрии `PRIME=1` (`prime-run`). Агар `USE_NET_OPT=1` бошад, `steam-net-boost` бо ҳисоби истинодҳо ва қулфи `flock` режими `on`/`off`-ро иҷро мекунад, дар ҳоле ки иерархияҳои статикии root CAKE ва HTB + leaf CAKE-ро ҳифз менамояд.

---

## Маркази ягонаи идоракунӣ (`steam-auto-ui`)

`steam-auto-ui`-ро аз менюи барномаҳои мизи корӣ, тавассути `steam-auto-run --ui` ё мустақиман оғоз кунед:

```bash
steam-auto-ui                 # Ба таври худкор Qt6 GUI (PyQt6/PySide6) ё curses TUI-ро интихоб мекунад
steam-auto-ui --gui           # Маҷбуран кушодани тирезаи аслии Qt6 GUI
steam-auto-ui --tui           # Маҷбуран кушодани curses TUI-и китобхонаи стандартӣ (тавассути SSH кор мекунад)
steam-auto-ui --lang tg       # Оғоз бо забони муайяншудаи UI (27 забон дастгирӣ мешавад)
steam-auto-ui --check         # Иҷрои худсанҷиши беэкран (ташхиси JSON-ро чоп мекунад)
```

`steam-auto-ui` забони системаро аз `LC_ALL` / `LC_MESSAGES` / `LANG` ба таври худкор муайян мекунад ва дар Qt6 GUI рӯйхати зиндаи интихоби забон (ва тугмаи тезкори `L` дар `curses` TUI)-ро барои гузариш байни ҳамаи 27 забон бидуни бозоғозӣ фароҳам меорад.

### Панҷ намоиши ҳамоҳангшуда

1. **Games & Profiles:** Ҷадвали филтршавандаи бозиҳои Steam ва сабтҳои танҳо-хониши ғайри-Steam `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), нишони Upscaler SDK (`AUTO_UPSCALER_INFO`), санҷиши зиндаи истиснои мутақобила барои ҳамаи 10 калиди профил + `VRR_CAP`, `Dry-Run Preview`, тугмаи гузариш ба `Benchmarks` ва `Reset Profile`.
2. **System & Telemetry:** Намоиши зиндаи ғайрибандкунандаи `steam-auto-run --doctor`, вазъи `scxctl get` / `sched_ext`, версияҳои насбшудаи стек (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), истифодаи кэши шейдерҳо (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), огоҳиҳои пастшавии версияи git/AUR аз `/var/log/pacman.log`, VRAM/сарборӣ/ҳарорати GPU, суръати `tc -s qdisc` LAN (`10:`) бар зидди WAN (`20:`/root) ва `av_delay`, инчунин `vr-mode status`.
3. **Library Sync:** Баннери зиндаи муҳофизатии вазъи фаъоли Steam ва фармонҳои яккликаи `--report`, `--sanitize --dry-run`, `--sanitize` (ҳангоми фаъол будани Steam рад карда мешавад) ва `--migrate-cachy-run`.
4. **Logs & Recovery:** Журналҳои `last-launch.log` ва `last-<APPID>.log`-ро бинед, огоҳиҳои `crash_hint`-ро тафтиш кунед ва бо як клик Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`)-ро татбиқ намоед.
5. **Benchmarks:** Ҷадвали филтршавандаи муқоисавии паҳлӯ ба паҳлӯи санҷишҳои `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Идоракунии VR (`vr-run`)

Барои бозиҳои VR дар Steam дар бахши **Хосиятҳо > Умумӣ > Имконоти оғоз** инро ворид кунед:

```text
vr-run %command%
```

- Танзимоти меросии flatscreen-ро пок мекунад (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- GPU-и дискретии дорои баландтарин VRAM-ро тавассути `MESA_VK_DEVICE_SELECT` ба таври худкор интихоб мекунад ва дар кортҳои AMD `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`-ро таъин менамояд.
- Масирҳои OpenXR/OpenVR-и WiVRn ва xrizer-ро динамикӣ месанҷад (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) ва бидуни тағйир додани танзимоти ошкори корбар `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` ва `LD_LIBRARY_PATH`-ро танзим мекунад.
- Ҳангоми насб будани `vr-mode`, дар `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (бо `flock`) ҳисоби истинодҳои `vr-mode on` / `vr-mode off`-ро иҷро мекунад (`VR_AUTO_MODE=0` онро хомӯш мекунад).
- Тавассути ҳамон занҷираи нақшасози ба `ananicy-cpp` ҳассос кор мекунад (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> `exec`-и мустақим).
- Тағйирёбандаҳои ҳалшударо ҳар вақт бо `vr-run --dry-run` пешакӣ бинед.

`steam-auto-run` ба таври худкор SteamVR (`250820`) ва оғозҳои `-vr`/`--vr`-ро давр мезанад, ва `steam-auto-sync` барои бозиҳои VR `vr-run %command%`-ро ба таври худкор таъин ва нигоҳ медорад.

---

## Ҳамоҳангсозии китобхонаи Steam (`steam-auto-sync`)

Пеш аз навиштан ба `localconfig.vdf` Steam-ро пурра пӯшед:

```bash
steam-auto-sync --report              # Аудити танҳо-хониши китобхона + shortcuts.vdf
steam-auto-sync --print-library-paths # Намоиши ҳамаи китобхонаҳои ёфтшудаи Steam
steam-auto-sync --dry-run             # Пешнамоиши тағйирот
steam-auto-sync                       # Ворид кардани steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Пешнамоиши тозакунии парчамҳои кӯҳна
steam-auto-sync --sanitize            # Тоза кардани парчамҳои номураттаб/бесоҳиб (ҳаммаъно: --clean)
steam-auto-sync --migrate-cachy-run   # Кӯчонидани профилҳои кӯҳнаи cachy-run
steam-auto-sync --remove              # Бардоштани қабати steam-auto-run
```

- Нусхаҳои эҳтиётии бо тамғаи вақт `localconfig.vdf.bak.*` бо `--keep-backups N` ба таври худкор кам карда мешаванд (пешфарз `10`; `0` ҳамаро нигоҳ медорад).
- Барои истисно кардани AppID-ҳои муайян онҳоро (як дона дар ҳар сатр, шарҳҳои `#` иҷозат дода мешаванд) дар `~/.config/steam-auto-profiler/ignore_appids.txt` номбар кунед.
- Нозири systemd auto-sync (`./install.sh --with-auto-sync` ё `steam-auto-sync --install-systemd`) ҳангоми тағйир ёфтани манифестҳои Steam фармони `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`-ро иҷро мекунад.

---

## Маълумотномаи CLI ва профилҳо

### Фармонҳо

| Мақсад | Фармон |
| --- | --- |
| Санҷиши омодагии система | `steam-auto-run --doctor` (ҳаммаъно `--check-system`) |
| Оғози Маркази идоракунӣ (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` ё `steam-auto-run --ui` |
| Санҷиши бозӣ (хондашаванда) | `steam-auto-run --inspect APPID` |
| Санҷиши бозӣ (JSON) | `steam-auto-detect --inspect --json APPID` |
| Аз нав танзимкунии интерактивии профил | `steam-auto-run --configure APPID` |
| Пешнамоиши муҳити оғоз | `steam-auto-run --dry-run APPID` |
| Бозгардонии профили захирашуда | `steam-auto-run --reset APPID` |
| Рӯйхати профилҳои захирашуда | `steam-auto-run --list-profiles` |
| Намоиши журнали охирини оғоз | `steam-auto-run --last-log [APPID]` |
| Пешнамоиши муҳити оғози VR | `vr-run --dry-run` |
| Санҷиши ёрдамчии шабака (танҳо-хониш) | `steam-net-boost status [IFACE]` |

### Калидҳои профили `.env` ва ивазкунандаҳои муҳит

Файлҳои профил дар `~/.config/steam-auto-profiler/profiles/<APPID>.env` ҷойгиранд ва формати `KEY=VALUE`-ро аз рӯи рӯйхати иҷозатдодашуда қабул мекунанд (ивазкунии фармонҳои shell ва калидҳои номаълум бехатар сарфи назар карда мешаванд):

| Калиди `.env` | Ивазкунандаи муҳит | Таъсир |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Маҷбур кардани XWayland ба ҷои Wine Wayland-и аслӣ |
| `USE_FSR4=0` | `FSR4=0` | Хомӯш кардани навсозии сатҳи драйвери FSR 4 (пешфарз `1`) |
| `USE_MLFG=1` | `MLFG=1` | Фаъол кардани тавлиди кадрҳо (Anti-Lag, таъхири кам ва маҳдудиятҳои VRR-ро хомӯш мекунад) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Фаъол кардани пули OptiScaler (барои `competitive-anticheat` муҳофизатӣ хомӯш аст) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Фаъол кардани тезкунии vkBasalt (ҳангоми фаъол будани FSR 4 ё OptiScaler хомӯш мешавад) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Сарфи назар кардани парчамҳои таҷрибавии `VKD3D_CONFIG` ва токени `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Фаъол кардани QoS-и шабакавии сессия тавассути `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Бартарӣ додан ба эмулятсияи аслии SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Нигоҳ доштани `LD_PRELOAD`-и Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Илова кардани `--in-process-gpu` барои оғозкунандаҳои CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Хомӯш кардани NTSync барои бозиҳои кӯҳна |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Хомӯш кардани чорчӯбаҳои мудири тиреза |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Маҳдудияти фардии кадрҳои DXVK/VKD3D (`0` маҳдудкуниро хомӯш мекунад) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Татбиқи захираи `-6%` ба басомади монитор (мас. `225 FPS` дар 240 Гс) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Иҷозат додани боздошти миёнбурҳо дар Wine Wayland (пешфарз `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Фаъолсозии худкори KDE Plasma 6 HDR ҳангоми оғоз ва барқарорсозии SDR ҳангоми баромад |
| — | `BENCH=1`, `BENCH_DURATION=60` | Иҷрои санҷиши хомӯшонаи MangoHud CSV ва захираи хулосаи JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Пинҳон кардан ё маҷбуран кушодани рӯйхати санҷиши `kdialog`/`zenity` пеш аз оғоз |
| — | `FSR_HUD=1` | Содир кардани тағйирёбандаҳои нишондиҳандаи FSR/DLSS/MLFG HUD |
| — | `VULKAN=1` / `PRIME=1` | Илова кардани `-vulkan` / печонидан бо `prime-run` |
| — | `GAMEID=umu-<appid>` | Муайян кардани AppID-ҳои UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus ва UMU

- **Lutris:** Имконоти пешрафтаро фаъол кунед, `proton-cachyos-slr` (ё сохти Proton-и худро) интихоб кунед, Lutris runtime-ро хомӯш созед, ба китобхонаҳои системавӣ бартарӣ диҳед ва пешванди фармонро `steam-auto-run` гузоред.
- **Heroic / Faugus:** `proton-cachyos-slr`-ро интихоб кунед ва `steam-auto-run`-ро ҳамчун қабат/пешванди фармон илова намоед.
- **UMU / Protonfixes:** Ҳангоми зарурат `PROTON_VERB=waitforexitandrun` ва `GAMEID=umu-<appid>`-ро содир кунед.

---

## Бартараф кардани мушкилот

- **Шикасти зуд дар Wayland ё DX12:** Дар `steam-auto-ui` бахши **Logs & Recovery**-ро кушоед (ё `steam-auto-run --last-log APPID`-ро иҷро кунед) ва Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`)-ро татбиқ намоед, ё `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`-ро иҷро кунед.
- **Бозиҳои дорои античит оғоз намешаванд:** `proton-cachyos-slr` (Steam Linux Runtime)-ро истифода баред ва барои санҷиши EAC v2, `/dev/ntsync` ва `vm.max_map_count` фармони `steam-auto-run --doctor`-ро иҷро кунед.
- **Steam имконоти оғозро бармегардонад:** Пеш аз иҷрои `steam-auto-sync` ё `steam-auto-sync --sanitize` Steam-ро пурра пӯшед.
- **Маҳдудияти нодуруст ё набудаи VRR:** `VRR_CAP=<fps>`-ро ошкоро таъин кунед, `VRR_CAP=0` барои хомӯш кардан, ё `VRR_MINUS_MARGIN=1` барои захираи `-6%`. Дар Gamescope танҳо `VRR_CAP`-и ошкоро маҳдудиятҳои DXVK/VKD3D-ро содир мекунад.
- **Санҷиши QoS-и шабака:** `steam-net-boost status`-ро иҷро кунед (беимтиёз, танҳо-хониш). Агар QoS-и худкори сессия лозим бошад, ёрдамчии root-ро бо `./install.sh --with-net-boost` насб намоед.

Барои ҷузъиёти меъморӣ ба [ARCHITECTURE.md](../../ARCHITECTURE.md), барои дастури асосии англисӣ ба [English User Guide](../../USER_GUIDE.md) ва барои ҳамаи 27 дастури тарҷумашуда ба [i18n Index](../README.md) нигаред.
