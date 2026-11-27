# Používateľská príručka Steam Auto-Profiler

> 🌐 [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Táto príručka pokrýva kompletnú inštaláciu, orchestráciu spúšťania klasických aj VR hier, ovládacie centrum `steam-auto-ui`, synchronizáciu knižnice, meranie výkonu a riešenie problémov pre **Steam Auto-Profiler v2.0**.

Steam Auto-Profiler je ľahký spúšťač a ovládacie centrum v Bash/Pythone pre Linux, ktorý skontroluje Steam AppID (alebo zástupcu hry mimo Steam), použije kontextový profil s prísnymi ochrannými pravidlami pre ovládače, upscalery a anti-cheat a spustí pôvodný príkaz hry. Nikdy nepribaľuje ani nevkladá externé behové prostredie Proton.

---

## Požiadavky

- Linuxová desktopová relácia (KDE Plasma 6 / Wayland, GNOME, wlroots alebo X11), Bash 5+, Python 3.10+, Steam a štandardné systémové nástroje.
- Voliteľné natívne GUI ovládacieho centra: `PyQt6` alebo `PySide6` (inak sa automaticky prepne do `curses` TUI zo štandardnej knižnice bez externých závislostí).
- Voliteľné predspúšťacie dialógy: `kdialog` alebo `zenity`.
- Voliteľné tiché meranie frametime (benchmarking): `mangohud`.
- Voliteľný sieťový pomocník relácie: `tc`, `ip` a `ethtool` (`sudo` je potrebné len počas inštalácie s voľbou `--with-net-boost`).

---

## Inštalácia a aktualizácie

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

Skript `./install.sh` skopíruje všetkých šesť spustiteľných súborov (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` a `steam-auto-ui`) do `~/.local/bin`, nainštaluje zástupcu pracovnej plochy (`~/.local/share/applications/steam-auto-profiler.desktop`), vytvorí adresár `~/.config/steam-auto-profiler/profiles` a pridá predvolené presety vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Uistite sa, že adresár `~/.local/bin` je v premennej `PATH`.

Voliteľné prepínače inštalátora možno kombinovať:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: nainštaluje `/usr/local/bin/steam-net-boost` (spolu so systémovými kópiami ostatných skriptov) a úzko vymedzené pravidlo sudoers bez hesla pre `steam-net-boost`.
- `--compat-cachy-run`: zálohuje existujúci `/usr/local/bin/cachy-run` ako `/usr/local/bin/cachy-run.bak` (ak už nejde o presmerovaciu vrstvu Steam Auto-Profiler) a nainštaluje presmerovanie na `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): nainštaluje a povolí používateľskú jednotku systemd `steam-auto-profiler-sync.path` spolu s prislúchajúcou oneshot službou pre všetky objavené knižnice Steam.
- `--uninstall`: odstráni nainštalované spustiteľné súbory, záznam plochy, voliteľný sieťový pomocník a pravidlo sudoers, vrstvu kompatibility a používateľské jednotky auto-synchronizácie systemd.

Aktualizácia existujúcej kópie repozitára:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Pred synchronizáciou hier overte pripravenosť systému:

```bash
steam-auto-run --doctor
```

---

## Kompletný spúšťací reťazec (End-to-End)

1. **Rozpoznanie AppID:** Kontroluje `SteamAppId`, `STEAM_COMPAT_APP_ID` a potom `GAMEID` (odstráni prípadnú predponu `umu-` pre Lutris/Heroic/UMU).
2. **Zisťovanie knižníc a zástupcov:** `steam-auto-detect` prehľadá koreňové priečinky Steam aj sekundárne knižnice v `libraryfolders.vdf`, načíta `appmanifest_<APPID>.acf`, prípadne v režime len na čítanie prečíta binárny súbor `userdata/*/config/shortcuts.vdf`, a vykoná jednopriechodové hľadanie `find` do hĺbky 10 úrovní (s vynechaním `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Päťstupňová priorita klasifikácie:**
   - **1. `competitive-anticheat`:** Známe súťažné AppID alebo zistený anti-cheat runtime (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE atď.). Vypne OptiScaler, MLFG, vkBasalt a asynchrónny DXVK; zapne nízku latenciu a sieťový QoS relácie.
   - **2. `vr`:** Zistené súbory `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` alebo prepínače zástupcu `vr-run`/`-vr`. Exportuje `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modulárny FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Zapne upgrade FSR4 na úrovni ovládača (`PROTON_FSR4_UPGRADE=1` alebo `PROTON_FSR4_RDNA3_UPGRADE=1` na AMD RDNA 3).
   - **4. `legacy-upscaler`:** Staršie DLL knižnice DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) alebo FSR 2/3.0. Nastaví `AUTO_OPTISCALER=1` a odporúčania v `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Bezpečný profil s natívnym Wine Wayland a VRR s nízkou latenciou.
4. **Obmedzenie snímok pre VRR:** Explicitné `VRR_CAP=<fps>` má vždy prednosť (`VRR_CAP=0` limit vypína). Inak sa aktívna obnovovacia frekvencia monitora zistí cez `kscreen-doctor` (aktívny režim `*` v KDE Plasma 6 alebo starší `Hz`), `wlr-randr` či `xrandr` a predvolene sa uplatní v pomere 1:1 (`240 FPS` pri 240 Hz). Zapnutím `VRR_MINUS_MARGIN=1` pridáte voliteľnú bezpečnostnú rezervu VRR `-6%` (`hz * 94 / 100`, napr. `225 FPS` pri 240 Hz). V reláciách Gamescope sa limity DXVK/VKD3D vynechávajú, pokiaľ `VRR_CAP` nie je zadané explicitne.
5. **Ochranné pravidlá vzájomného vylúčenia:**
   - **FSR 4 / OptiScaler + vkBasalt:** Vždy vynúti `ENABLE_VKBASALT=0`, keď je aktívne `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` alebo `USE_OPTISCALER=1` (zabraňuje dvojitému doostrovaniu a orezaniu HDR10).
   - **MLFG + nízka latencia / limity VRR:** `MLFG=1` (`USE_MLFG=1`) exportuje `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, zruší `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` a `DXVK_FRAME_PACE` a na AMD RDNA 3 exportuje `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. Keď je `USE_MLFG=0` a VRR limit je aktívny, exportuje sa `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Moderný DX12 + Safe DX12:** Na AMD exportuje `PROTON_NATIVE_AGS=1` a pri `USE_SAFEDX12=0` aj `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` (pri `SAFEDX12=1` čisto vynechané).
6. **Mapovanie tokenov kompatibility:** Spravované funkcie sa bez prepísania existujúcich používateľských hodnôt pripoja do `PROTON_ADD_CONFIG` aj `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Automatické HDR v KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Ak je zapnuté mimo Gamescope spolu s `DXVK_HDR=1` (alebo `USE_HDR=1`), zistí primárny aktívny výstup pomocou `kscreen-doctor -o`; ak je HDR vypnuté, zapne ho pred spustením a v obsluhe `EXIT`/`INT`/`TERM` vráti späť SDR.
8. **Tiché meranie frametime (`BENCH=1`):** Spustí MangoHud v skrytom CSV režime (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), po ukončení spracuje frametime, pridá `Avg FPS`, `1% Low FPS` a `P99 (ms)` do `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` a vymaže dočasné CSV súbory.
9. **Automatická obnova do núdzového režimu po rýchlom páde:** Ak hra pod Proton/Windows skončí nenulovým návratovým kódom za menej než `20s` (nastaviteľné cez `SAP_CRASH_THRESHOLD_SEC`) pri zapnutých experimentálnych prepínačoch Wayland alebo DX12 (`USE_XWAYLAND=0` alebo `USE_SAFEDX12=0`), zapíše `crash_hint` do `last-<APPID>.log` a `last-launch.log` a pri aktívnom GUI ponúkne uloženie `USE_XWAYLAND=1` + `USE_SAFEDX12=1` pre ďalšie spustenie.
10. **Životný cyklus plánovača a siete:** Spúšťa cez reťazec `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (iba ak je `ananicy-cpp.service` neaktívna) -> priame spustenie, s voliteľným `PRIME=1` (`prime-run`). Ak je `USE_NET_OPT=1`, `steam-net-boost` vykonáva referenčne počítané `on`/`off` s `flock`, pričom zachováva statický koreňový CAKE a hierarchie HTB + listový CAKE.

---

## Jednotné ovládacie centrum (`steam-auto-ui`)

Spustite `steam-auto-ui` z ponuky aplikácií, príkazom `steam-auto-run --ui` alebo priamo:

```bash
steam-auto-ui                 # Automaticky zvolí Qt6 GUI (PyQt6/PySide6) alebo curses TUI
steam-auto-ui --gui           # Vynúti natívne okno Qt6 GUI
steam-auto-ui --tui           # Vynúti curses TUI zo stdlib (funguje cez SSH)
steam-auto-ui --lang fi       # Spustí s explicitným jazykom UI (podporovaných 27 jazykov)
steam-auto-ui --check         # Spustí bezhlavú samokontrolu (vypíše JSON diagnostiku)
```

`steam-auto-ui` automaticky rozpozná systémové locale z `LC_ALL` / `LC_MESSAGES` / `LANG` a v Qt6 GUI poskytuje rozbaľovací výber jazyka za behu (v `curses` TUI kláves `L`) na okamžité prepínanie medzi všetkými 27 jazykmi (vrátane `sk`) bez reštartu.

### Päť synchronizovaných pohľadov

1. **Hry a profily (Games & Profiles):** Filtrovateľná tabuľka titulov Steam a položiek mimo Steam len na čítanie zo `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), štítok upscaler SDK (`AUTO_UPSCALER_INFO`), živá validácia vzájomného vylúčenia pre všetkých 10 prepínačov profilu + `VRR_CAP`, náhľad `Dry-Run Preview`, tlačidlo na prechod do `Benchmarks` a `Reset Profile`.
2. **Systém a telemetria (System & Telemetry):** Neblokujúci živý výpis z `steam-auto-run --doctor`, stav `scxctl get` / `sched_ext`, verzie nainštalovaného stacku (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), využitie shader cache (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), upozornenia na downgrade git/AUR balíkov z `/var/log/pacman.log`, VRAM/vyťaženie/teplota GPU, priepustnosť a `av_delay` z `tc -s qdisc` pre LAN (`10:`) vs WAN (`20:`/root) a stav `vr-mode status`.
3. **Synchronizácia knižnice (Library Sync):** Živý ochranný banner stavu bežiaceho Steamu a jedno-klikové akcie `--report`, `--sanitize --dry-run`, `--sanitize` (odmietnuté, kým Steam beží) a `--migrate-cachy-run`.
4. **Logy a obnova (Logs & Recovery):** Prehliadanie `last-launch.log` a `last-<APPID>.log`, kontrola upozornení `crash_hint` a aktivácia núdzového režimu jedným kliknutím (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarky (Benchmarks):** Filtrovateľná porovnávacia tabuľka meraní frametime z `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Orchestrácia VR (`vr-run`)

Vo Steame nastavte **Vlastnosti > Všeobecné > Možnosti spustenia** pre VR tituly na:

```text
vr-run %command%
```

- Odstráni zdedené prepisy pre klasické monitory (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Automaticky vyberie dedikovanú GPU s najväčšou VRAM cez `MESA_VK_DEVICE_SELECT` a na AMD GPU nastaví `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`.
- Dynamicky zistí cesty OpenXR/OpenVR pre WiVRn a xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) a nakonfiguruje `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` a `LD_LIBRARY_PATH` bez prepísania explicitných používateľských nastavení.
- Referenčne počíta `vr-mode on` / `vr-mode off` v `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (s `flock`), ak je nainštalovaný `vr-mode` (`VR_AUTO_MODE=0` funkciu vypne).
- Používa rovnaký reťazec plánovača zohľadňujúci `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> priamy `exec`).
- Vyhodnotené premenné si môžete kedykoľvek prezrieť príkazom `vr-run --dry-run`.

`steam-auto-run` automaticky obchádza SteamVR (`250820`) a spustenia s `-vr`/`--vr`; `steam-auto-sync` pre VR tituly automaticky priraďuje a zachováva `vr-run %command%`.

---

## Synchronizácia knižnice Steam (`steam-auto-sync`)

Pred zápisom do `localconfig.vdf` Steam úplne ukončite:

```bash
steam-auto-sync --report              # Audit knižnice a shortcuts.vdf len na čítanie
steam-auto-sync --print-library-paths # Zobrazí všetky objavené knižnice Steam
steam-auto-sync --dry-run             # Náhľad úprav
steam-auto-sync                       # Vloží steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Náhľad čistenia starých prepínačov
steam-auto-sync --sanitize            # Vyčistí neplatné/osirelé prepínače (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migruje staršie profily cachy-run
steam-auto-sync --remove              # Odstráni obal steam-auto-run
```

- Zálohy `localconfig.vdf.bak.*` s časovou pečiatkou sa automaticky prerezávajú podľa `--keep-backups N` (predvolene `10`; `0` ponechá všetky).
- Konkrétne AppID môžete vylúčiť ich uvedením (jedno na riadok, komentáre `#` sú povolené) v `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Sledovač auto-synchronizácie systemd (`./install.sh --with-auto-sync` alebo `steam-auto-sync --install-systemd`) pri zmene manifestov Steam spúšťa `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`.

---

## Referencia CLI a profilov

### Príkazy

| Účel | Príkaz |
| --- | --- |
| Audit pripravenosti systému | `steam-auto-run --doctor` (alias `--check-system`) |
| Spustenie ovládacieho centra (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` alebo `steam-auto-run --ui` |
| Inšpekcia hry (čitateľná pre človeka) | `steam-auto-run --inspect APPID` |
| Inšpekcia hry (JSON) | `steam-auto-detect --inspect --json APPID` |
| Interaktívna zmena profilu | `steam-auto-run --configure APPID` |
| Náhľad výsledného spúšťacieho prostredia | `steam-auto-run --dry-run APPID` |
| Reset uloženého profilu | `steam-auto-run --reset APPID` |
| Zoznam uložených profilov | `steam-auto-run --list-profiles` |
| Zobrazenie posledného logu spustenia | `steam-auto-run --last-log [APPID]` |
| Náhľad spúšťacieho prostredia VR | `vr-run --dry-run` |
| Kontrola sieťového pomocníka (len na čítanie) | `steam-net-boost status [IFACE]` |

### Kľúče uložených profilov `.env` a prepisy prostredia

Súbory profilov sa nachádzajú v `~/.config/steam-auto-profiler/profiles/<APPID>.env` a akceptujú iba povolený zoznam kľúčov vo formáte `KEY=VALUE` (substitúcie príkazov shellu a neznáme kľúče sa bezpečne ignorujú):

| Kľúč `.env` | Prepis v prostredí | Účinok |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Vynúti XWayland namiesto natívneho Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Vypne upgrade FSR 4 na úrovni ovládača (predvolene `1`) |
| `USE_MLFG=1` | `MLFG=1` | Zapne generovanie snímok (vypína Anti-Lag, nízku latenciu a VRR limity) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Zapne mostík OptiScaler (automaticky blokovaný pre `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Zapne doostrovanie vkBasalt (vypnuté pri aktívnom FSR 4 alebo OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Vynechá experimentálne prepínače `VKD3D_CONFIG` a token `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Aktivuje sieťový QoS relácie cez `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Uprednostní natívnu emuláciu SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Zachová `LD_PRELOAD` pre Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Pridá `--in-process-gpu` pre spúšťače založené na CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Vypne NTSync pre staršie tituly |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Vypne dekorácie správcu okien |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Vlastný limit snímok DXVK/VKD3D (`0` obmedzenie vypína) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Použije rezervu `-6%` voči frekvencii monitora (napr. `225 FPS` pri 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Povolí blokovanie skratiek vo Wine Wayland (predvolene `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Automaticky zapne HDR v KDE Plasma 6 pri štarte a po ukončení vráti SDR |
| — | `BENCH=1`, `BENCH_DURATION=60` | Spustí tichý CSV benchmark v MangoHud a uloží JSON súhrn |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Potlačí alebo vynúti zobrazenie predspúšťacieho okna `kdialog`/`zenity` |
| — | `FSR_HUD=1` | Exportuje premenné indikátora HUD pre FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Pripojí `-vulkan` / spustí cez `prime-run` |
| — | `GAMEID=umu-<appid>` | Rozpozná AppID pre UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus a UMU

- **Lutris:** Zapnite pokročilé nastavenia, vyberte `proton-cachyos-slr` (alebo svoje zostavenie Protonu), vypnite Lutris runtime, uprednostnite systémové knižnice a nastavte predponu príkazu na `steam-auto-run`.
- **Heroic / Faugus:** Vyberte `proton-cachyos-slr` a pridajte `steam-auto-run` ako wrapper / predponu príkazu.
- **UMU / Protonfixes:** Podľa potreby exportujte `PROTON_VERB=waitforexitandrun` a `GAMEID=umu-<appid>`.

---

## Riešenie problémov

- **Rýchly pád na Waylande alebo DX12:** Otvorte kartu **Logs & Recovery** v `steam-auto-ui` (alebo spustite `steam-auto-run --last-log APPID`) a použite núdzový režim (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), prípadne spustite `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Hry s anti-cheatom sa nespustia:** Použite `proton-cachyos-slr` (Steam Linux Runtime) a spustite `steam-auto-run --doctor` na overenie EAC v2, `/dev/ntsync` a `vm.max_map_count`.
- **Steam vracia pôvodné možnosti spustenia:** Pred spustením `steam-auto-sync` alebo `steam-auto-sync --sanitize` Steam úplne ukončite.
- **Nesprávny alebo chýbajúci VRR limit:** Nastavte explicitne `VRR_CAP=<fps>`, zadajte `VRR_CAP=0` na vypnutie alebo `VRR_MINUS_MARGIN=1` pre rezervu `-6%`. V Gamescope exportuje limity DXVK/VKD3D iba explicitné `VRR_CAP`.
- **Kontrola sieťového QoS:** Spustite `steam-net-boost status` (bez oprávnení root, len na čítanie). Pre automatický sieťový QoS relácie nainštalujte root pomocník príkazom `./install.sh --with-net-boost`.

Pozrite si aj [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) a [i18n Index](../README.md) so všetkými 27 jazykovými verziami.
