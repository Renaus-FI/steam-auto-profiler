# Steam Auto-Profiler пайдаланушы нұсқаулығы

> Түпнұсқа құжаттама: [English User Guide](../../USER_GUIDE.md) · Барлық тілдер: [i18n Index](../README.md)

Бұл нұсқаулық **Steam Auto-Profiler v2.0** үшін толық орнатуды, кәдімгі (flatscreen) және VR ойындарын іске қосу оркестрациясын, `steam-auto-ui` бірыңғай басқару орталығын, Steam кітапханасын синхрондауды, бенчмаркингті және ақаулықтарды жоюды қамтиды.

Steam Auto-Profiler — Linux жүйесіне арналған жеңіл Bash/Python іске қосу құралы және басқару орталығы. Ол Steam AppID (немесе Non-Steam таңбашасын) тексереді, драйвер, апскейлер және античит шектеулерін қатаң сақтай отырып контекстке сай профиль қолданады және ойынның бастапқы командасын іске қосады. Ол ешқашан бөгде Proton ортасын бірге жеткізбейді немесе ендірмейді.

---

## Талаптар

- Linux жұмыс үстелі сессиясы (KDE Plasma 6 / Wayland, GNOME, wlroots немесе X11), Bash 5+, Python 3.10+, Steam және стандартты базалық утилиталар.
- Қосымша нативті басқару орталығының GUI интерфейсі: `PyQt6` немесе `PySide6` (болмаса, сыртқы тәуелділіктерсіз стандартты кітапханадағы `curses` TUI режиміне автоматты ауысады).
- Іске қосар алдындағы қосымша чек-лист диалогтары: `kdialog` немесе `zenity`.
- Кадр уақытын (frametime) жасырын бенчмаркингтен өткізуге арналған қосымша құрал: `mangohud`.
- Сессиялық желі көмекшісіне арналған қосымша құралдар: `tc`, `ip` және `ethtool` (`sudo` тек `--with-net-boost` орнату кезінде қажет).

---

## Орнату және жаңарту

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` барлық алты орындалатын файлды (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` және `steam-auto-ui`) `~/.local/bin` каталогына көшіреді, жұмыс үстелі таңбашасын (`~/.local/share/applications/steam-auto-profiler.desktop`) орнатады, `~/.config/steam-auto-profiler/profiles` бумасын жасайды және стандартты vkBasalt пресеттерін (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`) қосады. `~/.local/bin` каталогы `PATH` ішінде екенін тексеріңіз.

Орнатушының қосымша жалаушаларын біріктіруге болады:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: `/usr/local/bin/steam-net-boost` (және басқа скрипттердің жүйелік көшірмелерін), сондай-ақ `steam-net-boost` үшін құпиясөзсіз тар ауқымды `sudoers` ережесін орнатады.
- `--compat-cachy-run`: бар `/usr/local/bin/cachy-run` файлын `/usr/local/bin/cachy-run.bak` ретінде сақтайды (егер ол әлі Steam Auto-Profiler қабықшасы болмаса) және `steam-auto-run` бағыттаушы қабықшасын орнатады.
- `--with-auto-sync` (`--enable-auto-sync`): табылған барлық Steam кітапханалары үшін пайдаланушының `steam-auto-profiler-sync.path` systemd бақылаушысын және сәйкес oneshot қызметін орнатып іске қосады.
- `--uninstall`: орнатылған бинарлы файлдарды, жұмыс үстелі таңбашасын, қосымша желі көмекшісі мен `sudoers` ережесін, үйлесімділік қабықшасын және автосинхрондаудың systemd юниттерін жояды.

Қолданыстағы репозиторийді жаңарту үшін:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Ойындарды синхрондамас бұрын жүйенің дайындығын тексеріңіз:

```bash
steam-auto-run --doctor
```

---

## Толық іске қосу конвейері

1. **AppID анықтау:** `SteamAppId`, `STEAM_COMPAT_APP_ID`, одан кейін `GAMEID` айнымалыларын тексереді (Lutris/Heroic/UMU үшін `umu-` префиксін алып тастайды).
2. **Кітапхана мен таңбашаларды табу:** `steam-auto-detect` Steam түбірлік бумаларын және `libraryfolders.vdf` ішіндегі қосымша кітапханаларды іздейді, `appmanifest_<APPID>.acf` файлын оқиды немесе тек оқу режимінде бинарлы `userdata/*/config/shortcuts.vdf` файлына жүгінеді, содан кейін 10 деңгейге дейінгі бір өтулі `find` жүргізеді (`screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization` бумаларын өткізіп жібереді).
3. **Бес деңгейлі жіктеу басымдығы:**
   - **1. `competitive-anticheat`:** белгілі жарыстық AppID немесе табылған античит ортасы (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE және т.б.). OptiScaler, MLFG, vkBasalt және асинхронды DXVK өшіріледі; төмен кідіріс және сессиялық желі QoS қосылады.
   - **2. `vr`:** `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` немесе `vr-run`/`-vr` таңбаша жалаушалары анықталғанда `AUTO_IS_VR=1` экспортталады.
   - **3. `native-fsr4` / `native-fsr`:** модульдік FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Драйвер деңгейіндегі FSR 4 жаңартуын қосады (`PROTON_FSR4_UPGRADE=1` немесе AMD RDNA 3 жүйесінде `PROTON_FSR4_RDNA3_UPGRADE=1`).
   - **4. `legacy-upscaler`:** ескірген DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) немесе FSR 2/3.0 DLL файлдары. `AUTO_OPTISCALER=1` белгісін қойып, `AUTO_UPSCALER_INFO` анықтамасын орнатады.
   - **5. `standard`:** нативті Wine Wayland және төмен кідірісті VRR бар қауіпсіз профиль.
4. **VRR жаңарту жиілігі бойынша кадр шектеуі:** нақты көрсетілген `VRR_CAP=<fps>` әрқашан басым болады (`VRR_CAP=0` шектеуді өшіреді). Басқа жағдайда дисплейдің белсенді жаңарту жиілігі `kscreen-doctor` (KDE Plasma 6 белсенді `*` режимі немесе ескі `Hz` шығысы), `wlr-randr` не `xrandr` арқылы анықталып, әдепкі бойынша 1:1 қолданылады (240 Гц кезінде `240 FPS`). Қосымша `-6%` VRR қауіпсіздік қоры үшін `VRR_MINUS_MARGIN=1` қосыңыз (`hz * 94 / 100`, мысалы 240 Гц кезінде `225 FPS`). Gamescope сессияларында `VRR_CAP` нақты берілмесе, DXVK/VKD3D шектеулері орнатылмайды.
5. **Өзара үйлеспейтін баптаулардан қорғау:**
   - **FSR 4 / OptiScaler + vkBasalt:** `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` немесе `USE_OPTISCALER=1` белсенді болған кезде `ENABLE_VKBASALT=0` мәжбүрлі орнатылады (қос айқындау мен HDR10 клиппингінің алдын алады).
   - **MLFG + төмен кідіріс / VRR шектеулері:** `MLFG=1` (`USE_MLFG=1`) кезінде `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0` экспортталады, `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` және `DXVK_FRAME_PACE` алынып тасталады, ал AMD RDNA 3 жүйесінде `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` экспортталады. `USE_MLFG=0` және VRR шектеуі белсенді болғанда `DXVK_FRAME_PACE=low-latency-vrr` экспортталады.
   - **Заманауи DX12 + Safe DX12:** `USE_SAFEDX12=0` болғанда AMD жүйесінде `PROTON_NATIVE_AGS=1` және `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` экспортталады (`SAFEDX12=1` кезінде толық өткізіледі).
6. **Compat-токендерді сәйкестендіру:** басқарылатын мүмкіндіктер пайдаланушының бұрынғы мәндерін өшірмей `PROTON_ADD_CONFIG` пен `STEAM_COMPAT_CONFIG` екеуіне де қосылады: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **KDE Plasma 6 авто-HDR ауыстыруы (`AUTO_HDR_SWITCH=1`):** Gamescope-тан тыс `DXVK_HDR=1` (немесе `USE_HDR=1`) бірге қосылса, `kscreen-doctor -o` арқылы негізгі белсенді мониторды тексереді; егер HDR өшірулі болса, іске қосар алдында қосып, `EXIT`/`INT`/`TERM` ұстағышында SDR-ді қалпына келтіреді.
8. **Кадр уақытын жасырын бенчмаркингтеу (`BENCH=1`):** MangoHud-ты жасырын CSV режимінде іске қосады (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), ойын аяқталғанда frametime деректерін талдап, `Avg FPS`, `1% Low FPS` және `P99 (ms)` көрсеткіштерін `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` файлына қосады және уақытша CSV файлдарын жояды.
9. **Жылдам апат кезіндегі Safe Mode автоқалпына келтіруі:** егер Proton/Windows ойыны Wayland немесе DX12 эксперименттік жалаушалары белсенді кезде (`USE_XWAYLAND=0` немесе `USE_SAFEDX12=0`) `20s` ішінде (`SAP_CRASH_THRESHOLD_SEC` арқылы бапталады) нөлден өзгеше кодпен жабылса, `last-<APPID>.log` және `last-launch.log` файлдарына `crash_hint` жазады, ал GUI белсенді болса келесі іске қосу үшін `USE_XWAYLAND=1` + `USE_SAFEDX12=1` сақтауды ұсынады.
10. **Жоспарлаушы және желі өмірлік циклі:** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (тек `ananicy-cpp.service` белсенді емес кезде) -> тікелей іске қосу тізбегімен жұмыс істейді, қосымша `PRIME=1` (`prime-run`) қолдайды. `USE_NET_OPT=1` болса, `steam-net-boost` статикалық түбірлік CAKE және HTB + жапырақты CAKE иерархияларын сақтай отырып, `flock` арқылы сілтеме санағышы бар `on`/`off` режимін орындайды.

---

## Бірыңғай басқару орталығы (`steam-auto-ui`)

`steam-auto-ui` құралын жұмыс үстелінің қолданбалар мәзірінен, `steam-auto-run --ui` арқылы немесе тікелей іске қосыңыз:

```bash
steam-auto-ui                 # Qt6 GUI (PyQt6/PySide6) немесе curses TUI автоматты анықтау
steam-auto-ui --gui           # Нативті Qt6 GUI терезесін мәжбүрлі ашу
steam-auto-ui --tui           # Стандартты curses TUI мәжбүрлі іске қосу (SSH арқылы жұмыс істейді)
steam-auto-ui --lang fi       # Интерфейс тілін нақты беру (мыс., --lang kk; 27 тіл қолдау табады)
steam-auto-ui --check         # Автономды өзін-өзі тексеру (JSON диагностикасын шығарады)
```

`steam-auto-ui` жүйелік локальді `LC_ALL` / `LC_MESSAGES` / `LANG` арқылы автоматты анықтайды және бағдарламаны қайта іске қоспай-ақ барлық 27 тіл арасында ауысу үшін Qt6 GUI-де тіл таңдау тізімін (ал `curses` TUI-де `L` пернесін) ұсынады.

### Бес синхрондалған бөлім

1. **Ойындар және профильдер (Games & Profiles):** Steam ойындары мен тек оқу режиміндегі Non-Steam `shortcuts.vdf` жазбаларының сүзгіленетін кестесі (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), апскейлер SDK белгісі (`AUTO_UPSCALER_INFO`), барлық 10 профиль қосқышы + `VRR_CAP` үшін нақты уақыттағы өзара үйлесімділік тексерісі, `Dry-Run Preview`, `Benchmarks` өту батырмасы және `Reset Profile`.
2. **Жүйе және телеметрия (System & Telemetry):** `steam-auto-run --doctor` нәтижелерін блоктамай көрсету, `scxctl get` / `sched_ext` күйі, орнатылған стек нұсқалары (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), шейдер кэшінің көлемі (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` файлындағы git/AUR нұсқа төмендеу ескертулері, GPU VRAM/жүктеме/температурасы, `tc -s qdisc` LAN (`10:`) және WAN (`20:`/root) өткізу қабілеті мен `av_delay`, сондай-ақ `vr-mode status`.
3. **Кітапхананы синхрондау (Library Sync):** Steam жұмыс күйінің қорғау баннері және бір басу арқылы `--report`, `--sanitize --dry-run`, `--sanitize` (Steam іске қосулы кезде бұғатталады) мен `--migrate-cachy-run`.
4. **Журналдар және қалпына келтіру (Logs & Recovery):** `last-launch.log` және `last-<APPID>.log` файлдарын қарау, `crash_hint` ескертулерін тексеру және бір басумен Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) қолдану.
5. **Бенчмарктар (Benchmarks):** `BENCH=1` кадр уақыты сынақтарының сүзгіленетін салыстырмалы кестесі (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR оркестрациясы (`vr-run`)

Steam ішінде VR ойындары үшін **Properties > General > Launch Options** өрісіне келесіні жазыңыз:

```text
vr-run %command%
```

- Мұраланған flatscreen баптауларын тазартады (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- `MESA_VK_DEVICE_SELECT` арқылы ең үлкен VRAM-ы бар дискретті GPU-ды автоматты таңдайды және AMD GPU үшін `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` орнатады.
- WiVRn және xrizer OpenXR/OpenVR жолдарын динамикалық іздейді (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) және пайдаланушының нақты айнымалыларын өшірмей `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` пен `LD_LIBRARY_PATH` мәндерін баптайды.
- `vr-mode` орнатылған болса, `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` файлында (`flock` арқылы) `vr-mode on` / `vr-mode off` сессияларын санайды (`VR_AUTO_MODE=0` мұны өшіреді).
- `ananicy-cpp` күйін ескеретін сол жоспарлаушы тізбегін пайдаланады (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> тікелей `exec`).
- Қорытынды айнымалыларды кез келген уақытта `vr-run --dry-run` арқылы алдын ала көруге болады.

`steam-auto-run` SteamVR (`250820`) пен `-vr`/`--vr` іске қосуларын автоматты түрде айналып өтеді, ал `steam-auto-sync` VR ойындарына `vr-run %command%` параметрін автоматты тағайындап сақтайды.

---

## Steam кітапханасын синхрондау (`steam-auto-sync`)

`localconfig.vdf` файлына жазбас бұрын Steam-ді толық жабыңыз:

```bash
steam-auto-sync --report              # Кітапхана мен shortcuts.vdf тек оқу аудиті
steam-auto-sync --print-library-paths # Табылған барлық Steam кітапханаларын көрсету
steam-auto-sync --dry-run             # Өзгерістерді алдын ала көру
steam-auto-sync                       # steam-auto-run / vr-run қосу
steam-auto-sync --sanitize --dry-run  # Ескі жалаушаларды тазалауды алдын ала көру
steam-auto-sync --sanitize            # Артық/ескірген жалаушаларды тазалау (бүркеншік: --clean)
steam-auto-sync --migrate-cachy-run   # Ескі cachy-run профильдерін көшіру
steam-auto-sync --remove              # steam-auto-run қабықшасын алып тастау
```

- Уақыт белгісі бар `localconfig.vdf.bak.*` сақтық көшірмелері `--keep-backups N` параметрімен автоматты тазартылады (әдепкі `10`; `0` барлығын сақтайды).
- Белгілі бір AppID мәндерін өткізіп жіберу үшін оларды `~/.config/steam-auto-profiler/ignore_appids.txt` файлына (әр жолға бірден, `#` түсініктемелері рұқсат етілген) жазыңыз.
- Автосинхрондаудың systemd бақылаушысы (`./install.sh --with-auto-sync` немесе `steam-auto-sync --install-systemd`) Steam манифесттері өзгергенде `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` командасын іске қосады.

---

## CLI және профильдер анықтамалығы

### Командалар

| Мақсаты | Команда |
| --- | --- |
| Жүйе дайындығын тексеру | `steam-auto-run --doctor` (бүркеншік `--check-system`) |
| Басқару орталығын ашу (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` немесе `steam-auto-run --ui` |
| Ойынды тексеру (адам оқитын түрде) | `steam-auto-run --inspect APPID` |
| Ойынды тексеру (JSON) | `steam-auto-detect --inspect --json APPID` |
| Профильді интерактивті қайта баптау | `steam-auto-run --configure APPID` |
| Іске қосу ортасын алдын ала көру | `steam-auto-run --dry-run APPID` |
| Сақталған профильді бастапқы күйге келтіру | `steam-auto-run --reset APPID` |
| Сақталған профильдер тізімі | `steam-auto-run --list-profiles` |
| Соңғы іске қосу журналын көрсету | `steam-auto-run --last-log [APPID]` |
| VR іске қосу ортасын алдын ала көру | `vr-run --dry-run` |
| Желі көмекшісін тексеру (тек оқу) | `steam-net-boost status [IFACE]` |

### Сақталған `.env` профиль кілттері мен орта айнымалылары

Профиль файлдары `~/.config/steam-auto-profiler/profiles/<APPID>.env` мекенжайында сақталады және рұқсат етілген `KEY=VALUE` пішімін қабылдайды (қабықша командаларын алмастыру және белгісіз кілттер қауіпсіз елеусіз қалады):

| `.env` кілті | Орта айнымалысы | Әсері |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Нативті Wine Wayland орнына XWayland-ты мәжбүрлі пайдалану |
| `USE_FSR4=0` | `FSR4=0` | Драйвер деңгейіндегі FSR 4 жаңартуын өшіру (әдепкі `1`) |
| `USE_MLFG=1` | `MLFG=1` | Кадр генерациясын қосу (Anti-Lag, төмен кідіріс және VRR шектеулерін өшіреді) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | OptiScaler көпірін қосу (`competitive-anticheat` үшін қорғаумен өшіріледі) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | vkBasalt айқындауын қосу (FSR 4 немесе OptiScaler белсенді болса өшеді) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Эксперименттік `VKD3D_CONFIG` жалаушалары мен `vkd3dbindlesstb` токенін өткізіп жіберу |
| `USE_NET_OPT=1` | `NETOPT=1` | `steam-net-boost` арқылы сессиялық желі QoS қосу |
| `USE_SDL=1` | `SDL=1` | Нативті SDL / Steam Input эмуляциясына басымдық беру |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Steam Overlay үшін `LD_PRELOAD` сақтау |
| `USE_CEF_FIX=1` | `CEF=1` | CEF лаунчерлері үшін `--in-process-gpu` қосу |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Ескі ойындар үшін NTSync өшіру |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Терезе менеджерінің жиектерін өшіру |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Арнайы DXVK/VKD3D кадр шектеуі (`0` шектеуді өшіреді) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Монитор жиілігінен `-6%` қор қолдану (мыс., 240 Гц кезінде `225 FPS`) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Wine Wayland астында перне тіркесімдерін бұғаттауға рұқсат беру (әдепкі `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Іске қосқанда KDE Plasma 6 HDR-ді автоқосып, шыққанда SDR-ге қайтару |
| — | `BENCH=1`, `BENCH_DURATION=60` | Жасырын MangoHud CSV бенчмаркін іске қосып, JSON қорытындысын сақтау |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Іске қосар алдындағы `kdialog`/`zenity` чек-листін жасыру немесе мәжбүрлі ашу |
| — | `FSR_HUD=1` | FSR/DLSS/MLFG HUD индикатор айнымалыларын экспорттау |
| — | `VULKAN=1` / `PRIME=1` | `-vulkan` қосу / `prime-run` арқылы іске қосу |
| — | `GAMEID=umu-<appid>` | UMU / Lutris / Heroic AppID мәндерін анықтау |

---

## Lutris, Heroic, Faugus және UMU

- **Lutris:** кеңейтілген баптауларды қосыңыз, `proton-cachyos-slr` (немесе өз Proton жинағыңызды) таңдаңыз, Lutris runtime-ды өшіріңіз, жүйелік кітапханаларға басымдық беріңіз және команда префиксі ретінде `steam-auto-run` көрсетіңіз.
- **Heroic / Faugus:** `proton-cachyos-slr` таңдап, қабықша / команда префиксі ретінде `steam-auto-run` қосыңыз.
- **UMU / Protonfixes:** қажет болғанда `PROTON_VERB=waitforexitandrun` және `GAMEID=umu-<appid>` экспорттаңыз.

---

## Ақаулықтарды жою

- **Wayland немесе DX12 кезінде жылдам құлау:** `steam-auto-ui` ішінде **Logs & Recovery** ашыңыз (немесе `steam-auto-run --last-log APPID` орындаңыз) да Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) қолданыңыз, не `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%` арқылы іске қосыңыз.
- **Античиті бар ойындар іске қосылмайды:** `proton-cachyos-slr` (Steam Linux Runtime) пайдаланыңыз және EAC v2, `/dev/ntsync` пен `vm.max_map_count` күйін тексеру үшін `steam-auto-run --doctor` орындаңыз.
- **Steam іске қосу параметрлерін қайтарып тастайды:** `steam-auto-sync` немесе `steam-auto-sync --sanitize` орындамас бұрын Steam-ді толық жабыңыз.
- **VRR шектеуі қате немесе жоқ:** `VRR_CAP=<fps>` мәнін нақты көрсетіңіз, өшіру үшін `VRR_CAP=0`, ал `-6%` қор үшін `VRR_MINUS_MARGIN=1` қойыңыз. Gamescope ішінде DXVK/VKD3D шектеулері тек `VRR_CAP` нақты берілгенде ғана экспортталады.
- **Желі QoS тексерісі:** `steam-net-boost status` орындаңыз (артықшылықсыз, тек оқу). Автоматты сессиялық QoS қажет болса, `./install.sh --with-net-boost` арқылы жүйелік көмекшіні орнатыңыз.

Сондай-ақ [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) (ішкі құрылым) және барлық 27 тілдегі нұсқаулықтар үшін [i18n Index](../README.md) бетін қараңыз.
