# Steam Auto-Profiler — Օգտատիրոջ ուղեցույց

> [English User Guide](../../USER_GUIDE.md) · [i18n Index](../README.md)

Այս ուղեցույցն ընդգրկում է **Steam Auto-Profiler v2.0**-ի ամբողջական տեղադրումը, սովորական էկրանի (flatscreen) և VR խաղերի գործարկման կազմակերպումը, `steam-auto-ui` կառավարման կենտրոնը, գրադարանի համաժամեցումը, արտադրողականության չափումը և անսարքությունների վերացումը։

Steam Auto-Profiler-ը Linux-ի համար նախատեսված թեթև Bash/Python գործարկիչ և կառավարման կենտրոն է, որը ստուգում է Steam AppID-ն (կամ ոչ Steam դյուրանցումը), կիրառում է համատեքստից կախված պրոֆիլ՝ դրայվերի, մասշտաբավորման (upscaler) և հակախաբեության (anti-cheat) խիստ պաշտպանիչ մեխանիզմներով, և գործարկում խաղի առկա հրամանը։ Այն երբեք չի ներառում կամ ներարկում երրորդ կողմի Proton միջավայր։

---

## Պահանջներ

- Linux աշխատասեղանի սեսիա (KDE Plasma 6 / Wayland, GNOME, wlroots կամ X11), Bash 5+, Python 3.10+, Steam և համակարգային հիմնական գործիքներ։
- Կամընտրական բնիկ կառավարման կենտրոնի GUI՝ `PyQt6` կամ `PySide6` (բացակայության դեպքում ավտոմատ կերպով անցնում է առանց արտաքին կախվածությունների ստանդարտ գրադարանի `curses` TUI-ին)։
- Կամընտրական նախագործարկման ստուգաթերթի երկխոսության պատուհաններ՝ `kdialog` կամ `zenity`։
- Կամընտրական անաղմուկ կադրերի ժամանակի (frametime) չափում՝ `mangohud`։
- Կամընտրական սեսիայի ցանցային օգնական՝ `tc`, `ip` և `ethtool` (`sudo`-ն անհրաժեշտ է միայն `--with-net-boost` տեղադրման ժամանակ)։

---

## Տեղադրում և թարմացումներ

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh`-ը բոլոր վեց գործարկվող ֆայլերը (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` և `steam-auto-ui`) պատճենում է `~/.local/bin` պանակում, տեղադրում աշխատասեղանի դյուրանցումը (`~/.local/share/applications/steam-auto-profiler.desktop`), ստեղծում `~/.config/steam-auto-profiler/profiles` պանակը և ավելացնում vkBasalt-ի սկզբնական նախադրումները (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`)։ Համոզվեք, որ `~/.local/bin`-ը ներառված է `PATH`-ում։

Տեղադրման լրացուցիչ դրոշակները կարելի է համադրել․

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`․ տեղադրում է `/usr/local/bin/steam-net-boost`-ը (ինչպես նաև մյուս սկրիպտների համակարգային պատճենները) և նեղ սահմանափակված առանց գաղտնաբառի sudoers կանոն `steam-net-boost`-ի համար։
- `--compat-cachy-run`․ պահպանում է առկա `/usr/local/bin/cachy-run`-ը որպես `/usr/local/bin/cachy-run.bak` (եթե այն արդեն Steam Auto-Profiler-ի փոխանցող շերտը չէ) և տեղադրում է `steam-auto-run`-ին ուղղորդող shim։
- `--with-auto-sync` (`--enable-auto-sync`)․ տեղադրում և միացնում է օգտատիրոջ systemd `steam-auto-profiler-sync.path` դիտորդը և համապատասխան մեկանգամյա ծառայությունը բոլոր հայտնաբերված Steam գրադարանների համար։
- `--uninstall`․ հեռացնում է տեղադրված գործարկվող ֆայլերը, աշխատասեղանի դյուրանցումը, լրացուցիչ ցանցային օգնականը և sudoers կանոնը, համատեղելիության shim-ը և օգտատիրոջ systemd auto-sync միավորները։

Առկա տարբերակը թարմացնելու համար․

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Ստուգեք համակարգի պատրաստվածությունը խաղերը համաժամեցնելուց առաջ․

```bash
steam-auto-run --doctor
```

---

## Գործարկման ամբողջական խողովակաշար

1. **AppID-ի որոշում․** Հերթականությամբ ստուգում է `SteamAppId`, `STEAM_COMPAT_APP_ID`, ապա `GAMEID` փոփոխականները (հեռացնելով `umu-` նախածանցը Lutris/Heroic/UMU-ի համար)։
2. **Գրադարանի և դյուրանցումների հայտնաբերում․** `steam-auto-detect`-ը որոնում է Steam-ի արմատային և լրացուցիչ գրադարանները `libraryfolders.vdf`-ում, կարդում է `appmanifest_<APPID>.acf`-ը կամ միայն ընթերցման ռեժիմով դիմում է երկուական `userdata/*/config/shortcuts.vdf` ֆայլին, այնուհետև կատարում է մեկ անցումով `find` մինչև 10 մակարդակ խորությամբ (բացառելով `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization` պանակները)։
3. **Հինգ մակարդակի դասակարգման առաջնահերթություն․**
   - **1. `competitive-anticheat`․** Հայտնի մրցակցային AppID կամ հայտնաբերված հակախաբեության համակարգ (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE և այլն)։ Անջատում է OptiScaler-ը, MLFG-ն, vkBasalt-ը և ասինխրոն DXVK-ն, միացնում է ցածր ուշացման ռեժիմը և սեսիայի ցանցային QoS-ը։
   - **2. `vr`․** Հայտնաբերված `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` կամ `vr-run`/`-vr` դյուրանցման դրոշակներ։ Արտահանում է `AUTO_IS_VR=1`։
   - **3. `native-fsr4` / `native-fsr`․** Մոդուլային FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`)։ Միացնում է դրայվերի մակարդակի FSR 4 թարմացումը (`PROTON_FSR4_UPGRADE=1` կամ `PROTON_FSR4_RDNA3_UPGRADE=1` AMD RDNA 3-ի վրա)։
   - **4. `legacy-upscaler`․** Հին DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) կամ FSR 2/3.0 DLL-ներ։ Նշում է `AUTO_OPTISCALER=1` և սահմանում `AUTO_UPSCALER_INFO` ուղղորդիչ տեղեկությունը։
   - **5. `standard`․** Անվտանգ բնիկ Wine Wayland + ցածր ուշացման VRR պրոֆիլ։
4. **VRR թարմացման հաճախականության սահմանափակում․** Բացահայտ սահմանված `VRR_CAP=<fps>` արժեքը միշտ գերակայում է (`VRR_CAP=0`-ը անջատում է սահմանափակումը)։ Հակառակ դեպքում ակտիվ էկրանի թարմացման հաճախականությունը որոշվում է `kscreen-doctor` (KDE Plasma 6-ի ակտիվ `*` ռեժիմ կամ ավանդական `Hz`), `wlr-randr` կամ `xrandr` գործիքներով և լռելյայն կիրառվում է 1:1 հարաբերակցությամբ (`240 FPS`՝ 240 Հց էկրանին)։ Միացրեք `VRR_MINUS_MARGIN=1`-ը՝ լրացուցիչ `-6%` VRR անվտանգության պաշար կիրառելու համար (`hz * 94 / 100`, օրինակ՝ `225 FPS`՝ 240 Հց-ի դեպքում)։ Gamescope սեսիաներում DXVK/VKD3D սահմանափակումները բաց են թողնվում, եթե `VRR_CAP`-ը բացահայտ նշված չէ։
5. **Փոխադարձ բացառման պաշտպանիչ կանոններ․**
   - **FSR 4 / OptiScaler + vkBasalt․** `ENABLE_VKBASALT=0`-ը պարտադրվում է ամեն անգամ, երբ ակտիվ է `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` կամ `USE_OPTISCALER=1` (կանխում է կրկնակի սրացումը և HDR10-ի կտրատումը)։
   - **MLFG + ցածր ուշացում / VRR սահմանափակումներ․** `MLFG=1`-ը (`USE_MLFG=1`) արտահանում է `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, մաքրում է `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` և `DXVK_FRAME_PACE` փոփոխականները և AMD RDNA 3-ի վրա արտահանում `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`։ Երբ `USE_MLFG=0` է և VRR սահմանափակումը միացված է, արտահանվում է `DXVK_FRAME_PACE=low-latency-vrr`։
   - **Ժամանակակից DX12 + Safe DX12․** AMD-ի վրա արտահանում է `PROTON_NATIVE_AGS=1`, իսկ երբ `USE_SAFEDX12=0` է՝ նաև `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` (մաքուր կերպով բաց է թողնվում, երբ `SAFEDX12=1`)։
6. **Համատեղելիության տոկենների (compat-tokens) քարտեզագրում․** Կառավարվող գործառույթները ավելացվում են առանց օգտատիրոջ առկա արժեքները ջնջելու՝ թե՛ `PROTON_ADD_CONFIG`, թե՛ `STEAM_COMPAT_CONFIG` փոփոխականներում՝ `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`։
7. **Ավտոմատ KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`)․** Երբ միացված է Gamescope-ից դուրս՝ `DXVK_HDR=1` (կամ `USE_HDR=1`) արժեքով, ստուգում է հիմնական ակտիվ էկրանը `kscreen-doctor -o`-ի միջոցով․ եթե HDR-ն անջատված է, միացնում է այն գործարկումից առաջ և վերականգնում SDR-ը `EXIT`/`INT`/`TERM` թակարդում (trap)։
8. **Անաղմուկ կադրերի ժամանակի չափում (`BENCH=1`)․** Գործարկում է MangoHud-ը թաքնված CSV ռեժիմում (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), խաղի ավարտից հետո վերլուծում է կադրերի ժամանակները, ավելացնում `Avg FPS`, `1% Low FPS` և `P99 (ms)` ցուցանիշները `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` ֆայլում և հեռացնում ժամանակավոր CSV ֆայլերը։
9. **Արագ վթարի անվտանգ ռեժիմի (Safe Mode) ավտոմատ վերականգնում․** Եթե Proton/Windows խաղն ավարտվում է ոչ զրոյական կոդով `20s`-ից պակաս ժամանակում (կարգավորելի է `SAP_CRASH_THRESHOLD_SEC`-ով), մինչ ակտիվ են փորձարարական Wayland կամ DX12 դրոշակները (`USE_XWAYLAND=0` կամ `USE_SAFEDX12=0`), գրանցում է `crash_hint` տեղեկություն `last-<APPID>.log` և `last-launch.log` ֆայլերում և (երբ GUI-ն ակտիվ է) առաջարկում է պահպանել `USE_XWAYLAND=1` + `USE_SAFEDX12=1` հաջորդ գործարկման համար։
10. **Պլանավորիչի և ցանցի կենսացիկլ․** Աշխատում է `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (միայն երբ `ananicy-cpp.service`-ն ակտիվ չէ) -> ուղիղ գործարկում շղթայով, կամընտրական `PRIME=1` (`prime-run`) աջակցությամբ։ Եթե `USE_NET_OPT=1`, `steam-net-boost`-ը կատարում է հղումների հաշվարկով `on`/`off` անցում՝ `flock` կողպմամբ, պահպանելով ստատիկ root CAKE և HTB + leaf CAKE հերթերի հիերարխիաները։

---

## Միասնական կառավարման կենտրոն (`steam-auto-ui`)

Գործարկեք `steam-auto-ui`-ը աշխատասեղանի հավելվածների ընտրացանկից, `steam-auto-run --ui` հրամանով կամ ուղիղ․

```bash
steam-auto-ui                 # Ավտոմատ ընտրում է Qt6 GUI (PyQt6/PySide6) կամ curses TUI
steam-auto-ui --gui           # Պարտադրել բնիկ Qt6 GUI պատուհան
steam-auto-ui --tui           # Պարտադրել ստանդարտ գրադարանի curses TUI (աշխատում է SSH-ով)
steam-auto-ui --lang hy       # Գործարկել ընտրված UI լեզվով (աջակցվում է 27 լեզու)
steam-auto-ui --check         # Կատարել առանց էկրանի ինքնաստուգում (տպում է JSON ախտորոշում)
```

`steam-auto-ui`-ն ավտոմատ կերպով հայտնաբերում է համակարգի լոկալը `LC_ALL` / `LC_MESSAGES` / `LANG` փոփոխականներից և ապահովում է լեզվի ակնթարթային ընտրիչ Qt6 GUI-ում (և `L` ստեղնը `curses` TUI-ում)՝ բոլոր 27 լեզուների միջև առանց վերագործարկման անցնելու համար։

### Հինգ համաժամեցված դիտումներ

1. **Games & Profiles․** Steam խաղերի և միայն ընթերցման ոչ Steam `shortcuts.vdf` գրառումների զտվող աղյուսակ (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), Upscaler SDK նշան (`AUTO_UPSCALER_INFO`), փոխադարձ բացառման կենդանի ստուգում բոլոր 10 պրոֆիլի անջատիչների + `VRR_CAP`-ի վրա, `Dry-Run Preview`, `Benchmarks` անցման կոճակ և `Reset Profile`։
2. **System & Telemetry․** Անարգել կենդանի ցուցադրում՝ `steam-auto-run --doctor`, `scxctl get` / `sched_ext` վիճակ, տեղադրված բաղադրիչների տարբերակներ (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), շեյդերների քեշի ծավալ (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` git/AUR տարբերակի իջեցման զգուշացումներ, GPU VRAM/ծանրաբեռնվածություն/ջերմաստիճան, `tc -s qdisc` LAN (`10:`) և WAN (`20:`/root) թողունակություն ու `av_delay`, ինչպես նաև `vr-mode status`։
3. **Library Sync․** Steam-ի գործարկված լինելու կենդանի պաշտպանիչ զգուշացում, ինչպես նաև մեկ սեղմումով `--report`, `--sanitize --dry-run`, `--sanitize` (մերժվում է, քանի դեռ Steam-ն աշխատում է) և `--migrate-cachy-run`։
4. **Logs & Recovery․** Դիտեք `last-launch.log` և `last-<APPID>.log` մատյանները, ստուգեք `crash_hint` ահազանգերը և մեկ սեղմումով կիրառեք Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`)։
5. **Benchmarks․** `BENCH=1` կադրերի ժամանակի թեստերի զտվող համեմատական աղյուսակ (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`)։

---

## VR կազմակերպում (`vr-run`)

VR խաղերի համար Steam-ում **Հատկություններ > Ընդհանուր > Գործարկման ընտրանքներ** դաշտում սահմանեք․

```text
vr-run %command%
```

- Մաքրում է ժառանգված flatscreen վերասահմանումները (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`)։
- Ավտոմատ ընտրում է ամենամեծ VRAM-ով առանձին (discrete) GPU-ն՝ `MESA_VK_DEVICE_SELECT`-ով, և AMD GPU-ների վրա սահմանում է `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`։
- Դինամիկորեն հայտնաբերում է WiVRn և xrizer OpenXR/OpenVR ուղիները (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) և կարգավորում է `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` և `LD_LIBRARY_PATH`՝ չվերագրանցելով օգտատիրոջ բացահայտ կարգավորումները։
- Կատարում է `vr-mode on` / `vr-mode off` հղումների հաշվարկ `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` ֆայլում (`flock`-ով), երբ տեղադրված է `vr-mode` (`VR_AUTO_MODE=0`-ը անջատում է այն)։
- Աշխատում է նույն `ananicy-cpp`-ն հաշվի առնող պլանավորիչի շղթայով (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> ուղիղ `exec`)։
- Ցանկացած պահի նախադիտեք որոշված փոփոխականները `vr-run --dry-run` հրամանով։

`steam-auto-run`-ը ավտոմատ կերպով շրջանցում է SteamVR-ը (`250820`) և `-vr`/`--vr` գործարկումները, իսկ `steam-auto-sync`-ը ավտոմատ նշանակում և պահպանում է `vr-run %command%`-ը VR խաղերի համար։

---

## Steam գրադարանի համաժամեցում (`steam-auto-sync`)

Ամբողջությամբ փակեք Steam-ը նախքան `localconfig.vdf`-ում փոփոխություններ գրելը․

```bash
steam-auto-sync --report              # Միայն ընթերցման աուդիտ՝ գրադարան + shortcuts.vdf
steam-auto-sync --print-library-paths # Ցույց տալ հայտնաբերված բոլոր Steam գրադարանները
steam-auto-sync --dry-run             # Նախադիտել փոփոխությունները
steam-auto-sync                       # Ներդնել steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Նախադիտել հին դրոշակների մաքրումը
steam-auto-sync --sanitize            # Մաքրել խառը/որբ դրոշակները (հոմանիշ՝ --clean)
steam-auto-sync --migrate-cachy-run   # Տեղափոխել հին cachy-run պրոֆիլները
steam-auto-sync --remove              # Հեռացնել steam-auto-run փաթաթիչը
```

- Ժամանակային դրոշմով `localconfig.vdf.bak.*` պահուստային պատճենները ավտոմատ մաքրվում են `--keep-backups N` պարամետրով (լռելյայն՝ `10`, `0`-ը պահում է բոլորը)։
- Որոշակի AppID-ներ բացառելու համար թվարկեք դրանք (յուրաքանչյուր տողում մեկը, `#` մեկնաբանությունները թույլատրվում են) `~/.config/steam-auto-profiler/ignore_appids.txt` ֆայլում։
- Systemd auto-sync դիտորդը (`./install.sh --with-auto-sync` կամ `steam-auto-sync --install-systemd`) գործարկում է `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`, երբ Steam-ի մանիֆեստները փոխվում են։

---

## CLI և պրոֆիլների տեղեկատու

### Հրամաններ

| Նպատակ | Հրաման |
| --- | --- |
| Համակարգի պատրաստվածության ստուգում | `steam-auto-run --doctor` (հոմանիշ՝ `--check-system`) |
| Գործարկել կառավարման կենտրոնը (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` կամ `steam-auto-run --ui` |
| Ստուգել խաղը (ընթեռնելի ձևաչափ) | `steam-auto-run --inspect APPID` |
| Ստուգել խաղը (JSON) | `steam-auto-detect --inspect --json APPID` |
| Ինտերակտիվ վերակարգավորել պրոֆիլը | `steam-auto-run --configure APPID` |
| Նախադիտել գործարկման միջավայրը | `steam-auto-run --dry-run APPID` |
| Վերակայել պահպանված պրոֆիլը | `steam-auto-run --reset APPID` |
| Ցուցակագրել պահպանված պրոֆիլները | `steam-auto-run --list-profiles` |
| Ցույց տալ վերջին գործարկման մատյանը | `steam-auto-run --last-log [APPID]` |
| Նախադիտել VR գործարկման միջավայրը | `vr-run --dry-run` |
| Ստուգել ցանցային օգնականը (միայն ընթերցում) | `steam-net-boost status [IFACE]` |

### Պահպանված `.env` պրոֆիլի բանալիներ և միջավայրի վերասահմանումներ

Պրոֆիլի ֆայլերը պահվում են `~/.config/steam-auto-profiler/profiles/<APPID>.env` հասցեում և ընդունում են թույլատրված ցանկով `KEY=VALUE` ձևաչափ (shell հրամանների փոխարինումները և անհայտ բանալիներն անվտանգ կերպով անտեսվում են)․

| `.env` բանալի | Միջավայրի վերասահմանում | Ազդեցություն |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Պարտադրել XWayland՝ բնիկ Wine Wayland-ի փոխարեն |
| `USE_FSR4=0` | `FSR4=0` | Անջատել դրայվերի մակարդակի FSR 4 թարմացումը (լռելյայն՝ `1`) |
| `USE_MLFG=1` | `MLFG=1` | Միացնել կադրերի գեներացիան (անջատում է Anti-Lag-ը, ցածր ուշացումը և VRR սահմանափակումները) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Միացնել OptiScaler կամուրջը (արգելափակված է `competitive-anticheat`-ի համար) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Միացնել vkBasalt սրացումը (անջատվում է, երբ ակտիվ է FSR 4-ը կամ OptiScaler-ը) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Բաց թողնել փորձարարական `VKD3D_CONFIG` դրոշակները և `vkd3dbindlesstb` տոկենը |
| `USE_NET_OPT=1` | `NETOPT=1` | Ակտիվացնել սեսիայի ցանցային QoS-ը `steam-net-boost`-ով |
| `USE_SDL=1` | `SDL=1` | Նախընտրել բնիկ SDL / Steam Input էմուլյացիան |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Պահպանել Steam Overlay-ի `LD_PRELOAD`-ը |
| `USE_CEF_FIX=1` | `CEF=1` | Ավելացնել `--in-process-gpu` CEF գործարկիչների համար |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Անջատել NTSync-ը հին խաղերի համար |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Անջատել պատուհանների կառավարչի եզրագծերը |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Ընտրովի DXVK/VKD3D կադրերի սահմանաչափ (`0`-ն անջատում է) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Կիրառել `-6%` պաշար մոնիտորի հաճախականությունից (օր.՝ `225 FPS`՝ 240 Հց-ում) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Թույլատրել դյուրանցումների արգելափակումը Wine Wayland-ում (լռելյայն՝ `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Ավտոմատ միացնել KDE Plasma 6 HDR-ը գործարկման ժամանակ և վերականգնել SDR-ը դուրս գալիս |
| — | `BENCH=1`, `BENCH_DURATION=60` | Գործարկել անաղմուկ MangoHud CSV չափում և պահպանել JSON ամփոփագիրը |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Թաքցնել կամ հարկադրաբար բացել նախագործարկման `kdialog`/`zenity` ստուգաթերթը |
| — | `FSR_HUD=1` | Արտահանել FSR/DLSS/MLFG HUD ցուցիչների փոփոխականները |
| — | `VULKAN=1` / `PRIME=1` | Ավելացնել `-vulkan` / փաթաթել `prime-run`-ով |
| — | `GAMEID=umu-<appid>` | Որոշել UMU / Lutris / Heroic AppID-ները |

---

## Lutris, Heroic, Faugus և UMU

- **Lutris․** Միացրեք ընդլայնված կարգավորումները, ընտրեք `proton-cachyos-slr` (կամ ձեր Proton տարբերակը), անջատեք Lutris runtime-ը, նախընտրեք համակարգային գրադարանները և հրամանի նախածանցը (command prefix) սահմանեք `steam-auto-run`։
- **Heroic / Faugus․** Ընտրեք `proton-cachyos-slr` և որպես wrapper/հրամանի նախածանց ավելացրեք `steam-auto-run`։
- **UMU / Protonfixes․** Անհրաժեշտության դեպքում արտահանեք `PROTON_VERB=waitforexitandrun` և `GAMEID=umu-<appid>`։

---

## Անսարքությունների վերացում

- **Արագ վթար Wayland-ի կամ DX12-ի վրա․** Բացեք **Logs & Recovery** բաժինը `steam-auto-ui`-ում (կամ գործարկեք `steam-auto-run --last-log APPID`) և կիրառեք Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), կամ գործարկեք `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`։
- **Հակախաբեության համակարգով խաղերը չեն գործարկվում․** Օգտագործեք `proton-cachyos-slr` (Steam Linux Runtime) և գործարկեք `steam-auto-run --doctor`՝ ստուգելու EAC v2-ը, `/dev/ntsync`-ը և `vm.max_map_count`-ը։
- **Steam-ը հետ է բերում գործարկման ընտրանքները․** Ամբողջությամբ փակեք Steam-ը նախքան `steam-auto-sync` կամ `steam-auto-sync --sanitize` գործարկելը։
- **Սխալ կամ բացակայող VRR սահմանափակում․** Բացահայտ սահմանեք `VRR_CAP=<fps>`, `VRR_CAP=0`՝ անջատելու համար, կամ `VRR_MINUS_MARGIN=1`՝ `-6%` պաշարի համար։ Gamescope-ում միայն բացահայտ `VRR_CAP`-ն է արտահանում DXVK/VKD3D սահմանափակումները։
- **Ցանցային QoS-ի ստուգում․** Գործարկեք `steam-net-boost status` (առանց արտոնությունների, միայն ընթերցում)։ Եթե ցանկանում եք ավտոմատ սեսիայի QoS, տեղադրեք root օգնականը `./install.sh --with-net-boost` հրամանով։

Ճարտարապետության մանրամասների համար տես [ARCHITECTURE.md](../../ARCHITECTURE.md), անգլերեն հիմնական ուղեցույցի համար՝ [English User Guide](../../USER_GUIDE.md), իսկ բոլոր 27 լեզուների համար՝ [i18n Index](../README.md)։
