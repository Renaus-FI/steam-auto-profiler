# Uživatelská příručka Steam Auto-Profiler

> 🌐 [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Tato příručka popisuje kompletní instalaci, orchestraci spouštění klasických i VR her, ovládací centrum `steam-auto-ui`, synchronizaci knihovny, měření výkonu a řešení problémů pro **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler je lehký spouštěč a ovládací centrum v Bash/Pythonu pro Linux, který zkontroluje Steam AppID (nebo zástupce hry mimo Steam), použije kontextově řízený profil s přísnými ochrannými pravidly pro ovladače, upscalery i anti-cheat a spustí původní příkaz hry. Nikdy nepřibaluje ani nevkládá cizí běhové prostředí Proton.

---

## Požadavky

- Linuxová desktopová relace (KDE Plasma 6 / Wayland, GNOME, wlroots nebo X11), Bash 5+, Python 3.10+, Steam a standardní systémové nástroje.
- Volitelné nativní GUI ovládacího centra: `PyQt6` nebo `PySide6` (jinak se automaticky přepne do `curses` TUI bez externích závislostí ze standardní knihovny).
- Volitelné dialogy před spuštěním: `kdialog` nebo `zenity`.
- Volitelné tiché měření frametime (benchmarking): `mangohud`.
- Volitelný síťový pomocník pro herní relace: `tc`, `ip` a `ethtool` (`sudo` je nutné pouze během instalace s volbou `--with-net-boost`).

---

## Instalace a aktualizace

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

Skript `./install.sh` zkopíruje všech šest spustitelných souborů (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` a `steam-auto-ui`) do `~/.local/bin`, nainstaluje zástupce plochy (`~/.local/share/applications/steam-auto-profiler.desktop`), vytvoří adresář `~/.config/steam-auto-profiler/profiles` a přidá výchozí presety vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Ujistěte se, že adresář `~/.local/bin` je obsažen v proměnné `PATH`.

Volitelné přepínače instalátoru lze libovolně kombinovat:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: nainstaluje `/usr/local/bin/steam-net-boost` (spolu se systémovými kopiemi ostatních skriptů) a úzce omezené pravidlo sudoers bez hesla pro `steam-net-boost`.
- `--compat-cachy-run`: zálohuje stávající `/usr/local/bin/cachy-run` jako `/usr/local/bin/cachy-run.bak` (pokud už nejde o přesměrovací vrstvu Steam Auto-Profiler) a nainstaluje přesměrování na `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): nainstaluje a povolí uživatelskou jednotku systemd `steam-auto-profiler-sync.path` spolu s odpovídající oneshot službou pro všechny nalezené knihovny Steam.
- `--uninstall`: odstraní nainstalované binární soubory, položku plochy, volitelný síťový pomocník a pravidlo sudoers, vrstvu kompatibility i uživatelské jednotky auto-synchronizace systemd.

Aktualizace stávající kopie repozitáře:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Před synchronizací her ověřte připravenost systému:

```bash
steam-auto-run --doctor
```

---

## Kompletní spouštěcí řetězec (End-to-End)

1. **Rozpoznání AppID:** Zkontroluje `SteamAppId`, `STEAM_COMPAT_APP_ID` a následně `GAMEID` (odstraní případnou předponu `umu-` pro Lutris/Heroic/UMU).
2. **Zjišťování knihoven a zástupců:** `steam-auto-detect` prohledá kořenové složky Steam i sekundární knihovny v `libraryfolders.vdf`, přečte `appmanifest_<APPID>.acf`, případně v režimu jen pro čtení načte binární `userdata/*/config/shortcuts.vdf`, a provede jednoprůchodový `find` do hloubky 10 úrovní (s vynecháním složek `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Pětistupňová priorita klasifikace:**
   - **1. `competitive-anticheat`:** Známé soutěžní AppID nebo detekovaný anti-cheat runtime (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE aj.). Vypne OptiScaler, MLFG, vkBasalt a asynchronní DXVK; aktivuje nízkou latenci a síťový QoS pro relaci.
   - **2. `vr`:** Detekované soubory `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` nebo přepínače zástupce `vr-run`/`-vr`. Exportuje `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modulární FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Zapne upgrade na FSR4 na úrovni ovladače (`PROTON_FSR4_UPGRADE=1`, případně `PROTON_FSR4_RDNA3_UPGRADE=1` na AMD RDNA 3).
   - **4. `legacy-upscaler`:** Starší DLL knihovny DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) nebo FSR 2/3.0. Nastaví `AUTO_OPTISCALER=1` a doporučení v `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Bezpečný profil s nativním Wine Wayland a VRR s nízkou latencí.
4. **Omezení snímků pro VRR:** Explicitní `VRR_CAP=<fps>` má vždy přednost (`VRR_CAP=0` omezení vypíná). Jinak se aktivní obnovovací frekvence monitoru zjistí přes `kscreen-doctor` (aktivní režim `*` v KDE Plasma 6 nebo starší `Hz`), `wlr-randr` či `xrandr` a výchozím způsobem se použije v poměru 1:1 (`240 FPS` na 240 Hz). Zapnutím `VRR_MINUS_MARGIN=1` přidáte volitelnou bezpečnostní rezervu VRR `-6%` (`hz * 94 / 100`, např. `225 FPS` na 240 Hz). V relacích Gamescope se limity DXVK/VKD3D vynechávají, pokud `VRR_CAP` není zadáno explicitně.
5. **Ochranná pravidla vzájemného vyloučení:**
   - **FSR 4 / OptiScaler + vkBasalt:** Vždy vynutí `ENABLE_VKBASALT=0`, pokud je zapnuto `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` nebo `USE_OPTISCALER=1` (brání dvojitému doostřování a ořezu HDR10).
   - **MLFG + nízká latence / limity VRR:** `MLFG=1` (`USE_MLFG=1`) exportuje `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, odstraní `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` a `DXVK_FRAME_PACE` a na AMD RDNA 3 nastaví `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. Když je `USE_MLFG=0` a omezení VRR je aktivní, exportuje se `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Moderní DX12 + Safe DX12:** Na AMD exportuje `PROTON_NATIVE_AGS=1` a při `USE_SAFEDX12=0` také `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` (při `SAFEDX12=1` čistě vynecháno).
6. **Mapování tokenů kompatibility:** Spravované funkce se bez přepsání stávajících uživatelských hodnot připojí do `PROTON_ADD_CONFIG` i `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Automatické HDR v KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Je-li povoleno mimo Gamescope společně s `DXVK_HDR=1` (nebo `USE_HDR=1`), dotáže se na primární aktivní výstup přes `kscreen-doctor -o`; pokud je HDR vypnuté, před spuštěním jej zapne a v obsluze `EXIT`/`INT`/`TERM` vrátí zpět SDR.
8. **Tiché měření frametime (`BENCH=1`):** Spustí MangoHud ve skrytém CSV režimu (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), po ukončení zpracuje frametime, uloží `Avg FPS`, `1% Low FPS` a `P99 (ms)` do `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` a smaže dočasné CSV soubory.
9. **Automatická obnova do nouzového režimu po rychlém pádu:** Pokud hra pod Proton/Windows skončí nenulovým návratovým kódem pod `20s` (nastavitelné přes `SAP_CRASH_THRESHOLD_SEC`) při aktivních experimentálních přepínačích Wayland nebo DX12 (`USE_XWAYLAND=0` nebo `USE_SAFEDX12=0`), zapíše `crash_hint` do `last-<APPID>.log` a `last-launch.log` a při aktivním GUI nabídne uložení `USE_XWAYLAND=1` + `USE_SAFEDX12=1` pro příští spuštění.
10. **Životní cyklus plánovače a sítě:** Spouští přes řetězec `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (pouze pokud je `ananicy-cpp.service` neaktivní) -> přímé spuštění, s volitelným `PRIME=1` (`prime-run`). Při `USE_NET_OPT=1` volá `steam-net-boost` referenčně počítané `on`/`off` s `flock`, přičemž zachovává statický kořenový CAKE i hierarchie HTB + listový CAKE.

---

## Jednotné ovládací centrum (`steam-auto-ui`)

Spusťte `steam-auto-ui` z nabídky aplikací, pomocí `steam-auto-run --ui` nebo přímo:

```bash
steam-auto-ui                 # Automaticky zvolí Qt6 GUI (PyQt6/PySide6) nebo curses TUI
steam-auto-ui --gui           # Vynutí nativní okno Qt6 GUI
steam-auto-ui --tui           # Vynutí curses TUI ze stdlib (funguje přes SSH)
steam-auto-ui --lang fi       # Spustí s explicitním jazykem UI (podporováno 27 jazyků)
steam-auto-ui --check         # Spustí bezhlavou samokontrolu (vypíše JSON diagnostiku)
```

`steam-auto-ui` automaticky zjišťuje systémové locale z `LC_ALL` / `LC_MESSAGES` / `LANG` a v Qt6 GUI nabízí rozbalovací výběr jazyka za běhu (v `curses` TUI klávesu `L`) pro okamžité přepínání mezi všemi 27 jazyky (včetně `cs`) bez restartu.

### Pět synchronizovaných pohledů

1. **Hry a profily (Games & Profiles):** Filtrovatelná tabulka titulů Steam a položek mimo Steam jen pro čtení ze `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), štítek upscaler SDK (`AUTO_UPSCALER_INFO`), živá kontrola vzájemného vyloučení pro všech 10 přepínačů profilu + `VRR_CAP`, náhled `Dry-Run Preview`, tlačítko pro přechod na `Benchmarks` a `Reset Profile`.
2. **Systém a telemetrie (System & Telemetry):** Neblokující živý výpis z `steam-auto-run --doctor`, stav `scxctl get` / `sched_ext`, verze nainstalovaného stacku (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), obsazení shader cache (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), upozornění na downgrade git/AUR balíčků z `/var/log/pacman.log`, VRAM/vytížení/teplota GPU, propustnost a `av_delay` z `tc -s qdisc` pro LAN (`10:`) vs WAN (`20:`/root) a stav `vr-mode status`.
3. **Synchronizace knihovny (Library Sync):** Živý ochranný banner stavu běžícího Steamu a jedno-klikové akce `--report`, `--sanitize --dry-run`, `--sanitize` (odmítnuto, pokud Steam běží) a `--migrate-cachy-run`.
4. **Logy a obnova (Logs & Recovery):** Prohlížení `last-launch.log` a `last-<APPID>.log`, kontrola varování `crash_hint` a aktivace nouzového režimu jedním kliknutím (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarky (Benchmarks):** Filtrovatelná srovnávací tabulka měření frametime z `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Orchestrace VR (`vr-run`)

Ve Steamu nastavte **Vlastnosti > Obecné > Možnosti spuštění** pro VR tituly na:

```text
vr-run %command%
```

- Odstraní zděděné přepisy pro klasické monitory (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Automaticky vybere dedikovanou GPU s největší VRAM přes `MESA_VK_DEVICE_SELECT` a na AMD GPU nastaví `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`.
- Dynamicky vyhledá cesty OpenXR/OpenVR pro WiVRn a xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) a nastaví `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` a `LD_LIBRARY_PATH` bez přepsání explicitních uživatelských proměnných.
- Referenčně počítá `vr-mode on` / `vr-mode off` v `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (pomocí `flock`), pokud je nainstalován `vr-mode` (`VR_AUTO_MODE=0` funkci vypne).
- Používá stejný řetězec plánovače respektující `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> přímý `exec`).
- Vyhodnocené proměnné lze kdykoli zobrazit příkazem `vr-run --dry-run`.

`steam-auto-run` automaticky obchází SteamVR (`250820`) a spuštění s `-vr`/`--vr`; `steam-auto-sync` pro VR tituly automaticky přiřazuje a zachovává `vr-run %command%`.

---

## Synchronizace knihovny Steam (`steam-auto-sync`)

Před zápisem do `localconfig.vdf` Steam úplně ukončete:

```bash
steam-auto-sync --report              # Audit knihovny a shortcuts.vdf jen pro čtení
steam-auto-sync --print-library-paths # Zobrazí všechny nalezené knihovny Steam
steam-auto-sync --dry-run             # Náhled úprav
steam-auto-sync                       # Vloží steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Náhled čištění starých přepínačů
steam-auto-sync --sanitize            # Vyčistí neplatné/osiřelé přepínače (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Převede starší profily cachy-run
steam-auto-sync --remove              # Odstraní obal steam-auto-run
```

- Zálohy `localconfig.vdf.bak.*` s časovým razítkem se automaticky prořezávají podle `--keep-backups N` (výchozí `10`; `0` ponechá všechny).
- Konkrétní AppID můžete vyloučit jejich zapsáním (jedno na řádek, komentáře `#` jsou povoleny) do `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Systémový sledovač systemd (`./install.sh --with-auto-sync` nebo `steam-auto-sync --install-systemd`) spouští při změně manifestů Steam příkaz `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`.

---

## Přehled CLI a profilů

### Příkazy

| Účel | Příkaz |
| --- | --- |
| Audit připravenosti systému | `steam-auto-run --doctor` (alias `--check-system`) |
| Spuštění ovládacího centra (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` nebo `steam-auto-run --ui` |
| Inspekce hry (čitelná pro člověka) | `steam-auto-run --inspect APPID` |
| Inspekce hry (JSON) | `steam-auto-detect --inspect --json APPID` |
| Interaktivní přenastavení profilu | `steam-auto-run --configure APPID` |
| Náhled výsledného spouštěcího prostředí | `steam-auto-run --dry-run APPID` |
| Obnovení uloženého profilu | `steam-auto-run --reset APPID` |
| Výpis uložených profilů | `steam-auto-run --list-profiles` |
| Zobrazení posledního logu spuštění | `steam-auto-run --last-log [APPID]` |
| Náhled spouštěcího prostředí VR | `vr-run --dry-run` |
| Kontrola síťového pomocníka (jen pro čtení) | `steam-net-boost status [IFACE]` |

### Klíče uložených profilů `.env` a přepisy prostředí

Soubory profilů leží v `~/.config/steam-auto-profiler/profiles/<APPID>.env` a přijímají pouze povolený seznam klíčů ve formátu `KEY=VALUE` (substituce příkazů shellu a neznámé klíče se bezpečně ignorují):

| Klíč `.env` | Přepis v prostředí | Účinek |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Vynutí XWayland místo nativního Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Vypne upgrade FSR 4 na úrovni ovladače (výchozí `1`) |
| `USE_MLFG=1` | `MLFG=1` | Zapne generování snímků (vypíná Anti-Lag, nízkou latenci a VRR limity) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Zapne můstek OptiScaler (automaticky vypnuto pro `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Zapne doostřování vkBasalt (vypnuto při aktivním FSR 4 nebo OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Vynechá experimentální přepínače `VKD3D_CONFIG` a token `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Aktivuje síťový QoS relace přes `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Upřednostní nativní emulaci SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Zachová `LD_PRELOAD` pro Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Přidá `--in-process-gpu` pro spouštěče postavené na CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Vypne NTSync pro starší tituly |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Vypne dekorace správce oken |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Vlastní limit snímků DXVK/VKD3D (`0` omezení vypíná) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Použije rezervu `-6%` vůči frekvenci monitoru (např. `225 FPS` na 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Povolí blokování zkratek ve Wine Wayland (výchozí `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Automaticky zapne HDR v KDE Plasma 6 při startu a po ukončení vrátí SDR |
| — | `BENCH=1`, `BENCH_DURATION=60` | Spustí tichý CSV benchmark v MangoHud a uloží JSON souhrn |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Potlačí nebo vynutí zobrazení předspouštěcího okna `kdialog`/`zenity` |
| — | `FSR_HUD=1` | Exportuje proměnné indikátoru HUD pro FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Připojí `-vulkan` / spustí přes `prime-run` |
| — | `GAMEID=umu-<appid>` | Rozpozná AppID pro UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus a UMU

- **Lutris:** Zapněte pokročilé volby, vyberte `proton-cachyos-slr` (nebo své sestavení Protonu), vypněte Lutris runtime, upřednostněte systémové knihovny a nastavte předponu příkazu na `steam-auto-run`.
- **Heroic / Faugus:** Zvolte `proton-cachyos-slr` a přidejte `steam-auto-run` jako wrapper / předponu příkazu.
- **UMU / Protonfixes:** Podle potřeby exportujte `PROTON_VERB=waitforexitandrun` a `GAMEID=umu-<appid>`.

---

## Řešení problémů

- **Rychlý pád na Waylandu nebo DX12:** Otevřete kartu **Logs & Recovery** v `steam-auto-ui` (nebo spusťte `steam-auto-run --last-log APPID`) a použijte nouzový režim (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), případně spusťte `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Hry s anti-cheatem se nespustí:** Použijte `proton-cachyos-slr` (Steam Linux Runtime) a spusťte `steam-auto-run --doctor` pro kontrolu EAC v2, `/dev/ntsync` a `vm.max_map_count`.
- **Steam vrací původní možnosti spuštění:** Před spuštěním `steam-auto-sync` nebo `steam-auto-sync --sanitize` Steam kompletně ukončete.
- **Chybný nebo chybějící VRR limit:** Nastavte explicitně `VRR_CAP=<fps>`, zadejte `VRR_CAP=0` pro vypnutí nebo `VRR_MINUS_MARGIN=1` pro rezervu `-6%`. V Gamescope exportuje limity DXVK/VKD3D pouze explicitní `VRR_CAP`.
- **Kontrola síťového QoS:** Spusťte `steam-net-boost status` (bez práv root, jen pro čtení). Pro automatický síťový QoS relace nainstalujte root pomocník příkazem `./install.sh --with-net-boost`.

---

## Novinky ve v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 a Steam Controller 2026)

- **Přepínače Mesa 27.0 / RDNA 4:** `TRANSFER_QUEUE=1` (deduplikované `RADV_PERFTEST=sam,transfer_queue` na RDNA 3/4), `NATIVE_ANTILAG=1` (nativní `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, blokováno při anti-cheatu a MLFG) a `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** experimentální režim bez anti-cheatu (`VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, `WAYLANDDRV_RAWINPUT=1` pouze v nativním Waylandu mimo Gamescope).
- **Ochrana Hunt: Showdown 1896 (`AppID 594650`):** vynucuje `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0` a `USE_NET_OPT=1`; `--doctor` i `steam-auto-ui` kontrolují `config.vdf` (doporučeno `Proton 11.0-2` nebo `Proton Hotfix`).
- **Steam Controller 2026 / Wireless Puck (`28de:{1302,1304,1005,1007}`):** 4 režimy (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` zachovává Wayland + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`, bez `sdlinput`), automaticky posílá `steam://forceinputappid/<APPID>` s `udevadm` sledováním znovupřipojení a při ukončení vrací `steam://forceinputappid/0`. Ručně: `steam-auto-run --reapply-input <APPID|0>`; udev: `./install.sh --with-steam-controller`.

---

Viz také [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) a [i18n Index](../README.md) se všemi 27 jazykovými verzemi.
