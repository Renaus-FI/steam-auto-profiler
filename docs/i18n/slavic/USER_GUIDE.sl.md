# Uporabniški priročnik za Steam Auto-Profiler

> 🌐 [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Ta priročnik pokriva celotno namestitev, orkestracijo zagona klasičnih in VR iger, nadzorni center `steam-auto-ui`, sinhronizacijo knjižnice, merjenje zmogljivosti ter odpravljanje težav za **Steam Auto-Profiler v2.0**.

Steam Auto-Profiler je lahek zaganjalnik in nadzorni center v jeziku Bash/Python za Linux, ki preveri Steam AppID (ali bližnjico za igro zunaj Steama), uporabi kontekstno prilagojen profil s strogimi zaščitnimi pravili za gonilnike, upscalerje in sisteme proti goljufanju (anti-cheat) ter zažene obstoječi ukaz igre. Nikoli ne vključuje ali vstavlja zunanjega izvajalnega okolja Proton.

---

## Zahteve

- Namizna seja Linux (KDE Plasma 6 / Wayland, GNOME, wlroots ali X11), Bash 5+, Python 3.10+, Steam in standardna sistemska orodja.
- Izbirni domorodni GUI nadzornega centra: `PyQt6` ali `PySide6` (samodejno preklopi na `curses` TUI iz standardne knjižnice brez zunanjih odvisnosti).
- Izbirna pogovorna okna s kontrolnim seznamom pred zagonom: `kdialog` ali `zenity`.
- Izbirno tiho merjenje časov sličic (frametime benchmarking): `mangohud`.
- Izbirni omrežni pomočnik za sejo: `tc`, `ip` in `ethtool` (`sudo` je potreben samo med namestitvijo z zastavico `--with-net-boost`).

---

## Namestitev in posodobitve

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` skopira vseh šest izvedljivih datotek (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` in `steam-auto-ui`) v `~/.local/bin`, namesti namizno bližnjico (`~/.local/share/applications/steam-auto-profiler.desktop`), ustvari `~/.config/steam-auto-profiler/profiles` in doda privzete prednastavitve vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Prepričajte se, da je `~/.local/bin` v spremenljivki `PATH`.

Izbirne zastavice namestitvenega programa je mogoče kombinirati:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: namesti `/usr/local/bin/steam-net-boost` (ter sistemske kopije ostalih skript) in ozko omejeno pravilo sudoers brez gesla za `steam-net-boost`.
- `--compat-cachy-run`: ohrani obstoječi `/usr/local/bin/cachy-run` kot `/usr/local/bin/cachy-run.bak` (razen če že gre za posredovalni shim programa Steam Auto-Profiler) in namesti posredovalni shim na `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): namesti in omogoči uporabniško enoto systemd `steam-auto-profiler-sync.path` ter pripadajočo storitev oneshot za vse odkrite knjižnice Steam.
- `--uninstall`: odstrani nameščene izvedljive datoteke, namizno bližnjico, izbirni omrežni pomočnik/pravilo sudoers, sloj združljivosti in uporabniške enote systemd za samodejno sinhronizacijo.

Za posodobitev obstoječe lokalne kopije:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Pred sinhronizacijo iger preverite pripravljenost gostitelja:

```bash
steam-auto-run --doctor
```

---

## Celoten cevovod zagona (End-to-End)

1. **Določanje AppID:** Preveri zaporedno `SteamAppId`, `STEAM_COMPAT_APP_ID`, nato `GAMEID` (pri čemer odstrani predpono `umu-` za Lutris/Heroic/UMU).
2. **Odkrivanje knjižnic in bližnjic:** `steam-auto-detect` preišče korenske mape Steama in sekundarne knjižnice v `libraryfolders.vdf`, prebere `appmanifest_<APPID>.acf` ali v načinu samo za branje prebere binarni `userdata/*/config/shortcuts.vdf`, nato pa izvede enoprehodno iskanje `find` do 10 ravni globoko (brez map `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Petstopenjska prednostna klasifikacija:**
   - **1. `competitive-anticheat`:** Znan tekmovalni AppID ali zaznano okolje anti-cheat (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE itd.). Onemogoči OptiScaler, MLFG, vkBasalt in asinhroni DXVK; vklopi nizko zakasnitev in omrežni QoS za sejo.
   - **2. `vr`:** Zaznane datoteke `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` ali zastavice bližnjice `vr-run`/`-vr`. Izvozi `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modularni FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Omogoči nadgradnjo FSR4 na ravni gonilnika (`PROTON_FSR4_UPGRADE=1` ali `PROTON_FSR4_RDNA3_UPGRADE=1` na AMD RDNA 3).
   - **4. `legacy-upscaler`:** Starejše knjižnice DLL za DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) ali FSR 2/3.0. Nastavi `AUTO_OPTISCALER=1` in smernice v `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Varen domorodni profil Wine Wayland + VRR z nizko zakasnitvijo.
4. **Omejitev sličic za VRR:** Izrecni `VRR_CAP=<fps>` ima vedno prednost (`VRR_CAP=0` onemogoči omejitev). Sicer se aktivna frekvenca osveževanja zaslona pridobi preko `kscreen-doctor` (aktivni način `*` v KDE Plasma 6 ali starejši `Hz`), `wlr-randr` ali `xrandr` in se privzeto uporabi 1:1 (`240 FPS` pri 240 Hz). Omogočite `VRR_MINUS_MARGIN=1` za izbirno `-6%` varnostno rezervo VRR (`hz * 94 / 100`, npr. `225 FPS` pri 240 Hz). V sejah Gamescope so omejitve DXVK/VKD3D izpuščene, razen če je `VRR_CAP` nastavljen izrecno.
5. **Zaščitna pravila medsebojnega izključevanja:**
   - **FSR 4 / OptiScaler + vkBasalt:** Vedno uveljavi `ENABLE_VKBASALT=0`, kadar je aktiven `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` ali `USE_OPTISCALER=1` (preprečuje dvojno ostrenje in prirezovanje HDR10).
   - **MLFG + nizka zakasnitev / omejitve VRR:** `MLFG=1` (`USE_MLFG=1`) izvozi `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, počisti `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` in `DXVK_FRAME_PACE` ter izvozi `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` na AMD RDNA 3. Ko je `USE_MLFG=0` in je omejitev VRR aktivna, se izvozi `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Sodobni DX12 + Safe DX12:** Na AMD izvozi `PROTON_NATIVE_AGS=1` in `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, kadar je `USE_SAFEDX12=0` (čisto izpuščeno pri `SAFEDX12=1`).
6. **Preslikava žetonov združljivosti:** Upravljane funkcije se brez prepisovanja obstoječih uporabniških vrednosti pripnejo v obe spremenljivki `PROTON_ADD_CONFIG` in `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Samodejni HDR v KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Kadar je omogočen zunaj Gamescope skupaj z `DXVK_HDR=1` (ali `USE_HDR=1`), preveri primarni omogočeni izhod prek `kscreen-doctor -o`; če je HDR trenutno izklopljen, ga vklopi pred zagonom in ob izhodu v pasti `EXIT`/`INT`/`TERM` obnovi SDR.
8. **Tiho merjenje časov sličic (`BENCH=1`):** Zažene MangoHud v skritem načinu CSV (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), ob izhodu obdela čase sličic, doda `Avg FPS`, `1% Low FPS` in `P99 (ms)` v `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` ter odstrani začasne datoteke CSV.
9. **Samodejna obnovitev v Varni način po hitrem sesutju:** Če se naslov Proton/Windows konča z neničelno izhodno kodo v manj kot `20s` (nastavljivo prek `SAP_CRASH_THRESHOLD_SEC`), medtem ko so aktivne eksperimentalne zastavice Wayland ali DX12 (`USE_XWAYLAND=0` ali `USE_SAFEDX12=0`), zapiše `crash_hint` v `last-<APPID>.log` in `last-launch.log`, ob aktivnem GUI pa ponudi shranjevanje `USE_XWAYLAND=1` + `USE_SAFEDX12=1` za naslednji zagon.
10. **Življenjski cikel razporejevalnika in omrežja:** Teče skozi verigo `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (le kadar `ananicy-cpp.service` ni aktiven) -> neposredni zagon, z izbirnim `PRIME=1` (`prime-run`). Če je `USE_NET_OPT=1`, `steam-net-boost` izvede referenčno šteti `on`/`off` s `flock`, pri čemer ohrani statične korenske CAKE in HTB + listne CAKE hierarhije.

---

## Enotni nadzorni center (`steam-auto-ui`)

Zaženite `steam-auto-ui` iz menija aplikacij, z ukazom `steam-auto-run --ui` ali neposredno:

```bash
steam-auto-ui                 # Samodejno zazna Qt6 GUI (PyQt6/PySide6) ali curses TUI
steam-auto-ui --gui           # Vsili domorodno okno Qt6 GUI
steam-auto-ui --tui           # Vsili stdlib curses TUI (deluje prek SSH)
steam-auto-ui --lang fi       # Zažene z izrecnim jezikom vmesnika (podprtih 27 jezikov)
steam-auto-ui --check         # Izvede samopreverjanje brez zaslona (izpiše JSON diagnostiko)
```

`steam-auto-ui` samodejno zazna sistemsko območno nastavitev iz `LC_ALL` / `LC_MESSAGES` / `LANG` in nudi spustni meni za izbiro jezika v živo v Qt6 GUI (ter bližnjico `L` v `curses` TUI) za preklapljanje med vsemi 27 jeziki (vključno s `sl`) med delovanjem brez ponovnega zagona.

### Pet sinhroniziranih pogledov

1. **Igre in profili (Games & Profiles):** Filtrirna tabela naslovov Steam in vnosov zunaj Steama samo za branje iz `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), značka Upscaler SDK (`AUTO_UPSCALER_INFO`), sprotni nadzor medsebojnega izključevanja za vseh 10 stikal profila + `VRR_CAP`, `Dry-Run Preview`, gumb za skok v `Benchmarks` in `Reset Profile`.
2. **Sistem in telemetrija (System & Telemetry):** Neblokirajoči sprotni izpis `steam-auto-run --doctor`, stanje `scxctl get` / `sched_ext`, nameščene različice sklada (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), poraba predpomnilnika senčilnikov (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), opozorila o nižanju različic paketov git/AUR iz `/var/log/pacman.log`, VRAM/zasedenost/temperatura GPU, prepustnost in `av_delay` iz `tc -s qdisc` za LAN (`10:`) proti WAN (`20:`/root) ter `vr-mode status`.
3. **Sinhronizacija knjižnice (Library Sync):** Sprotni zaščitni pas ob delujočem Steamu ter enoklikovni ukazi `--report`, `--sanitize --dry-run`, `--sanitize` (zavrnjen, dokler Steam teče) in `--migrate-cachy-run`.
4. **Dnevniki in obnovitev (Logs & Recovery):** Brskanje po `last-launch.log` in `last-<APPID>.log`, pregled opozoril `crash_hint` in vklop Varnega načina z enim klikom (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Primerjalni testi (Benchmarks):** Filtrirna primerjalna tabela meritev `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR orkestracija (`vr-run`)

V Steamu nastavite **Properties > General > Launch Options** za VR naslove na:

```text
vr-run %command%
```

- Odstrani podedovane nastavitve za ploske zaslone (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Samodejno izbere namensko grafično kartico z največ VRAM prek `MESA_VK_DEVICE_SELECT` in nastavi `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` na AMD GPU.
- Dinamično poišče poti WiVRn in xrizer za OpenXR/OpenVR (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) ter nastavi `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` in `LD_LIBRARY_PATH`, ne da bi prepisal izrecne uporabniške nastavitve.
- Referenčno šteje `vr-mode on` / `vr-mode off` v `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (s `flock`), kadar je `vr-mode` nameščen (`VR_AUTO_MODE=0` to onemogoči).
- Deluje prek iste verige razporejevalnika, ki upošteva `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> neposredni `exec`).
- Razrešene spremenljivke si lahko kadarkoli ogledate z `vr-run --dry-run`.

`steam-auto-run` samodejno preskoči SteamVR (`250820`) in zagone z `-vr`/`--vr`, medtem ko `steam-auto-sync` za VR naslove samodejno dodeli in ohrani `vr-run %command%`.

---

## Sinhronizacija knjižnice Steam (`steam-auto-sync`)

Pred pisanjem v `localconfig.vdf` popolnoma zaprite Steam:

```bash
steam-auto-sync --report              # Pregled knjižnice in shortcuts.vdf samo za branje
steam-auto-sync --print-library-paths # Prikaže vse odkrite knjižnice Steam
steam-auto-sync --dry-run             # Predogled sprememb
steam-auto-sync                       # Vstavi steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Predogled čiščenja starih zastavic
steam-auto-sync --sanitize            # Počisti neurejene/osirotele zastavice (vzdevek: --clean)
steam-auto-sync --migrate-cachy-run   # Preseli stare profile cachy-run
steam-auto-sync --remove              # Odstrani ovoj steam-auto-run
```

- Varnostne kopije s časovnim žigom `localconfig.vdf.bak.*` se samodejno obrezujejo z `--keep-backups N` (privzeto `10`; `0` ohrani vse).
- Določene AppID lahko izključite tako, da jih zapišete (po enega na vrstico, dovoljeni so komentarji `#`) v `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Nadzornik systemd za samodejno sinhronizacijo (`./install.sh --with-auto-sync` ali `steam-auto-sync --install-systemd`) ob spremembi Steamovih manifestov zažene `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`.

---

## Referenca za CLI in profile

### Ukazi

| Namen | Ukaz |
| --- | --- |
| Pregled pripravljenosti sistema | `steam-auto-run --doctor` (vzdevek `--check-system`) |
| Zagon Nadzornega centra (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` ali `steam-auto-run --ui` |
| Pregled igre (berljivo za ljudi) | `steam-auto-run --inspect APPID` |
| Pregled igre (JSON) | `steam-auto-detect --inspect --json APPID` |
| Interaktivna ponastavitev profila | `steam-auto-run --configure APPID` |
| Predogled razrešenega zagonskega okolja | `steam-auto-run --dry-run APPID` |
| Ponastavitev shranjenega profila | `steam-auto-run --reset APPID` |
| Seznam shranjenih profilov | `steam-auto-run --list-profiles` |
| Prikaz zadnjega dnevnika zagona | `steam-auto-run --last-log [APPID]` |
| Predogled zagonskega okolja VR | `vr-run --dry-run` |
| Pregled omrežnega pomočnika (samo za branje) | `steam-net-boost status [IFACE]` |

### Ključi shranjenih `.env` profilov in okoljske spremenljivke

Datoteke profilov se nahajajo v `~/.config/steam-auto-profiler/profiles/<APPID>.env` in sprejemajo le dovoljeni seznam zapisov v obliki `KEY=VALUE` (ukazne zamenjave lupine in neznani ključi se varno prezrejo):

| Ključ `.env` | Okoljska preglasitev | Učinek |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Vsili XWayland namesto domorodnega Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Onemogoči nadgradnjo FSR 4 na ravni gonilnika (privzeto `1`) |
| `USE_MLFG=1` | `MLFG=1` | Omogoči generiranje sličic (onemogoči Anti-Lag, nizko zakasnitev in omejitve VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Omogoči most OptiScaler (zaščitno izklopljen za `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Omogoči ostrenje vkBasalt (onemogočeno, ko je aktiven FSR 4 ali OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Izpusti eksperimentalne zastavice `VKD3D_CONFIG` in žeton `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Aktivira omrežni QoS seje prek `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Daje prednost domorodni emulaciji SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Ohrani `LD_PRELOAD` za Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Doda `--in-process-gpu` za zaganjalnike CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Onemogoči NTSync za starejše naslove |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Onemogoči okraske upravitelja oken |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Po meri nastavljena omejitev sličic DXVK/VKD3D (`0` onemogoči omejitev) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Uporabi `-6%` rezervo glede na osveževanje zaslona (npr. `225 FPS` pri 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Dovoli prestrezanje bližnjic v Wine Wayland (privzeto `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Samodejno vklopi HDR v KDE Plasma 6 ob zagonu in obnovi SDR ob izhodu |
| — | `BENCH=1`, `BENCH_DURATION=60` | Izvede tihi CSV benchmark z MangoHud in shrani JSON povzetek |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Skrije ali znova prikaže kontrolni seznam `kdialog`/`zenity` pred zagonom |
| — | `FSR_HUD=1` | Izvozi spremenljivke kazalnika HUD za FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Doda `-vulkan` / ovije s `prime-run` |
| — | `GAMEID=umu-<appid>` | Razreši AppID za UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus in UMU

- **Lutris:** Omogočite napredne možnosti, izberite `proton-cachyos-slr` (ali svojo različico Proton), onemogočite Lutris runtime, dajte prednost sistemskim knjižnicam in nastavite predpono ukaza na `steam-auto-run`.
- **Heroic / Faugus:** Izberite `proton-cachyos-slr` in dodajte `steam-auto-run` kot ovoj / predpono ukaza.
- **UMU / Protonfixes:** Po potrebi izvozite `PROTON_VERB=waitforexitandrun` in `GAMEID=umu-<appid>`.

---

## Odpravljanje težav

- **Hitro sesutje v Waylandu ali DX12:** Odprite **Logs & Recovery** v `steam-auto-ui` (ali zaženite `steam-auto-run --last-log APPID`) in uveljavite Varni način (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), ali pa zaženite `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Igre s sistemom anti-cheat se ne zaženejo:** Uporabite `proton-cachyos-slr` (Steam Linux Runtime) in zaženite `steam-auto-run --doctor`, da preverite EAC v2, `/dev/ntsync` in `vm.max_map_count`.
- **Steam povrne stare možnosti zagona:** Pred zagonom `steam-auto-sync` ali `steam-auto-sync --sanitize` popolnoma zaprite Steam.
- **Napačna ali manjkajoča omejitev VRR:** Izrecno nastavite `VRR_CAP=<fps>`, `VRR_CAP=0` za izklop ali `VRR_MINUS_MARGIN=1` za `-6%` rezervo. V Gamescope le izrecni `VRR_CAP` izvozi omejitve DXVK/VKD3D.
- **Preverjanje omrežnega QoS:** Zaženite `steam-net-boost status` (brez skrbniških pravic, samo za branje). Za samodejni omrežni QoS seje namestite root pomočnik z `./install.sh --with-net-boost`.

Oglejte si tudi [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) in [i18n Index](../README.md) z vsemi 27 lokaliziranimi priročniki.
