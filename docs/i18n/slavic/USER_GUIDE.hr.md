# Korisnički priručnik za Steam Auto-Profiler

> 🌐 [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Ovaj priručnik pokriva potpunu instalaciju, orkestraciju pokretanja klasičnih i VR igara, upravljački centar `steam-auto-ui`, sinkronizaciju biblioteke, benchmark mjerenja i rješavanje problema za **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler je lagani Bash/Python pokretač i upravljački centar za Linux koji provjerava Steam AppID (ili prečac za igru izvan Steama), primjenjuje kontekstualni profil sa strogim zaštitnim pravilima za upravljačke programe, upscalere i anti-cheat sustave te pokreće postojeću naredbu igre. Nikada ne pakira niti ubrizgava vanjsko Proton izvodno okruženje.

---

## Zahtjevi

- Linux radna sesija (KDE Plasma 6 / Wayland, GNOME, wlroots ili X11), Bash 5+, Python 3.10+, Steam i standardni sistemski alati.
- Neobavezni nativni GUI upravljačkog centra: `PyQt6` ili `PySide6` (automatski se prebacuje na `curses` TUI iz standardne biblioteke bez dodatnih ovisnosti).
- Neobavezni dijalozi s popisom provjere prije pokretanja: `kdialog` ili `zenity`.
- Neobavezno tiho mjerenje vremena kadrova (frametime benchmarking): `mangohud`.
- Neobavezni mrežni pomoćnik za sesiju: `tc`, `ip` i `ethtool` (`sudo` je potreban samo tijekom instalacije s `--with-net-boost`).

---

## Instalacija i ažuriranja

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` kopira svih šest izvršnih datoteka (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` i `steam-auto-ui`) u `~/.local/bin`, instalira prečac radne površine (`~/.local/share/applications/steam-auto-profiler.desktop`), stvara `~/.config/steam-auto-profiler/profiles` i dodaje zadane vkBasalt predloške (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Provjerite nalazi li se `~/.local/bin` u varijabli `PATH`.

Neobavezne zastavice instalatora mogu se kombinirati:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: instalira `/usr/local/bin/steam-net-boost` (uz sistemske kopije ostalih skripti) i usko ograničeno sudoers pravilo bez lozinke za `steam-net-boost`.
- `--compat-cachy-run`: čuva postojeći `/usr/local/bin/cachy-run` kao `/usr/local/bin/cachy-run.bak` (osim ako već nije prosljeđujući shim Steam Auto-Profilera) i instalira prosljeđujući shim prema `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): instalira i omogućuje korisničku systemd jedinicu `steam-auto-profiler-sync.path` te odgovarajući oneshot servis za sve otkrivene Steam biblioteke.
- `--uninstall`: uklanja instalirane binarne datoteke, stavku radne površine, neobavezni mrežni pomoćnik/sudoers pravilo, sloj kompatibilnosti i korisničke systemd jedinice za automatsku sinkronizaciju.

Za ažuriranje postojeće lokalne kopije:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Provjerite spremnost sustava prije sinkronizacije igara:

```bash
steam-auto-run --doctor
```

---

## Cjeloviti lanac pokretanja (End-to-End)

1. **Razrješavanje AppID-a:** Provjerava redom `SteamAppId`, `STEAM_COMPAT_APP_ID`, zatim `GAMEID` (uklanjajući eventualni prefiks `umu-` za Lutris/Heroic/UMU).
2. **Otkrivanje biblioteka i prečaca:** `steam-auto-detect` pretražuje korijenske mape Steama i sekundarne biblioteke u `libraryfolders.vdf`, čita `appmanifest_<APPID>.acf`, ili u načinu samo za čitanje prelazi na binarni `userdata/*/config/shortcuts.vdf`, a zatim izvodi jednoprolazni `find` do 10 razina dubine (preskačući `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Petostupanjski prioritet klasifikacije:**
   - **1. `competitive-anticheat`:** Poznati natjecateljski AppID ili otkriveni anti-cheat runtime (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE itd.). Isključuje OptiScaler, MLFG, vkBasalt i asinkroni DXVK; uključuje nisku latenciju i mrežni QoS sesije.
   - **2. `vr`:** Otkriveni `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` ili zastavice prečaca `vr-run`/`-vr`. Izvozi `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modularni FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Omogućuje FSR4 nadogradnju na razini upravljačkog programa (`PROTON_FSR4_UPGRADE=1` ili `PROTON_FSR4_RDNA3_UPGRADE=1` na AMD RDNA 3).
   - **4. `legacy-upscaler`:** Starije DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) ili FSR 2/3.0 DLL biblioteke. Postavlja `AUTO_OPTISCALER=1` i smjernice u `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Siguran nativni Wine Wayland + VRR profil niske latencije.
4. **Ograničavanje sličica za VRR:** Eksplicitni `VRR_CAP=<fps>` uvijek ima prednost (`VRR_CAP=0` isključuje ograničenje). Inače se aktivna frekvencija osvježavanja zaslona očita putem `kscreen-doctor` (aktivni `*` način u KDE Plasma 6 ili stariji `Hz`), `wlr-randr` ili `xrandr` i zadano primjenjuje 1:1 (`240 FPS` na 240 Hz). Uključite `VRR_MINUS_MARGIN=1` za neobaveznu `-6%` VRR sigurnosnu marginu (`hz * 94 / 100`, npr. `225 FPS` na 240 Hz). U Gamescope sesijama ograničenja za DXVK/VKD3D se izostavljaju osim ako `VRR_CAP` nije eksplicitno postavljen.
5. **Zaštitna pravila međusobnog isključivanja:**
   - **FSR 4 / OptiScaler + vkBasalt:** Uvijek nameće `ENABLE_VKBASALT=0` kad god je aktivan `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` ili `USE_OPTISCALER=1` (sprječava dvostruko izoštravanje i HDR10 rezanje).
   - **MLFG + niska latencija / VRR ograničenja:** `MLFG=1` (`USE_MLFG=1`) izvozi `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, uklanja `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` i `DXVK_FRAME_PACE` te izvozi `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` na AMD RDNA 3. Kada je `USE_MLFG=0` i VRR ograničenje aktivno, izvozi se `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Moderni DX12 + Safe DX12:** Na AMD-u izvozi `PROTON_NATIVE_AGS=1` te `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` kada je `USE_SAFEDX12=0` (čisto izostavljeno kada je `SAFEDX12=1`).
6. **Mapiranje tokena kompatibilnosti:** Upravljane značajke dodaju se bez prepisivanja postojećih korisničkih vrijednosti u obje varijable `PROTON_ADD_CONFIG` i `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Automatski HDR u KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Kada je uključen izvan Gamescopea uz `DXVK_HDR=1` (ili `USE_HDR=1`), provjerava primarni aktivni izlaz putem `kscreen-doctor -o`; ako je HDR trenutačno isključen, uključuje ga prije pokretanja i vraća SDR u `EXIT`/`INT`/`TERM` zamci.
8. **Tihi frametime benchmark (`BENCH=1`):** Pokreće MangoHud u skrivenom CSV načinu (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), pri izlasku obrađuje vremena kadrova, dodaje `Avg FPS`, `1% Low FPS` i `P99 (ms)` u `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` i uklanja privremene CSV datoteke.
9. **Automatski oporavak u Sigurni način nakon brzog rušenja:** Ako Proton/Windows igra završi s nenultim kodom za manje od `20s` (podesivo putem `SAP_CRASH_THRESHOLD_SEC`) dok su aktivne eksperimentalne Wayland ili DX12 zastavice (`USE_XWAYLAND=0` ili `USE_SAFEDX12=0`), zapisuje `crash_hint` u `last-<APPID>.log` i `last-launch.log`, a uz aktivan GUI nudi spremanje `USE_XWAYLAND=1` + `USE_SAFEDX12=1` za sljedeće pokretanje.
10. **Životni ciklus raspoređivača i mreže:** Prolazi kroz lanac `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (samo kada je `ananicy-cpp.service` neaktivan) -> izravno pokretanje, uz neobavezni `PRIME=1` (`prime-run`). Ako je `USE_NET_OPT=1`, `steam-net-boost` pokreće referentno brojani `on`/`off` s `flock` uz očuvanje statičnih korijenskih CAKE i HTB + lisnih CAKE hijerarhija.

---

## Jedinstveni upravljački centar (`steam-auto-ui`)

Pokrenite `steam-auto-ui` iz izbornika aplikacija, naredbom `steam-auto-run --ui` ili izravno:

```bash
steam-auto-ui                 # Automatski otkriva Qt6 GUI (PyQt6/PySide6) ili curses TUI
steam-auto-ui --gui           # Prisiljava nativni Qt6 GUI prozor
steam-auto-ui --tui           # Prisiljava stdlib curses TUI (radi preko SSH-a)
steam-auto-ui --lang fi       # Pokreće s eksplicitnim jezikom sučelja (podržano 27 jezika)
steam-auto-ui --check         # Izvodi headless samoprovjeru (ispisuje JSON dijagnostiku)
```

`steam-auto-ui` automatski prepoznaje sistemski lokal iz `LC_ALL` / `LC_MESSAGES` / `LANG` te nudi padajući izbornik jezika uživo u Qt6 GUI-ju (i tipku `L` u `curses` TUI-ju) za prebacivanje između svih 27 jezika (uključujući `hr`) tijekom rada bez ponovnog pokretanja.

### Pet sinkroniziranih prikaza

1. **Igre i profili (Games & Profiles):** Filtrirajuća tablica Steam naslova i Non-Steam unosa samo za čitanje iz `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), značka Upscaler SDK (`AUTO_UPSCALER_INFO`), provjera međusobnog isključivanja uživo za svih 10 prekidača profila + `VRR_CAP`, `Dry-Run Preview`, gumb za prijelaz na `Benchmarks` i `Reset Profile`.
2. **Sustav i telemetrija (System & Telemetry):** Neblokirajući prikaz uživo za `steam-auto-run --doctor`, stanje `scxctl get` / `sched_ext`, instalirane verzije stoga (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), zauzeće predmemorije shadera (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), upozorenja na downgrade git/AUR paketa iz `/var/log/pacman.log`, VRAM/opterećenje/temperaturu GPU-a, propusnost i `av_delay` iz `tc -s qdisc` za LAN (`10:`) naspram WAN (`20:`/root) te `vr-mode status`.
3. **Sinkronizacija biblioteke (Library Sync):** Zaštitni natpis uživo dok je Steam pokrenut te radnje jednim klikom za `--report`, `--sanitize --dry-run`, `--sanitize` (odbijeno dok Steam radi) i `--migrate-cachy-run`.
4. **Dnevnici i oporavak (Logs & Recovery):** Pregled `last-launch.log` i `last-<APPID>.log`, uvid u `crash_hint` upozorenja i primjena Sigurnog načina jednim klikom (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmark mjerenja (Benchmarks):** Filtrirajuća usporedna tablica `BENCH=1` mjerenja vremena kadrova (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR orkestracija (`vr-run`)

U Steamu postavite **Properties > General > Launch Options** za VR naslove na:

```text
vr-run %command%
```

- Uklanja naslijeđene postavke za klasične zaslone (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Automatski odabire diskretnu grafičku karticu s najviše VRAM-a putem `MESA_VK_DEVICE_SELECT` i postavlja `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` na AMD GPU-ovima.
- Dinamički otkriva WiVRn i xrizer OpenXR/OpenVR putanje (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) i konfigurira `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` te `LD_LIBRARY_PATH` bez prepisivanja eksplicitnih korisničkih varijabli.
- Referentno broji `vr-mode on` / `vr-mode off` u `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (uz `flock`) kada je `vr-mode` instaliran (`VR_AUTO_MODE=0` isključuje ovu opciju).
- Izvodi se kroz isti lanac raspoređivača svjestan `ananicy-cpp` servisa (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> izravni `exec`).
- Izračunate varijable možete pregledati u bilo kojem trenutku pomoću `vr-run --dry-run`.

`steam-auto-run` automatski zaobilazi SteamVR (`250820`) i pokretanja s `-vr`/`--vr`, dok `steam-auto-sync` automatski dodjeljuje i čuva `vr-run %command%` za VR naslove.

---

## Sinkronizacija Steam biblioteke (`steam-auto-sync`)

Potpuno zatvorite Steam prije pisanja u `localconfig.vdf`:

```bash
steam-auto-sync --report              # Revizija biblioteke i shortcuts.vdf samo za čitanje
steam-auto-sync --print-library-paths # Prikazuje sve otkrivene Steam biblioteke
steam-auto-sync --dry-run             # Pregled izmjena
steam-auto-sync                       # Umeće steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Pregled čišćenja starih zastavica
steam-auto-sync --sanitize            # Čisti neuredne/zaostale zastavice (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migrira stare cachy-run profile
steam-auto-sync --remove              # Uklanja steam-auto-run omotač
```

- Sigurnosne kopije s vremenskom oznakom `localconfig.vdf.bak.*` automatski se čiste opcijom `--keep-backups N` (zadano `10`; `0` čuva sve).
- Pojedine AppID-ove možete isključiti upisom (jedan po retku, dopušteni su `#` komentari) u `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Systemd nadzornik automatske sinkronizacije (`./install.sh --with-auto-sync` ili `steam-auto-sync --install-systemd`) pokreće `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` kad god se Steam manifesti promijene.

---

## Referenca za CLI i profile

### Naredbe

| Namjena | Naredba |
| --- | --- |
| Provjera spremnosti sustava | `steam-auto-run --doctor` (alias `--check-system`) |
| Pokretanje Upravljačkog centra (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` ili `steam-auto-run --ui` |
| Inspekcija igre (čitljivo ljudima) | `steam-auto-run --inspect APPID` |
| Inspekcija igre (JSON) | `steam-auto-detect --inspect --json APPID` |
| Interaktivna izmjena profila | `steam-auto-run --configure APPID` |
| Pregled izračunatog okruženja pokretanja | `steam-auto-run --dry-run APPID` |
| Poništavanje spremljenog profila | `steam-auto-run --reset APPID` |
| Popis spremljenih profila | `steam-auto-run --list-profiles` |
| Prikaz zadnjeg dnevnika pokretanja | `steam-auto-run --last-log [APPID]` |
| Pregled VR okruženja pokretanja | `vr-run --dry-run` |
| Provjera mrežnog pomoćnika (samo za čitanje) | `steam-net-boost status [IFACE]` |

### Ključevi spremljenih `.env` profila i varijable okruženja

Datoteke profila nalaze se u `~/.config/steam-auto-profiler/profiles/<APPID>.env` i prihvaćaju samo dopušteni popis unosa u obliku `KEY=VALUE` (supstitucije naredbi ljuske i nepoznati ključevi sigurno se ignoriraju):

| `.env` ključ | Env zamjena | Učinak |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Prisiljava XWayland umjesto nativnog Wine Waylanda |
| `USE_FSR4=0` | `FSR4=0` | Isključuje FSR 4 nadogradnju na razini upravljačkog programa (zadano `1`) |
| `USE_MLFG=1` | `MLFG=1` | Uključuje generiranje kadrova (isključuje Anti-Lag, nisku latenciju i VRR limite) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Uključuje OptiScaler most (blokiran za `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Uključuje vkBasalt izoštravanje (isključeno kada je aktivan FSR 4 ili OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Izostavlja eksperimentalne `VKD3D_CONFIG` zastavice i token `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Aktivira mrežni QoS sesije putem `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Preferira nativnu SDL / Steam Input emulaciju |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Čuva Steam Overlay `LD_PRELOAD` |
| `USE_CEF_FIX=1` | `CEF=1` | Dodaje `--in-process-gpu` za CEF pokretače |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Isključuje NTSync za starije naslove |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Isključuje dekoracije upravitelja prozora |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Prilagođeno DXVK/VKD3D ograničenje sličica (`0` isključuje ograničenje) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Primjenjuje `-6%` marginu u odnosu na osvježavanje monitora (npr. `225 FPS` na 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Dopušta inhibiciju prečaca pod Wine Waylandom (zadano `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Automatski uključuje HDR u KDE Plasma 6 pri pokretanju i vraća SDR pri izlasku |
| — | `BENCH=1`, `BENCH_DURATION=60` | Pokreće tihi MangoHud CSV benchmark i sprema JSON sažetak |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Potiskuje ili ponovno otvara `kdialog`/`zenity` popis provjere prije pokretanja |
| — | `FSR_HUD=1` | Izvozi varijable HUD pokazatelja za FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Dodaje `-vulkan` / omotava s `prime-run` |
| — | `GAMEID=umu-<appid>` | Razrješava AppID za UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus i UMU

- **Lutris:** Omogućite napredne opcije, odaberite `proton-cachyos-slr` (ili vlastitu Proton inačicu), isključite Lutris runtime, dajte prednost sistemskim bibliotekama i postavite prefiks naredbe na `steam-auto-run`.
- **Heroic / Faugus:** Odaberite `proton-cachyos-slr` i dodajte `steam-auto-run` kao wrapper / prefiks naredbe.
- **UMU / Protonfixes:** Po potrebi izvezite `PROTON_VERB=waitforexitandrun` i `GAMEID=umu-<appid>`.

---

## Rješavanje problema

- **Brzo rušenje na Waylandu ili DX12:** Otvorite **Logs & Recovery** u `steam-auto-ui` (ili pokrenite `steam-auto-run --last-log APPID`) i primijenite Sigurni način (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), ili pokrenite `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Anti-cheat igre se ne pokreću:** Koristite `proton-cachyos-slr` (Steam Linux Runtime) i pokrenite `steam-auto-run --doctor` za provjeru EAC v2, `/dev/ntsync` i `vm.max_map_count`.
- **Steam vraća stare opcije pokretanja:** Potpuno zatvorite Steam prije pokretanja `steam-auto-sync` ili `steam-auto-sync --sanitize`.
- **Pogrešno ili nedostajuće VRR ograničenje:** Postavite eksplicitno `VRR_CAP=<fps>`, `VRR_CAP=0` za isključivanje ili `VRR_MINUS_MARGIN=1` za `-6%` marginu. U Gamescopeu samo eksplicitni `VRR_CAP` izvozi DXVK/VKD3D ograničenja.
- **Provjera mrežnog QoS-a:** Pokrenite `steam-net-boost status` (bez root ovlasti, samo za čitanje). Instalirajte root pomoćnik pomoću `./install.sh --with-net-boost` ako želite automatski mrežni QoS sesije.

---

## Novosti u v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 i Steam Controller 2026)

- **Oznake Mesa 27.0 / RDNA 4:** `TRANSFER_QUEUE=1` (deduplicirani `RADV_PERFTEST=sam,transfer_queue` na RDNA 3/4), `NATIVE_ANTILAG=1` (nativni `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, blokirano u anti-cheatu i MLFG-u) i `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** eksperimentalni stek bez anti-cheata (`VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, `WAYLANDDRV_RAWINPUT=1` samo u nativnom Waylandu izvan Gamescopea).
- **Zaštita Hunt: Showdown 1896 (`AppID 594650`):** nameće `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0` i `USE_NET_OPT=1`; `--doctor` i `steam-auto-ui` provjeravaju `config.vdf` za `Proton 11.0-2` / `Proton Hotfix`.
- **Steam Controller 2026 / Wireless Puck (`28de:{1302,1304,1005,1007}`):** 4 načina (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` zadržava Wayland + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`, bez `sdlinput`), automatski šalje `steam://forceinputappid/<APPID>` s `udevadm` nadzorom ponovnog povezivanja i resetira `steam://forceinputappid/0` pri izlazu. Ručno: `steam-auto-run --reapply-input <APPID|0>`; udev: `./install.sh --with-steam-controller`.

---

Pogledajte i [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) te [i18n Index](../README.md) sa svih 27 lokaliziranih priručnika.
