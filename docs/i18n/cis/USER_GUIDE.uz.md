# Steam Auto-Profiler foydalanuvchi qo'llanmasi

> Asl hujjat: [English User Guide](../../USER_GUIDE.md) · Barcha tillar: [i18n Index](../README.md)

Ushbu qo'llanma **Steam Auto-Profiler v2.1** uchun to'liq o'rnatish, oddiy (flatscreen) va VR o'yinlarni ishga tushirish orkestratsiyasi, `steam-auto-ui` yagona boshqaruv markazi, Steam kutubxonasini sinxronlash, benchmark o'lchash hamda muammolarni bartaraf etish jarayonlarini qamrab oladi.

Steam Auto-Profiler — Linux uchun yengil Bash/Python ishga tushirgich va boshqaruv markazi bo'lib, Steam AppID (yoki Non-Steam yorlig'i) ni tahlil qiladi, drayver, upscaler va anti-cheat himoya cheklovlariga qat'iy rioya qilgan holda kontekstga mos profilni qo'llaydi hamda mavjud o'yin buyrug'ini ishga tushiradi. U hech qachon uchinchi tomon Proton muhitini o'zi bilan qo'shib bermaydi yoki kiritmaydi.

---

## Talablar

- Linux ish stoli sessiyasi (KDE Plasma 6 / Wayland, GNOME, wlroots yoki X11), Bash 5+, Python 3.10+, Steam va standart asosiy utilitalar.
- Ixtiyoriy nativ boshqaruv markazi GUI interfeysi: `PyQt6` yoki `PySide6` (mavjud bo'lmasa, tashqi bog'liqliklarsiz standart kutubxonadagi `curses` TUI rejimiga avtomatik o'tadi).
- Ishga tushirishdan oldingi ixtiyoriy tekshiruv oynalari: `kdialog` yoki `zenity`.
- Kadr vaqtini (frametime) yashirin benchmark qilish uchun ixtiyoriy vosita: `mangohud`.
- Sessiya tarmoq yordamchisi uchun ixtiyoriy vositalar: `tc`, `ip` va `ethtool` (`sudo` faqat `--with-net-boost` bilan o'rnatish vaqtida kerak bo'ladi).

---

## O'rnatish va yangilash

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` barcha oltita bajariluvchi faylni (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` va `steam-auto-ui`) `~/.local/bin` jildiga nusxalaydi, ish stoli yorlig'ini (`~/.local/share/applications/steam-auto-profiler.desktop`) o'rnatadi, `~/.config/steam-auto-profiler/profiles` katalogini yaratadi hamda standart vkBasalt presetlarini (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`) qo'shadi. `~/.local/bin` jildi `PATH` tarkibida ekanligiga ishonch hosil qiling.

O'rnatuvchining ixtiyoriy bayroqlarini birgalikda ishlatish mumkin:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: `/usr/local/bin/steam-net-boost` (shuningdek boshqa skriptlarning tizim nusxalari) va `steam-net-boost` uchun parolsiz, tor doiradagi `sudoers` qoidasini o'rnatadi.
- `--compat-cachy-run`: mavjud `/usr/local/bin/cachy-run` faylini `/usr/local/bin/cachy-run.bak` sifatida saqlab qoladi (agar u allaqachon Steam Auto-Profiler o'ramasi bo'lmasa) va `steam-auto-run` ga yo'naltiruvchi o'rama o'rnatadi.
- `--with-auto-sync` (`--enable-auto-sync`): topilgan barcha Steam kutubxonalari uchun foydalanuvchi systemd kuzatuvchisi `steam-auto-profiler-sync.path` va tegishli oneshot xizmatini o'rnatadi hamda yoqadi.
- `--uninstall`: o'rnatilgan bajariluvchi fayllar, ish stoli yorlig'i, ixtiyoriy tarmoq yordamchisi va `sudoers` qoidasi, moslik o'ramasi hamda avtosinxronlash systemd unitlarini o'chiradi.

Mavjud repozitoriyni yangilash uchun:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

O'yinlarni sinxronlashdan oldin tizim tayyorligini tekshiring:

```bash
steam-auto-run --doctor
```

---

## To'liq ishga tushirish konveyeri

1. **AppID aniqlash:** avval `SteamAppId`, keyin `STEAM_COMPAT_APP_ID`, so'ng `GAMEID` ni tekshiradi (Lutris/Heroic/UMU uchun `umu-` prefiksini olib tashlaydi).
2. **Kutubxona va yorliqlarni aniqlash:** `steam-auto-detect` Steam ildiz kataloglari va `libraryfolders.vdf` ichidagi qo'shimcha kutubxonalarni qidiradi, `appmanifest_<APPID>.acf` ni o'qiydi yoki faqat o'qish rejimida binar `userdata/*/config/shortcuts.vdf` fayliga murojaat qiladi, so'ngra 10 darajagacha chuqurlikda bir martalik `find` bajaradi (`screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization` jildlarini chetlab o'tadi).
3. **Besh darajali tasniflash ustuvorligi:**
   - **1. `competitive-anticheat`:** ma'lum musobaqaviy AppID yoki aniqlangan anti-cheat muhiti (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE va boshqalar). OptiScaler, MLFG, vkBasalt va asinxron DXVK ni o'chiradi; past kechikish va sessiya tarmoq QoS ni yoqadi.
   - **2. `vr`:** `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` yoki `vr-run`/`-vr` yorliq bayroqlari topilganda `AUTO_IS_VR=1` eksport qiladi.
   - **3. `native-fsr4` / `native-fsr`:** modulli FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Drayver darajasidagi FSR 4 yangilanishini yoqadi (`PROTON_FSR4_UPGRADE=1` yoki AMD RDNA 3 da `PROTON_FSR4_RDNA3_UPGRADE=1`).
   - **4. `legacy-upscaler`:** eski DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) yoki FSR 2/3.0 DLL fayllari. `AUTO_OPTISCALER=1` belgilaydi va `AUTO_UPSCALER_INFO` yo'riqnomasini o'rnatadi.
   - **5. `standard`:** xavfsiz nativ Wine Wayland + past kechikishli VRR profili.
4. **VRR yangilanish chastotasi bo'yicha kadr cheklovi:** aniq ko'rsatilgan `VRR_CAP=<fps>` har doim ustun turadi (`VRR_CAP=0` cheklovni o'chiradi). Aks holda displeyning faol yangilanish chastotasi `kscreen-doctor` (KDE Plasma 6 faol `*` rejimi yoki eski `Hz`), `wlr-randr` yoki `xrandr` orqali aniqlanadi va sukut bo'yicha 1:1 qo'llanadi (240 Hz da `240 FPS`). Ixtiyoriy `-6%` VRR zaxira chegarasi uchun `VRR_MINUS_MARGIN=1` ni yoqing (`hz * 94 / 100`, masalan 240 Hz da `225 FPS`). Gamescope sessiyalarida `VRR_CAP` aniq berilmagan bo'lsa, DXVK/VKD3D cheklovlari qo'yilmaydi.
5. **O'zaro istisno qiluvchi himoya qoidalari:**
   - **FSR 4 / OptiScaler + vkBasalt:** `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` yoki `USE_OPTISCALER=1` faol bo'lganda `ENABLE_VKBASALT=0` majburiy qo'llanadi (ikki karra keskinlashtirish va HDR10 klippingining oldini oladi).
   - **MLFG + past kechikish / VRR cheklovlari:** `MLFG=1` (`USE_MLFG=1`) bo'lganda `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0` eksport qilinadi, `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` va `DXVK_FRAME_PACE` olib tashlanadi, AMD RDNA 3 da esa `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` eksport qilinadi. `USE_MLFG=0` va VRR cheklovi faol bo'lganda `DXVK_FRAME_PACE=low-latency-vrr` eksport qilinadi.
   - **Zamonaviy DX12 + Safe DX12:** `USE_SAFEDX12=0` bo'lganda AMD da `PROTON_NATIVE_AGS=1` va `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` eksport qilinadi (`SAFEDX12=1` da to'liq o'tkazib yuboriladi).
6. **Compat-tokenlarni moslashtirish:** boshqariladigan funksiyalar foydalanuvchining mavjud qiymatlarini o'chirmasdan `PROTON_ADD_CONFIG` va `STEAM_COMPAT_CONFIG` ikkalasiga ham qo'shiladi: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **KDE Plasma 6 avto-HDR almashinuvi (`AUTO_HDR_SWITCH=1`):** Gamescope tashqarisida `DXVK_HDR=1` (yoki `USE_HDR=1`) bilan yoqilganda `kscreen-doctor -o` orqali asosiy faol ekranni tekshiradi; agar HDR hozir o'chiq bo'lsa, ishga tushirishdan oldin yoqadi va `EXIT`/`INT`/`TERM` ishlovchisida SDR ni tiklaydi.
8. **Yashirin frametime benchmarki (`BENCH=1`):** MangoHud ni yashirin CSV rejimida ishga tushiradi (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), chiqishda kadr vaqtlarini tahlil qilib, `Avg FPS`, `1% Low FPS` va `P99 (ms)` ko'rsatkichlarini `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` fayliga qo'shadi hamda vaqtinchalik CSV fayllarini o'chiradi.
9. **Tez qulashda Safe Mode avto-tiklanishi:** agar Proton/Windows o'yini eksperimental Wayland yoki DX12 bayroqlari faol bo'lganda (`USE_XWAYLAND=0` yoki `USE_SAFEDX12=0`) `20s` dan kam vaqtda (`SAP_CRASH_THRESHOLD_SEC` bilan sozlanadi) noldan farqli kod bilan yopilsa, `last-<APPID>.log` va `last-launch.log` fayllariga `crash_hint` yozadi hamda GUI faol bo'lsa keyingi ishga tushirish uchun `USE_XWAYLAND=1` + `USE_SAFEDX12=1` saqlashni taklif qiladi.
10. **Rejalashtiruvchi va tarmoq hayot sikli:** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (faqat `ananicy-cpp.service` nofaol bo'lganda) -> to'g'ridan-to'g'ri ishga tushirish zanjiri orqali ishlaydi, ixtiyoriy `PRIME=1` (`prime-run`) qo'llab-quvvatlanadi. `USE_NET_OPT=1` bo'lsa, `steam-net-boost` statik ildiz CAKE va HTB + barg CAKE iyerarxiyalarini saqlagan holda `flock` bilan havola hisoblagichli `on`/`off` ni bajaradi.

---

## Yagona boshqaruv markazi (`steam-auto-ui`)

`steam-auto-ui` ni ish stoli ilovalar menyusidan, `steam-auto-run --ui` orqali yoki to'g'ridan-to'g'ri ishga tushiring:

```bash
steam-auto-ui                 # Qt6 GUI (PyQt6/PySide6) yoki curses TUI ni avtomatik aniqlash
steam-auto-ui --gui           # Nativ Qt6 GUI oynasini majburiy ochish
steam-auto-ui --tui           # Standart kutubxonadagi curses TUI ni majburiy ochish (SSH da ishlaydi)
steam-auto-ui --lang fi       # Interfeys tilini aniq belgilash (mas., --lang uz; 27 ta til)
steam-auto-ui --check         # Avtonom o'z-o'zini tekshirish (JSON diagnostikasini chiqaradi)
```

`steam-auto-ui` tizim lokalini `LC_ALL` / `LC_MESSAGES` / `LANG` orqali avtomatik aniqlaydi va qayta ishga tushirmasdan barcha 27 til orasida almashish uchun Qt6 GUI da til tanlash menyusini (`curses` TUI da esa `L` tezkor tugmasini) taqdim etadi.

### Besh sinxronlashtirilgan bo'lim

1. **O'yinlar va profillar (Games & Profiles):** Steam o'yinlari va faqat o'qish rejimidagi Non-Steam `shortcuts.vdf` yozuvlarining filtrlanadigan jadvali (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), upscaler SDK belgisi (`AUTO_UPSCALER_INFO`), barcha 10 ta profil tugmasi + `VRR_CAP` bo'yicha jonli o'zaro istisno tekshiruvi, `Dry-Run Preview`, `Benchmarks` ga o'tish tugmasi va `Reset Profile`.
2. **Tizim va telemetriya (System & Telemetry):** `steam-auto-run --doctor` natijalarining bloklamaydigan jonli ko'rinishi, `scxctl get` / `sched_ext` holati, o'rnatilgan stek versiyalari (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), sheyder keshi hajmi (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` dagi git/AUR versiya pasayishi ogohlantirishlari, GPU VRAM/yuklama/harorati, `tc -s qdisc` LAN (`10:`) va WAN (`20:`/root) o'tkazuvchanligi hamda `av_delay`, shuningdek `vr-mode status`.
3. **Kutubxonani sinxronlash (Library Sync):** Steam ishlayotganligini ko'rsatuvchi jonli himoya banneri hamda bir bosish bilan `--report`, `--sanitize --dry-run`, `--sanitize` (Steam ishlayotgan paytda bloklanadi) va `--migrate-cachy-run`.
4. **Jurnallar va tiklash (Logs & Recovery):** `last-launch.log` va `last-<APPID>.log` ni ko'rish, `crash_hint` ogohlantirishlarini tekshirish hamda bir bosishda Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) ni qo'llash.
5. **Benchmarklar (Benchmarks):** `BENCH=1` frametime sinovlarining filtrlanadigan taqqoslash jadvali (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR orkestratsiyasi (`vr-run`)

Steam da VR o'yinlar uchun **Properties > General > Launch Options** maydoniga quyidagini kiriting:

```text
vr-run %command%
```

- Meros olingan flatscreen sozlamalarini tozalaydi (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- `MESA_VK_DEVICE_SELECT` orqali eng katta VRAM ga ega diskret GPU ni avtomatik tanlaydi va AMD GPU larda `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` ni o'rnatadi.
- WiVRn va xrizer OpenXR/OpenVR yo'llarini dinamik tekshiradi (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) va foydalanuvchining aniq o'zgaruvchilarini buzmasdan `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` hamda `LD_LIBRARY_PATH` ni sozlaydi.
- `vr-mode` o'rnatilgan bo'lsa, `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` da (`flock` bilan) `vr-mode on` / `vr-mode off` sessiyalarini hisoblaydi (`VR_AUTO_MODE=0` buni o'chiradi).
- Xuddi shu `ananicy-cpp` ni hisobga oluvchi rejalashtiruvchi zanjiridan foydalanadi (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> to'g'ridan-to'g'ri `exec`).
- Yakuniy o'zgaruvchilarni istalgan vaqtda `vr-run --dry-run` orqali oldindan ko'rish mumkin.

`steam-auto-run` SteamVR (`250820`) va `-vr`/`--vr` ishga tushirishlarini avtomatik chetlab o'tadi, `steam-auto-sync` esa VR o'yinlar uchun `vr-run %command%` ni avtomatik tayinlaydi va saqlab qoladi.

---

## Steam kutubxonasini sinxronlash (`steam-auto-sync`)

`localconfig.vdf` fayliga yozishdan oldin Steam ni to'liq yoping:

```bash
steam-auto-sync --report              # Kutubxona va shortcuts.vdf ni faqat o'qish rejimida audit qilish
steam-auto-sync --print-library-paths # Topilgan barcha Steam kutubxonalarini ko'rsatish
steam-auto-sync --dry-run             # O'zgarishlarni oldindan ko'rish
steam-auto-sync                       # steam-auto-run / vr-run qo'shish
steam-auto-sync --sanitize --dry-run  # Eski bayroqlarni tozalashni oldindan ko'rish
steam-auto-sync --sanitize            # Ortiqcha/eski bayroqlarni tozalash (taxallus: --clean)
steam-auto-sync --migrate-cachy-run   # Eski cachy-run profillarini ko'chirish
steam-auto-sync --remove              # steam-auto-run o'ramasini olib tashlash
```

- Vaqt belgili `localconfig.vdf.bak.*` zaxira nusxalari `--keep-backups N` bilan avtomatik tozalanadi (sukut bo'yicha `10`; `0` barchasini saqlaydi).
- Muayyan AppID larni istisno qilish uchun ularni `~/.config/steam-auto-profiler/ignore_appids.txt` fayliga (har bir qatorda bittadan, `#` izohlari ruxsat etilgan) yozing.
- Avtosinxronlash systemd kuzatuvchisi (`./install.sh --with-auto-sync` yoki `steam-auto-sync --install-systemd`) Steam manifestlari o'zgarganda `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` ni ishga tushiradi.

---

## CLI va profillar ma'lumotnomasi

### Buyruqlar

| Vazifa | Buyruq |
| --- | --- |
| Tizim tayyorligini tekshirish | `steam-auto-run --doctor` (taxallus `--check-system`) |
| Boshqaruv markazini ochish (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` yoki `steam-auto-run --ui` |
| O'yinni tekshirish (o'qishga qulay) | `steam-auto-run --inspect APPID` |
| O'yinni tekshirish (JSON) | `steam-auto-detect --inspect --json APPID` |
| Profilni interaktiv qayta sozlash | `steam-auto-run --configure APPID` |
| Ishga tushirish muhitini oldindan ko'rish | `steam-auto-run --dry-run APPID` |
| Saqlangan profilni tiklash | `steam-auto-run --reset APPID` |
| Saqlangan profillar ro'yxati | `steam-auto-run --list-profiles` |
| So'nggi ishga tushirish jurnalini ko'rsatish | `steam-auto-run --last-log [APPID]` |
| VR ishga tushirish muhitini oldindan ko'rish | `vr-run --dry-run` |
| Tarmoq yordamchisini tekshirish (faqat o'qish) | `steam-net-boost status [IFACE]` |

### Saqlangan `.env` profil kalitlari va muhit o'zgaruvchilari

Profil fayllari `~/.config/steam-auto-profiler/profiles/<APPID>.env` manzilida saqlanadi va ruxsat etilgan `KEY=VALUE` formatini qabul qiladi (qobiq buyruqlarini almashtirish va noma'lum kalitlar xavfsiz e'tiborsiz qoldiriladi):

| `.env` kaliti | Muhit o'zgaruvchisi | Ta'siri |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Nativ Wine Wayland o'rniga XWayland dan majburiy foydalanish |
| `USE_FSR4=0` | `FSR4=0` | Drayver darajasidagi FSR 4 yangilanishini o'chirish (sukut bo'yicha `1`) |
| `USE_MLFG=1` | `MLFG=1` | Kadr generatsiyasini yoqish (Anti-Lag, past kechikish va VRR cheklovlarini o'chiradi) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | OptiScaler ko'prigini yoqish (`competitive-anticheat` uchun himoya bilan o'chiriladi) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | vkBasalt keskinlashtirishini yoqish (FSR 4 yoki OptiScaler faol bo'lganda o'chadi) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Eksperimental `VKD3D_CONFIG` bayroqlari va `vkd3dbindlesstb` tokenini o'tkazib yuborish |
| `USE_NET_OPT=1` | `NETOPT=1` | `steam-net-boost` orqali sessiya tarmoq QoS ni faollashtirish |
| `USE_SDL=1` | `SDL=1` | Nativ SDL / Steam Input emulyatsiyasiga ustuvorlik berish |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Steam Overlay uchun `LD_PRELOAD` ni saqlab qolish |
| `USE_CEF_FIX=1` | `CEF=1` | CEF ishga tushirgichlari uchun `--in-process-gpu` qo'shish |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Eski o'yinlar uchun NTSync ni o'chirish |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Oyna menejeri bezaklarini o'chirish |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Maxsus DXVK/VKD3D kadr cheklovi (`0` cheklovni o'chiradi) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Monitor yangilanish chastotasidan `-6%` zaxira qo'llash (mas., 240 Hz da `225 FPS`) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Wine Wayland ostida tugma birikmalarini bloklashga ruxsat berish (sukut bo'yicha `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Ishga tushganda KDE Plasma 6 HDR ni avto-yoqish va chiqishda SDR ni tiklash |
| — | `BENCH=1`, `BENCH_DURATION=60` | Yashirin MangoHud CSV benchmarkini ishga tushirish va JSON xulosani saqlash |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Ishga tushirishdan oldingi `kdialog`/`zenity` tekshiruv oynasini yashirish yoki majburiy ochish |
| — | `FSR_HUD=1` | FSR/DLSS/MLFG HUD indikator o'zgaruvchilarini eksport qilish |
| — | `VULKAN=1` / `PRIME=1` | `-vulkan` qo'shish / `prime-run` bilan o'rash |
| — | `GAMEID=umu-<appid>` | UMU / Lutris / Heroic AppID larini aniqlash |

---

## Lutris, Heroic, Faugus va UMU

- **Lutris:** kengaytirilgan sozlamalarni yoqing, `proton-cachyos-slr` (yoki o'z Proton yig'ilmangizni) tanlang, Lutris runtime ni o'chiring, tizim kutubxonalariga ustuvorlik bering va buyruq prefiksini `steam-auto-run` qilib belgilang.
- **Heroic / Faugus:** `proton-cachyos-slr` ni tanlang va o'rama / buyruq prefiksi sifatida `steam-auto-run` qo'shing.
- **UMU / Protonfixes:** zarur bo'lganda `PROTON_VERB=waitforexitandrun` va `GAMEID=umu-<appid>` eksport qiling.

---

## Muammolarni bartaraf etish

- **Wayland yoki DX12 da tez qulash:** `steam-auto-ui` da **Logs & Recovery** ni oching (yoki `steam-auto-run --last-log APPID` ni ishga tushiring) va Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) ni qo'llang, yoki `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%` orqali ishga tushiring.
- **Anti-cheat li o'yinlar ishga tushmayapti:** `proton-cachyos-slr` (Steam Linux Runtime) dan foydalaning hamda EAC v2, `/dev/ntsync` va `vm.max_map_count` ni tekshirish uchun `steam-auto-run --doctor` ni ishga tushiring.
- **Steam ishga tushirish parametrlarini qaytarib qo'ymoqda:** `steam-auto-sync` yoki `steam-auto-sync --sanitize` ni ishga tushirishdan oldin Steam ni to'liq yoping.
- **Noto'g'ri yoki yo'q VRR cheklovi:** `VRR_CAP=<fps>` ni aniq ko'rsating, o'chirish uchun `VRR_CAP=0` yoki `-6%` zaxira uchun `VRR_MINUS_MARGIN=1` qo'ying. Gamescope da DXVK/VKD3D cheklovlari faqat aniq `VRR_CAP` berilgandagina eksport qilinadi.
- **Tarmoq QoS tekshiruvi:** `steam-net-boost status` ni bajaring (imtiyozsiz, faqat o'qish). Avtomatik sessiya QoS kerak bo'lsa, `./install.sh --with-net-boost` bilan tizim yordamchisini o'rnating.

---

## v2.1 yangiliklari (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 va Steam Controller 2026)

- **Mesa 27.0 / RDNA 4 bayroqlari:** `TRANSFER_QUEUE=1` (RDNA 3/4 uchun takrorlanmas `RADV_PERFTEST=sam,transfer_queue`), `NATIVE_ANTILAG=1` (nativ `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, anti-cheat va MLFG da bloklanadi) hamda `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** anti-cheatsiz o'yinlar uchun eksperimental stek (`VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1` va `WAYLANDDRV_RAWINPUT=1` faqat Gamescope tashqarisidagi nativ Waylandda).
- **Hunt: Showdown 1896 (`AppID 594650`) himoyasi:** `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, `USE_NET_OPT=1` majburlaydi; `--doctor` va `steam-auto-ui` `config.vdf` da `Proton 11.0-2` / `Proton Hotfix` ni tekshiradi.
- **Steam Controller 2026 / Wireless Puck (`28de:{1302,1304,1005,1007}`):** 4 rejim (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` nativ Wayland + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`) ni saqlaydi, `steam://forceinputappid/<APPID>` va `udevadm` qayta ulanish kuzatuvchisini ishga tushiradi va chiqishda `steam://forceinputappid/0` ga qaytaradi. Qo'lda: `steam-auto-run --reapply-input <APPID|0>`; udev: `./install.sh --with-steam-controller`.

---

Shuningdek, [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) (ichki arxitektura) va barcha 27 ta mahalliylashtirilgan qo'llanmalar uchun [i18n Index](../README.md) ga qarang.
