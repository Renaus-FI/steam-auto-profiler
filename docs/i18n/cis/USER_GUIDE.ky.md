# Steam Auto-Profiler — Колдонуучунун колдонмосу

> [English User Guide](../../USER_GUIDE.md) · [i18n Index](../README.md)

Бул колдонмо **Steam Auto-Profiler v2.0** системасын толук орнотууну, кадимки экран (flatscreen) жана VR оюндарын иштетүү оркестрациясын, `steam-auto-ui` башкаруу борборун, китепкананы шайкештештирүүнү, өндүрүмдүүлүктү өлчөөнү (бенчмаркинг) жана мүчүлүштүктөрдү оңдоону камтыйт.

Steam Auto-Profiler — Linux үчүн жеңил Bash/Python ишке киргизгич жана башкаруу борбору. Ал Steam AppID'син (же Steam'ге кирбеген жарлыкты) текшерип, драйвер, масштабдагыч (upscaler) жана античит боюнча катаал коргоо эрежелери менен контекстке ылайыктуу профилди колдонот да, оюндун бар болгон буйругун иштетет. Ал эч качан үчүнчү тараптын Proton чөйрөсүн камтыбайт жана киргизбейт.

---

## Талаптар

- Linux иш столунун сессиясы (KDE Plasma 6 / Wayland, GNOME, wlroots же X11), Bash 5+, Python 3.10+, Steam жана стандарттуу системалык куралдар.
- Кошумча нативдүү башкаруу борборунун GUI'си: `PyQt6` же `PySide6` (болбогондо автоматтык түрдө кошумча көз карандылыгы жок стандарттуу китепканадагы `curses` TUI режимине өтөт).
- Кошумча ишке киргизүү алдындагы текшерүү тизмеси терезелери: `kdialog` же `zenity`.
- Кошумча үнсүз кадр убактысын (frametime) өлчөө: `mangohud`.
- Кошумча сессиялык тармак жардамчысы: `tc`, `ip` жана `ethtool` (`sudo` бир гана `--with-net-boost` орнотуу учурунда талап кылынат).

---

## Орнотуу жана жаңыртуулар

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` бардык алты аткарылуучу файлды (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` жана `steam-auto-ui`) `~/.local/bin` папкасына көчүрөт, иш столунун жарлыгын (`~/.local/share/applications/steam-auto-profiler.desktop`) орнотот, `~/.config/steam-auto-profiler/profiles` папкасын түзөт жана vkBasalt'тын демейки пресеттерин (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`) кошот. `~/.local/bin` папкасы `PATH` тизмесинде бар экенин текшериңиз.

Кошумча орнотуу желекчелерин бириктирип колдонууга болот:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: `/usr/local/bin/steam-net-boost` файлын (ошондой эле башка скрипттердин системалык көчүрмөлөрүн) жана `steam-net-boost` үчүн тар чектелген сырсөзсүз sudoers эрежесин орнотот.
- `--compat-cachy-run`: бар болгон `/usr/local/bin/cachy-run` файлын `/usr/local/bin/cachy-run.bak` катары сактайт (эгер ал мурунтан Steam Auto-Profiler өткөргүчү болбосо) жана `steam-auto-run` буйругуна багыттоочу shim орнотот.
- `--with-auto-sync` (`--enable-auto-sync`): табылган бардык Steam китепканалары боюнча колдонуучунун systemd `steam-auto-profiler-sync.path` байкоочусун жана тиешелүү бир жолку кызматын орнотуп иштетет.
- `--uninstall`: орнотулган аткарылуучу файлдарды, иш столунун жарлыгын, кошумча тармак жардамчысын/sudoers эрежесин, шайкештик shim'ин жана колдонуучунун systemd auto-sync бирдиктерин өчүрөт.

Бар болгон орнотууну жаңыртуу үчүн:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Оюндарды шайкештештирүүдөн мурун системанын даярдыгын текшериңиз:

```bash
steam-auto-run --doctor
```

---

## Башынан аягына чейин ишке киргизүү конвейери

1. **AppID аныктоо:** Ирети менен `SteamAppId`, `STEAM_COMPAT_APP_ID`, андан кийин `GAMEID` өзгөрмөлөрүн текшерет (Lutris/Heroic/UMU үчүн `umu-` префиксин алып салат).
2. **Китепканаларды жана жарлыктарды табуу:** `steam-auto-detect` Steam'дин негизги папкаларын жана `libraryfolders.vdf` ичиндеги кошумча китепканаларды издейт, `appmanifest_<APPID>.acf` файлын окуйт же окууга гана уруксат берилген режимде бинардык `userdata/*/config/shortcuts.vdf` файлына кайрылат; андан соң 10 деңгээл тереңдикке чейин бир өтмөктүү `find` аткарат (`screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization` папкаларын өткөрүп жиберүү менен).
3. **Беш деңгээлдүү классификация артыкчылыгы:**
   - **1. `competitive-anticheat`:** Белгилүү мелдештик AppID же аныкталган античит модулу (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE ж.б.). OptiScaler, MLFG, vkBasalt жана асинхрондук DXVK'ны өчүрөт; төмөнкү кечигүү режимин жана сессиялык тармак QoS'ту иштетет.
   - **2. `vr`:** Табылган `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` же `vr-run`/`-vr` жарлык желекчелери. `AUTO_IS_VR=1` экспорттойт.
   - **3. `native-fsr4` / `native-fsr`:** Модулдук FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Драйвер деңгээлиндеги FSR 4 жаңыртуусун иштетет (`PROTON_FSR4_UPGRADE=1` же AMD RDNA 3 видеокартасында `PROTON_FSR4_RDNA3_UPGRADE=1`).
   - **4. `legacy-upscaler`:** Эски DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) же FSR 2/3.0 DLL файлдары. `AUTO_OPTISCALER=1` белгилейт жана `AUTO_UPSCALER_INFO` көрсөтмө маалыматын орнотот.
   - **5. `standard`:** Коопсуз нативдүү Wine Wayland + төмөнкү кечигүүлүү VRR профили.
4. **VRR жаңылануу жыштыгын чектөө:** Так көрсөтүлгөн `VRR_CAP=<fps>` ар дайым үстөмдүк кылат (`VRR_CAP=0` чектөөнү өчүрөт). Болбосо активдүү экрандын жаңылануу жыштыгы `kscreen-doctor` (KDE Plasma 6 активдүү `*` режими же эски `Hz`), `wlr-randr` же `xrandr` аркылуу аныкталып, демейки боюнча 1:1 колдонулат (240 Гц монитордо `240 FPS`). Кошумча `-6%` VRR коопсуздук кору үчүн `VRR_MINUS_MARGIN=1` күйгүзүңүз (`hz * 94 / 100`, мисалы 240 Гцте `225 FPS`). Gamescope сессияларында `VRR_CAP` атайын көрсөтүлбөсө, DXVK/VKD3D чектөөлөрү коюлбайт.
5. **Өз ара жокко чыгаруучу коргоо эрежелери:**
   - **FSR 4 / OptiScaler + vkBasalt:** `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` же `USE_OPTISCALER=1` активдүү болгондо `ENABLE_VKBASALT=0` мажбурлап коюлат (кош курчутууну жана HDR10 кесилишин алдын алат).
   - **MLFG + Төмөнкү кечигүү / VRR чектөөлөрү:** `MLFG=1` (`USE_MLFG=1`) өзгөрмөлөрү `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0` маанилерин экспорттойт, `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` жана `DXVK_FRAME_PACE` өзгөрмөлөрүн тазалайт жана AMD RDNA 3'тө `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` экспорттойт. `USE_MLFG=0` болуп, VRR чектөөсү активдүү болгондо `DXVK_FRAME_PACE=low-latency-vrr` экспорттолот.
   - **Заманбап DX12 + Safe DX12:** AMD'де `PROTON_NATIVE_AGS=1` жана `USE_SAFEDX12=0` болгондо `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` экспорттойт (`SAFEDX12=1` болгондо таза алынып салынат).
6. **Compat-токендерди шайкештештирүү:** Башкарылуучу функциялар колдонуучунун бар маанилерин өчүрбөстөн `PROTON_ADD_CONFIG` жана `STEAM_COMPAT_CONFIG` өзгөрмөлөрүнүн экөөнө тең кошулат: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Автоматтык KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** Gamescope сыртында `DXVK_HDR=1` (же `USE_HDR=1`) менен иштетилгенде, негизги активдүү экранды `kscreen-doctor -o` аркылуу текшерет; эгер HDR өчүк болсо, ишке киргизүү алдында аны күйгүзөт жана чыкканда `EXIT`/`INT`/`TERM` кармагычы (trap) аркылуу SDR'ди калыбына келтирет.
8. **Үнсүз кадр убактысын өлчөө (`BENCH=1`):** MangoHud'ду жашыруун CSV режиминде иштетет (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), чыккандан кийин кадр убактыларын талдап, `Avg FPS`, `1% Low FPS` жана `P99 (ms)` маанилерин `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` файлына кошот жана убактылуу CSV файлдарын өчүрөт.
9. **Тез бузулууда Коопсуз режимге (Safe Mode) авто-калыбына келтирүү:** Эгер Proton/Windows оюну эксперименталдык Wayland же DX12 желекчелери күйүк турганда (`USE_XWAYLAND=0` же `USE_SAFEDX12=0`) `20s` ичинде (`SAP_CRASH_THRESHOLD_SEC` аркылуу жөндөлөт) нөлдөн айырмаланган код менен жабылса, `last-<APPID>.log` жана `last-launch.log` файлдарына `crash_hint` жазат жана (GUI активдүү болгондо) кийинки ишке киргизүү үчүн `USE_XWAYLAND=1` + `USE_SAFEDX12=1` сактоону сунуштайт.
10. **Пландоочу жана тармактын жашоо цикли:** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (`ananicy-cpp.service` активдүү эмес болгондо гана) -> түз аткаруу чынжыры аркылуу, кошумча `PRIME=1` (`prime-run`) колдоосу менен иштейт. Эгер `USE_NET_OPT=1` болсо, `steam-net-boost` статикалык root CAKE жана HTB + leaf CAKE иерархияларын сактап калуу менен `flock` аркылуу шилтеме эсептегичтүү `on`/`off` режимин аткарат.

---

## Бирдиктүү башкаруу борбору (`steam-auto-ui`)

`steam-auto-ui` программасын иш столунун тиркемелер менюсунан, `steam-auto-run --ui` буйругу аркылуу же түз ишке киргизиңиз:

```bash
steam-auto-ui                 # Qt6 GUI (PyQt6/PySide6) же curses TUI режимин автоматтык аныктайт
steam-auto-ui --gui           # Нативдүү Qt6 GUI терезесин мажбурлап ачуу
steam-auto-ui --tui           # Стандарттуу китепканадагы curses TUI режимин мажбурлап ачуу (SSH аркылуу иштейт)
steam-auto-ui --lang ky       # Көрсөтүлгөн UI тили менен ишке киргизүү (27 тил колдоого алынат)
steam-auto-ui --check         # Экрансыз өзүн-өзү текшерүү (JSON диагностикасын чыгарат)
```

`steam-auto-ui` системанын тилин `LC_ALL` / `LC_MESSAGES` / `LANG` өзгөрмөлөрүнөн автоматтык түрдө аныктайт жана кайра иштетпестен 27 тилдин ортосунда дароо которулуу үчүн Qt6 GUI'де тил тандоо тизмесин (`curses` TUI'де `L` тез баскычын) сунуштайт.

### Беш шайкештештирилген көрүнүш

1. **Games & Profiles:** Steam оюндарынын жана окууга гана мүмкүн болгон Steam'ден тышкаркы `shortcuts.vdf` жазууларынын чыпкалануучу таблицасы (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), Upscaler SDK белгиси (`AUTO_UPSCALER_INFO`), бардык 10 профиль которгучу + `VRR_CAP` боюнча жандуу өз ара жокко чыгаруу текшерүүсү, `Dry-Run Preview`, `Benchmarks` өтүү баскычы жана `Reset Profile`.
2. **System & Telemetry:** Бөгөттөбөгөн жандуу көрсөткүчтөр: `steam-auto-run --doctor`, `scxctl get` / `sched_ext` абалы, орнотулган стек версиялары (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), шейдер кэшинин көлөмү (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` git/AUR версия төмөндөө эскертүүлөрү, GPU VRAM/жүктөмү/температурасы, `tc -s qdisc` LAN (`10:`) жана WAN (`20:`/root) өткөрүү жөндөмдүүлүгү менен `av_delay`, ошондой эле `vr-mode status`.
3. **Library Sync:** Steam иштеп жаткан абалын көрсөткөн жандуу коргоо баннери жана бир басуу менен `--report`, `--sanitize --dry-run`, `--sanitize` (Steam иштеп турганда баш тартылат) жана `--migrate-cachy-run`.
4. **Logs & Recovery:** `last-launch.log` жана `last-<APPID>.log` журналдарын көрүңүз, `crash_hint` эскертүүлөрүн текшериңиз жана бир басуу менен Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) колдонуңуз.
5. **Benchmarks:** `BENCH=1` кадр убактысы сыноолорунун чыпкалануучу салыштырма таблицасы (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR оркестрациясы (`vr-run`)

VR оюндары үчүн Steam'де **Касиеттер > Жалпы > Ишке киргизүү параметрлери** бөлүмүнө муну жазыңыз:

```text
vr-run %command%
```

- Калып калган flatscreen жөндөөлөрүн тазалайт (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- `MESA_VK_DEVICE_SELECT` аркылуу эң чоң VRAM'дуу дискреттүү GPU'ну автоматтык тандайт жана AMD GPU'ларында `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` орнотот.
- WiVRn жана xrizer OpenXR/OpenVR жолдорун динамикалык түрдө текшерет (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) жана колдонуучунун так жөндөөлөрүн бузбастан `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` жана `LD_LIBRARY_PATH` өзгөрмөлөрүн конфигурациялайт.
- `vr-mode` орнотулган болсо, `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` файлында (`flock` менен) шилтеме эсептегичтүү `vr-mode on` / `vr-mode off` иштетет (`VR_AUTO_MODE=0` аны өчүрөт).
- Ошол эле `ananicy-cpp` эске алган пландоочу чынжыры аркылуу иштейт (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> түз `exec`).
- Чечилген өзгөрмөлөрдү каалаган убакта `vr-run --dry-run` менен алдын ала көрүңүз.

`steam-auto-run` SteamVR (`250820`) жана `-vr`/`--vr` ишке киргизүүлөрүн автоматтык өткөрүп жиберет, ал эми `steam-auto-sync` VR оюндары үчүн `vr-run %command%` буйругун автоматтык дайындап сактайт.

---

## Steam китепканасын шайкештештирүү (`steam-auto-sync`)

`localconfig.vdf` файлына жазуудан мурун Steam'ди толугу менен жабыңыз:

```bash
steam-auto-sync --report              # Окууга гана китепкана + shortcuts.vdf аудити
steam-auto-sync --print-library-paths # Табылган бардык Steam китепканаларын көрсөтүү
steam-auto-sync --dry-run             # Өзгөртүүлөрдү алдын ала көрүү
steam-auto-sync                       # steam-auto-run / vr-run кошуу
steam-auto-sync --sanitize --dry-run  # Эски желекчелерди тазалоону алдын ала көрүү
steam-auto-sync --sanitize            # Башаламан/жетим желекчелерди тазалоо (синоним: --clean)
steam-auto-sync --migrate-cachy-run   # Эски cachy-run профилдерин көчүрүү
steam-auto-sync --remove              # steam-auto-run орогучун алып салуу
```

- Убакыт белгиси бар `localconfig.vdf.bak.*` камдык көчүрмөлөрү `--keep-backups N` аркылуу автоматтык тазаланат (демейки `10`; `0` баарын сактайт).
- Белгилүү AppID'лерди чыгарып салуу үчүн аларды (ар бир сапка бирден, `#` комментарийлерине уруксат берилет) `~/.config/steam-auto-profiler/ignore_appids.txt` файлына жазыңыз.
- Systemd auto-sync байкоочусу (`./install.sh --with-auto-sync` же `steam-auto-sync --install-systemd`) Steam манифесттери өзгөргөндө `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` буйругун аткарат.

---

## CLI жана профиль маалымдамасы

### Буйруктар

| Максаты | Буйрук |
| --- | --- |
| Системанын даярдыгын текшерүү | `steam-auto-run --doctor` (синоним `--check-system`) |
| Башкаруу борборун ишке киргизүү (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` же `steam-auto-run --ui` |
| Оюнду текшерүү (адам окуй турган) | `steam-auto-run --inspect APPID` |
| Оюнду текшерүү (JSON) | `steam-auto-detect --inspect --json APPID` |
| Профилди интерактивдүү кайра жөндөө | `steam-auto-run --configure APPID` |
| Ишке киргизүү чөйрөсүн алдын ала көрүү | `steam-auto-run --dry-run APPID` |
| Сакталган профилди баштапкы абалга келтирүү | `steam-auto-run --reset APPID` |
| Сакталган профилдердин тизмеси | `steam-auto-run --list-profiles` |
| Акыркы ишке киргизүү журналын көрсөтүү | `steam-auto-run --last-log [APPID]` |
| VR ишке киргизүү чөйрөсүн алдын ала көрүү | `vr-run --dry-run` |
| Тармак жардамчысын текшерүү (окууга гана) | `steam-net-boost status [IFACE]` |

### Сакталган `.env` профиль ачкычтары жана чөйрө өзгөрмөлөрү

Профиль файлдары `~/.config/steam-auto-profiler/profiles/<APPID>.env` дарегинде жайгашат жана уруксат берилген ачкычтардын `KEY=VALUE` форматын кабыл алат (shell буйруктарын алмаштыруулар жана белгисиз ачкычтар коопсуз өткөрүп жиберилет):

| `.env` ачкычы | Чөйрө өзгөрмөсү | Таасири |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Нативдүү Wine Wayland ордуна XWayland мажбурлоо |
| `USE_FSR4=0` | `FSR4=0` | Драйвер деңгээлиндеги FSR 4 жаңыртуусун өчүрүү (демейки `1`) |
| `USE_MLFG=1` | `MLFG=1` | Кадр генерациясын иштетүү (Anti-Lag, төмөнкү кечигүү жана VRR чектөөлөрүн өчүрөт) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | OptiScaler көпүрөсүн иштетүү (`competitive-anticheat` үчүн коргоо менен өчүрүлгөн) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | vkBasalt курчутуусун иштетүү (FSR 4 же OptiScaler активдүү болгондо өчүрүлөт) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Эксперименталдык `VKD3D_CONFIG` желекчелерин жана `vkd3dbindlesstb` токенин өткөрүп жиберүү |
| `USE_NET_OPT=1` | `NETOPT=1` | `steam-net-boost` аркылуу сессиялык тармак QoS'ту иштетүү |
| `USE_SDL=1` | `SDL=1` | Нативдүү SDL / Steam Input эмуляциясына артыкчылык берүү |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Steam Overlay `LD_PRELOAD` маанисин сактоо |
| `USE_CEF_FIX=1` | `CEF=1` | CEF ишке киргизгичтери үчүн `--in-process-gpu` кошуу |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Эски оюндар үчүн NTSync өчүрүү |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Терезе башкаргычтын алкактарын өчүрүү |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Ыңгайлаштырылган DXVK/VKD3D кадр чектөөсү (`0` чектөөнү өчүрөт) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Монитор жыштыгына `-6%` кор колдонуу (мис., 240 Гцте `225 FPS`) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Wine Wayland алдында жарлыктарды бөгөттөөгө уруксат берүү (демейки `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Ишке киргизүүдө KDE Plasma 6 HDR'ди автоматтык күйгүзүү жана чыкканда SDR'ди калыбына келтирүү |
| — | `BENCH=1`, `BENCH_DURATION=60` | Үнсүз MangoHud CSV бенчмаркын иштетип, JSON жыйынтыгын сактоо |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Ишке киргизүү алдындагы `kdialog`/`zenity` текшерүү тизмесин жашыруу же мажбурлап ачуу |
| — | `FSR_HUD=1` | FSR/DLSS/MLFG HUD индикатор өзгөрмөлөрүн экспорттоо |
| — | `VULKAN=1` / `PRIME=1` | `-vulkan` кошуу / `prime-run` менен ороо |
| — | `GAMEID=umu-<appid>` | UMU / Lutris / Heroic AppID'лерин аныктоо |

---

## Lutris, Heroic, Faugus жана UMU

- **Lutris:** Кеңейтилген параметрлерди күйгүзүңүз, `proton-cachyos-slr` (же өз Proton курамыңызды) тандаңыз, Lutris runtime'ды өчүрүңүз, системалык китепканаларга артыкчылык бериңиз жана буйрук префиксин `steam-auto-run` деп орнотуңуз.
- **Heroic / Faugus:** `proton-cachyos-slr` тандап, орогуч/буйрук префикси катары `steam-auto-run` кошуңуз.
- **UMU / Protonfixes:** Зарыл болгондо `PROTON_VERB=waitforexitandrun` жана `GAMEID=umu-<appid>` экспорттоңуз.

---

## Мүчүлүштүктөрдү оңдоо

- **Wayland же DX12'де тез бузулуу:** `steam-auto-ui` ичинен **Logs & Recovery** бөлүмүн ачыңыз (же `steam-auto-run --last-log APPID` иштетиңиз) жана Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) колдонуңуз, же `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%` буйругун аткарыңыз.
- **Античит оюндары ачылбай жатат:** `proton-cachyos-slr` (Steam Linux Runtime) колдонуңуз жана EAC v2, `/dev/ntsync`, ошондой эле `vm.max_map_count` текшерүү үчүн `steam-auto-run --doctor` иштетиңиз.
- **Steam ишке киргизүү параметрлерин кайтарып салууда:** `steam-auto-sync` же `steam-auto-sync --sanitize` иштетүүдөн мурун Steam'ди толугу менен жабыңыз.
- **Туура эмес же жок VRR чектөөсү:** `VRR_CAP=<fps>` так орнотуңуз, өчүрүү үчүн `VRR_CAP=0`, же `-6%` кор үчүн `VRR_MINUS_MARGIN=1` колдонуңуз. Gamescope'то бир гана так көрсөтүлгөн `VRR_CAP` DXVK/VKD3D чектөөлөрүн экспорттойт.
- **Тармак QoS текшерүүсү:** `steam-net-boost status` иштетиңиз (артыкчылыксыз, окууга гана). Автоматтык сессиялык QoS керек болсо, root жардамчысын `./install.sh --with-net-boost` менен орнотуңуз.

Дизайн чоо-жайы үчүн [ARCHITECTURE.md](../../ARCHITECTURE.md), англисче негизги колдонмо үчүн [English User Guide](../../USER_GUIDE.md) жана бардык 27 тилдеги колдонмолор үчүн [i18n Index](../README.md) караңыз.
