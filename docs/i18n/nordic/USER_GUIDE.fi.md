# Steam Auto-Profiler — Käyttöopas

> [English User Guide](../../USER_GUIDE.md) · [i18n Index](../README.md)

Tämä opas kattaa **Steam Auto-Profiler v2.1**:n täydellisen asennuksen, tasoruutu- ja VR-käynnistysorkestroinnin, `steam-auto-ui`-hallintakeskuksen, kirjastojen synkronoinnin, suorituskykytestauksen ja vianmäärityksen.

Steam Auto-Profiler on kevyt Bash/Python-käynnistin ja hallintakeskus Linuxille, joka tunnistaa Steam AppID:n (tai muun kuin Steamin pikakuvakkeen), soveltaa tilannekohtaisen profiilin tiukoilla ajuri-, skaalain- ja huijauksenestosuojauksilla ja käynnistää pelin olemassa olevan käynnistyskomennon. Se ei koskaan sisällytä tai injektoi kolmannen osapuolen Proton-ajonaikaa.

---

## Järjestelmävaatimukset

- Linux-työpöytäistunto (KDE Plasma 6 / Wayland, GNOME, wlroots tai X11), Bash 5+, Python 3.10+, Steam ja perusjärjestelmätyökalut.
- Valinnainen natiivi hallintakeskuksen käyttöliittymä (GUI): `PyQt6` tai `PySide6` (siirtyy automaattisesti ilman ulkoisia riippuvuuksia toimivaan Pythonin standardikirjaston `curses`-TUI-käyttöliittymään).
- Valinnaiset käynnistystä edeltävät tarkistuslistadialogit: `kdialog` tai `zenity`.
- Valinnainen hiljainen ruutuaikamittaus (frametime-vertailu): `mangohud`.
- Valinnainen istuntokohtainen verkkoapuri: `tc`, `ip` ja `ethtool` (`sudo` tarvitaan vain `--with-net-boost`-asennuksen aikana).

---

## Asennus ja päivitykset

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` kopioi kaikki kuusi suoritettavaa ohjelmaa (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` ja `steam-auto-ui`) hakemistoon `~/.local/bin`, asentaa työpöytäkuvakkeen (`~/.local/share/applications/steam-auto-profiler.desktop`), luo hakemiston `~/.config/steam-auto-profiler/profiles` ja lisää vkBasalt-oletusesiasetukset (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Varmista, että `~/.local/bin` on `PATH`-ympäristömuuttujassa.

Valinnaisia asennuslippuja voidaan yhdistellä:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: asentaa `/usr/local/bin/steam-net-boost`-työkalun (sekä järjestelmätason kopiot muista skripteistä) ja kapeasti rajatun salasanattoman sudoers-säännön komennolle `steam-net-boost`.
- `--compat-cachy-run`: säilyttää olemassa olevan `/usr/local/bin/cachy-run`-tiedoston nimellä `/usr/local/bin/cachy-run.bak` (ellei se jo ole Steam Auto-Profilerin ohjausskripti) ja asentaa edelleenohjaavan sovittimen (shim) kohteeseen `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): asentaa ja ottaa käyttöön käyttäjäkohtaisen systemd-yksikön `steam-auto-profiler-sync.path` sekä vastaavan kertaluonteisen palvelun kaikille löydetyille Steam-kirjastoille.
- `--uninstall`: poistaa asennetut binäärit, työpöytäkuvakkeen, valinnaisen verkkoapurin ja sudoers-säännön, yhteensopivuussovittimen sekä käyttäjän systemd auto-sync -yksiköt.

Olemassa olevan asennuksen päivittäminen:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Tarkista järjestelmän valmius ennen pelien synkronointia:

```bash
steam-auto-run --doctor
```

---

## Päästä päähän -käynnistysputki

1. **AppID:n selvitys:** Tarkistaa järjestyksessä muuttujat `SteamAppId`, `STEAM_COMPAT_APP_ID` ja sitten `GAMEID` (poistaen mahdollisen `umu-`-etuliitteen Lutris/Heroic/UMU-käynnistyksissä).
2. **Kirjastojen ja pikakuvakkeiden tunnistus:** `steam-auto-detect` hakee Steamin juurihakemistot ja toissijaiset kirjastot tiedostosta `libraryfolders.vdf`, lukee manifestin `appmanifest_<APPID>.acf` tai turvautuu vain luku -tilassa binääriseen tiedostoon `userdata/*/config/shortcuts.vdf`. Tämän jälkeen se suorittaa yhden läpikäynnin `find`-haun enintään 10 tason syvyyteen (ohittaen hakemistot `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Viisitasoinen luokittelujärjestys:**
   - **1. `competitive-anticheat`:** Tunnettu kilpailullinen AppID tai havaittu huijaukseneston ajonaika (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE jne.). Poistaa käytöstä OptiScalerin, MLFG:n, vkBasaltin ja asynkronisen DXVK:n; ottaa käyttöön matalan viiveen tilan ja istunnon verkko-QoS:n.
   - **2. `vr`:** Havaittu `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` tai `vr-run`/`-vr`-pikakuvakeliput. Asettaa muuttujan `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modulaarinen FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Ottaa käyttöön ajuritason FSR 4 -päivityksen (`PROTON_FSR4_UPGRADE=1` tai `PROTON_FSR4_RDNA3_UPGRADE=1` AMD RDNA 3 -näytönohjaimilla).
   - **4. `legacy-upscaler`:** Vanhemmat DLSS- (`nvngx_dlss*.dll`), XeSS- (`libxess*.dll`), Streamline- (`sl.interposer.dll`) tai FSR 2/3.0 -kirjastot. Merkitsee `AUTO_OPTISCALER=1` ja asettaa ohjaustiedon `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Turvallinen natiivi Wine Wayland + matalan viiveen VRR-profiili.
4. **VRR-virkistystaajuuden rajoitus:** Erikseen asetettu `VRR_CAP=<fps>` voittaa aina (`VRR_CAP=0` poistaa rajoituksen käytöstä). Muutoin aktiivisen näytön virkistystaajuus luetaan työkaluilla `kscreen-doctor` (KDE Plasma 6:n aktiivinen `*`-tila tai perinteinen `Hz`), `wlr-randr` tai `xrandr` ja asetetaan oletuksena 1:1-suhteessa (`240 FPS` 240 Hz:n näytöllä). Aseta `VRR_MINUS_MARGIN=1`, jos haluat valinnaisen `-6%` VRR-turvamarginaalin (`hz * 94 / 100`, esim. `225 FPS` 240 Hz:n näytöllä). Gamescope-istunnoissa DXVK/VKD3D-rajoitukset jätetään asettamatta, ellei `VRR_CAP` ole erikseen määritetty.
5. **Keskinäisen poissulkemisen suojaukset:**
   - **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` pakotetaan aina, kun `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` tai `USE_OPTISCALER=1` on aktiivinen (estää kaksinkertaisen terävöinnin ja HDR10-leikkautumisen).
   - **MLFG + matala viive / VRR-rajoitukset:** `MLFG=1` (`USE_MLFG=1`) asettaa muuttujat `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, poistaa muuttujat `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` ja `DXVK_FRAME_PACE` sekä asettaa muuttujan `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` AMD RDNA 3:lla. Kun `USE_MLFG=0` ja VRR-rajoitus on käytössä, asetetaan `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Moderni DX12 + Safe DX12:** Asettaa `PROTON_NATIVE_AGS=1` AMD-näytönohjaimilla sekä `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, kun `USE_SAFEDX12=0` (jätetään siististi pois, kun `SAFEDX12=1`).
6. **Compat-tunnisteiden (tokenien) kartoitus:** Hallitut ominaisuudet lisätään käyttäjän aiempia arvoja ylikirjoittamatta sekä muuttujaan `PROTON_ADD_CONFIG` että `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Automaattinen KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** Kun tämä on käytössä Gamescopen ulkopuolella yhdessä muuttujan `DXVK_HDR=1` (tai `USE_HDR=1`) kanssa, tarkistaa ensisijaisen käytössä olevan näytön komennolla `kscreen-doctor -o`; jos HDR on pois päältä, ottaa sen käyttöön ennen käynnistystä ja palauttaa SDR-tilan `EXIT`/`INT`/`TERM`-siepparissa (trap).
8. **Hiljainen ruutuaikamittaus (`BENCH=1`):** Käyttää MangoHudia piilotetussa CSV-tilassa (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), jäsentää ruutuajat pelin päätyttyä, lisää arvot `Avg FPS`, `1% Low FPS` ja `P99 (ms)` tiedostoon `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` ja poistaa väliaikaiset CSV-tiedostot.
9. **Nopean kaatumisen vikasietotilan automaattipalautus:** Jos Proton/Windows-peli päättyy virhekoodilla alle `20s`:ssa (säädettävissä muuttujalla `SAP_CRASH_THRESHOLD_SEC`) samalla kun kokeelliset Wayland- tai DX12-liput ovat päällä (`USE_XWAYLAND=0` tai `USE_SAFEDX12=0`), lokiin `last-<APPID>.log` ja `last-launch.log` kirjataan `crash_hint` ja (GUI:n ollessa aktiivinen) käyttäjältä kysytään, tallennetaanko `USE_XWAYLAND=1` + `USE_SAFEDX12=1` seuraavaa käynnistystä varten.
10. **Skeduleri- ja verkkoelinkaari:** Suorittaa ketjun `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (vain kun `ananicy-cpp.service` ei ole aktiivinen) -> suora suoritus, valinnaisesti yhdessä `PRIME=1` (`prime-run`) -asetuksen kanssa. Jos `USE_NET_OPT=1`, `steam-net-boost` ajaa viitelasketun `on`/`off`-tilan `flock`-lukituksella säilyttäen staattiset root CAKE- ja HTB + leaf CAKE -jonohierarkiat.

---

## Yhtenäinen hallintakeskus (`steam-auto-ui`)

Käynnistä `steam-auto-ui` työpöydän sovellusvalikosta, komennolla `steam-auto-run --ui` tai suoraan:

```bash
steam-auto-ui                 # Tunnistaa automaattisesti Qt6-GUI:n (PyQt6/PySide6) tai curses-TUI:n
steam-auto-ui --gui           # Pakota natiivi Qt6-GUI-ikkuna
steam-auto-ui --tui           # Pakota standardikirjaston curses-TUI (toimii SSH:n yli)
steam-auto-ui --lang fi       # Käynnistä valitulla käyttöliittymäkielellä (27 tuettua kieltä)
steam-auto-ui --check         # Suorita päätön itsetarkistus (tulostaa JSON-diagnostiikan)
```

`steam-auto-ui` tunnistaa järjestelmän kieliasetuksen automaattisesti muuttujista `LC_ALL` / `LC_MESSAGES` / `LANG` ja tarjoaa reaaliaikaisen kielivalikon Qt6-GUI:ssa (sekä pikanäppäimen `L` `curses`-TUI:ssa) kaikkien 27 kielen vaihtamiseen lennossa ilman uudelleenkäynnistystä.

### Viisi synkronoitua näkymää

1. **Games & Profiles:** Suodatettava taulukko Steam-peleistä ja vain luku -tilaisista muista kuin Steamin `shortcuts.vdf`-merkinnöistä (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), skaalain-SDK-tunniste (`AUTO_UPSCALER_INFO`), reaaliaikainen keskinäisen poissulkemisen validointi kaikille 10 profiilikytkimelle + `VRR_CAP`, `Dry-Run Preview`, pikapainike `Benchmarks`-näkymään ja `Reset Profile`.
2. **System & Telemetry:** Ei-estoinen reaaliaikainen näkymä kohteista `steam-auto-run --doctor`, `scxctl get` / `sched_ext` -tila, asennetut pakettiversiot (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), varjostinvälimuistin käyttö (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` git/AUR-versioalennushälytykset, GPU:n VRAM/käyttöaste/lämpötila, `tc -s qdisc` LAN (`10:`) vs. WAN (`20:`/root) -siirtonopeus ja `av_delay` sekä `vr-mode status`.
3. **Library Sync:** Reaaliaikainen Steamin käynnissäolotilan suojausbanneri sekä yhden napsautuksen komennot `--report`, `--sanitize --dry-run`, `--sanitize` (estetään Steamin ollessa käynnissä) ja `--migrate-cachy-run`.
4. **Logs & Recovery:** Selaa tiedostoja `last-launch.log` ja `last-<APPID>.log`, tutki `crash_hint`-hälytyksiä ja ota yhdellä napsautuksella käyttöön Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarks:** Suodatettava rinnakkaisvertailutaulukko `BENCH=1`-ruutuaika-ajoista (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR-orkestrointi (`vr-run`)

Aseta VR-peleille Steamissa kohdassa **Ominaisuudet > Yleiset > Käynnistysasetukset**:

```text
vr-run %command%
```

- Poistaa periytyvät tasoruutujen ohitukset (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Valitsee automaattisesti suurimmalla VRAM-muistilla varustetun erillisnäytönohjaimen muuttujalla `MESA_VK_DEVICE_SELECT` ja asettaa AMD-näytönohjaimilla `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`.
- Etsii dynaamisesti WiVRn- ja xrizer OpenXR/OpenVR -polut (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) ja konfiguroi muuttujat `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` ja `LD_LIBRARY_PATH` ylikirjoittamatta käyttäjän omia asetuksia.
- Viitelaskee tilat `vr-mode on` / `vr-mode off` tiedostossa `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (`flock`-lukituksella), kun `vr-mode` on asennettu (`VR_AUTO_MODE=0` poistaa toiminnon käytöstä).
- Suorittaa saman `ananicy-cpp`-tietoisen skeduleriketjun (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> suora `exec`).
- Esikatsele lopulliset ympäristömuuttujat milloin tahansa komennolla `vr-run --dry-run`.

`steam-auto-run` ohittaa automaattisesti SteamVR:n (`250820`) ja `-vr`/`--vr`-käynnistykset, ja `steam-auto-sync` määrittää sekä säilyttää automaattisesti komennon `vr-run %command%` VR-peleille.

---

## Steam-kirjaston synkronointi (`steam-auto-sync`)

Sulje Steam kokonaan ennen tiedostoon `localconfig.vdf` kirjoittamista:

```bash
steam-auto-sync --report              # Vain luku -tilainen kirjaston ja shortcuts.vdf:n tarkastus
steam-auto-sync --print-library-paths # Näytä kaikki löydetyt Steam-kirjastot
steam-auto-sync --dry-run             # Esikatsele muutokset
steam-auto-sync                       # Lisää steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Esikatsele vanhojen lippujen siivous
steam-auto-sync --sanitize            # Siivoa sotkuiset/orvot liput (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Siirrä vanhat cachy-run-profiilit
steam-auto-sync --remove              # Poista steam-auto-run-kääre
```

- Aikaleimatut `localconfig.vdf.bak.*`-varmuuskopiot siivotaan automaattisesti lipulla `--keep-backups N` (oletus `10`; `0` säilyttää kaikki).
- Voit jättää tiettyjä AppID-tunnuksia synkronoinnin ulkopuolelle listaamalla ne (yksi per rivi, `#`-kommentit sallittu) tiedostoon `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Systemd auto-sync -valvoja (`./install.sh --with-auto-sync` tai `steam-auto-sync --install-systemd`) suorittaa komennon `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`, kun Steamin manifestit muuttuvat.

---

## Komentorivi- ja profiiliviite

### Komennot

| Tarkoitus | Komento |
| --- | --- |
| Järjestelmän valmiustarkastus | `steam-auto-run --doctor` (alias `--check-system`) |
| Käynnistä hallintakeskus (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` tai `steam-auto-run --ui` |
| Tarkastele peliä (ihmisluettava) | `steam-auto-run --inspect APPID` |
| Tarkastele peliä (JSON) | `steam-auto-detect --inspect --json APPID` |
| Muokkaa profiilia vuorovaikutteisesti | `steam-auto-run --configure APPID` |
| Esikatsele käynnistysympäristö | `steam-auto-run --dry-run APPID` |
| Palauta tallennettu profiili | `steam-auto-run --reset APPID` |
| Listaa tallennetut profiilit | `steam-auto-run --list-profiles` |
| Näytä viimeisin käynnistysloki | `steam-auto-run --last-log [APPID]` |
| Esikatsele VR-käynnistysympäristö | `vr-run --dry-run` |
| Tarkastele verkkoapuria (vain luku) | `steam-net-boost status [IFACE]` |

### Tallennetut `.env`-profiiliavaimet ja ympäristöohitukset

Profiilitiedostot sijaitsevat polussa `~/.config/steam-auto-profiler/profiles/<APPID>.env` ja hyväksyvät sallittujen avainten listan mukaisen `KEY=VALUE`-muodon (komentokorvaukset ja tuntemattomat avaimet ohitetaan turvallisesti):

| `.env`-avain | Ympäristöohitus | Vaikutus |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Pakota XWayland natiivin Wine Waylandin sijaan |
| `USE_FSR4=0` | `FSR4=0` | Poista ajuritason FSR 4 -päivitys käytöstä (oletus `1`) |
| `USE_MLFG=1` | `MLFG=1` | Ota ruutujen generointi käyttöön (poistaa Anti-Lagin, matalan viiveen ja VRR-rajoitukset) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Ota OptiScaler-silta käyttöön (estetty luokassa `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Ota vkBasalt-terävöinti käyttöön (pois päältä, kun FSR 4 tai OptiScaler on aktiivinen) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Jätä kokeelliset `VKD3D_CONFIG`-liput ja `vkd3dbindlesstb`-tunniste pois |
| `USE_NET_OPT=1` | `NETOPT=1` | Aktivoi istunnon verkko-QoS työkalulla `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Suosi natiivia SDL- / Steam Input -emulointia |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Säilytä Steam Overlayn `LD_PRELOAD` |
| `USE_CEF_FIX=1` | `CEF=1` | Lisää `--in-process-gpu` CEF-käynnistimille |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Poista NTSync käytöstä vanhoilla peleillä |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Poista ikkunanhallinnan kehykset käytöstä |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Mukautettu DXVK/VKD3D-ruutunopeusraja (`0` poistaa rajoituksen) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Sovella `-6%` marginaali näytön virkistystaajuuteen (esim. `225 FPS` 240 Hz:llä) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Salli pikanäppäinten esto Wine Waylandissa (oletus `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Ota KDE Plasma 6 HDR automaattisesti käyttöön käynnistyksessä ja palauta SDR lopetuksessa |
| — | `BENCH=1`, `BENCH_DURATION=60` | Suorita hiljainen MangoHud CSV -suorituskykytesti ja tallenna JSON-yhteenveto |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Estä tai pakota avaamaan käynnistystä edeltävä `kdialog`/`zenity`-tarkistuslista |
| — | `FSR_HUD=1` | Vie FSR/DLSS/MLFG HUD -ilmaisinmuuttujat |
| — | `VULKAN=1` / `PRIME=1` | Lisää `-vulkan` / kääri komennolla `prime-run` |
| — | `GAMEID=umu-<appid>` | Selvitä UMU / Lutris / Heroic AppID:t |

---

## Lutris, Heroic, Faugus ja UMU

- **Lutris:** Ota lisäasetukset käyttöön, valitse `proton-cachyos-slr` (tai oma Proton-versiosi), poista Lutris-ajonaika käytöstä, suosi järjestelmän kirjastoja ja aseta komennon etuliitteeksi `steam-auto-run`.
- **Heroic / Faugus:** Valitse `proton-cachyos-slr` ja lisää `steam-auto-run` kääreeksi tai komennon etuliitteeksi.
- **UMU / Protonfixes:** Vie tarvittaessa muuttujat `PROTON_VERB=waitforexitandrun` ja `GAMEID=umu-<appid>`.

---

## Vianmääritys

- **Nopea kaatuminen Waylandissa tai DX12:ssa:** Avaa **Logs & Recovery** työkalussa `steam-auto-ui` (tai aja `steam-auto-run --last-log APPID`) ja ota käyttöön Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), tai käynnistä komennolla `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Huijauksenestoa käyttävät pelit eivät käynnisty:** Käytä `proton-cachyos-slr`-ajonaikaa (Steam Linux Runtime) ja tarkista komennolla `steam-auto-run --doctor`, että EAC v2, `/dev/ntsync` ja `vm.max_map_count` ovat kunnossa.
- **Steam palauttaa vanhat käynnistysasetukset:** Sulje Steam kokonaan ennen komentojen `steam-auto-sync` tai `steam-auto-sync --sanitize` ajamista.
- **Väärä tai puuttuva VRR-rajoitus:** Aseta `VRR_CAP=<fps>` suoraan, `VRR_CAP=0` rajoituksen poistamiseksi tai `VRR_MINUS_MARGIN=1` `-6%` marginaalille. Gamescopessa vain erikseen asetettu `VRR_CAP` vie DXVK/VKD3D-rajoitukset.
- **Verkko-QoS:n tarkistus:** Aja `steam-net-boost status` (etuoikeudeton vain luku -tila). Asenna pääkäyttäjän apuri komennolla `./install.sh --with-net-boost`, jos haluat automaattisen istuntokohtaisen QoS:n.

---

## Uutta versiossa v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 ja Steam Controller 2026)

- **Mesa 27.0 / RDNA 4 -asetukset:** `TRANSFER_QUEUE=1` (deduplikoitu `RADV_PERFTEST=sam,transfer_queue` RDNA 3/4 -näytönohjaimilla), `NATIVE_ANTILAG=1` (natiivi `VK_AMD_anti_lag` ilman vanhaa kerrosta), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, estetty huijauksenestopeleissä ja MLFG:ssä) sekä `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** Valinnainen kokeellinen tila (ei huijauksenestopeleille), joka aktivoi deduplikoitujen RADV-lippujen lisäksi asetukset `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1` ja `WAYLANDDRV_RAWINPUT=1` (vain natiivissa Waylandissa Gamescopen ulkopuolella).
- **Hunt: Showdown 1896 (`AppID 594650`) -yhteensopivuussuoja:** Pakottaa automaattisesti tilan `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0` ja `USE_NET_OPT=1`. Komennot `steam-auto-run --doctor` ja `steam-auto-ui` tarkistavat lisäksi `config/config.vdf` `CompatToolMapping`-merkinnän (suositus: Valven `Proton 11.0-2` tai `Proton Hotfix`).
- **Steam Controller 2026 (`Triton`/`Proteus`) & Wireless Steam Puck (`28de:{1302,1304,1005,1007}`):**
  - Neljä reititystilaa (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`, valittavissa myös `steam-auto-ui`:ssa ja TUI:n pikanäppäimellä `c`): `auto` valitsee Waylandissa oletuksena tilan `wayland-hdr` (ja X11:ssä `xwayland`).
  - `wayland-hdr` säilyttää natiivin `winewayland.drv` + OLED HDR10 -tuen (`USE_XWAYLAND=0`, `PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`) ilman turhaa `LD_PRELOAD`-kuormaa, asettaa `PROTON_USE_SDL=0`, `PROTON_PREFER_SDL=0`, `PROTON_NO_STEAMINPUT=0` (ilman `sdlinput`-tunnistetta), lukitsee pelin Steam Input -profiilin komennolla `steam://forceinputappid/<APPID>` ja valvoo automaattisesti ohjaimen uudelleenyhdistämisiä (`udevadm monitor`) palauttaen työpöytäasettelun (`steam://forceinputappid/0`) pelin päättyessä.
  - Käytä komentoa `steam-auto-run --reapply-input <APPID|0>` manuaaliseen uudelleenaktivointiin ja `./install.sh --with-steam-controller` udev-sääntöjen (`/etc/udev/rules.d/61-steam-controller-2026.rules`) asentamiseen.

---

Katso suunnittelun yksityiskohdat tiedostosta [ARCHITECTURE.md](../../ARCHITECTURE.md), englanninkielinen pääopas osoitteesta [English User Guide](../../USER_GUIDE.md) ja kaikki 27 kieliversiota hakemistosta [i18n Index](../README.md).
