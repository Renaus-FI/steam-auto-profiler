# Podręcznik użytkownika Steam Auto-Profiler

> 🌐 [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Ten podręcznik opisuje kompletną instalację, orkiestrację uruchamiania gier płaskoekranowych i VR, centrum sterowania `steam-auto-ui`, synchronizację biblioteki, testy wydajności oraz rozwiązywanie problemów w **Steam Auto-Profiler v2.0**.

Steam Auto-Profiler to lekki launcher i centrum sterowania napisane w Bash/Python dla systemu Linux, które analizuje Steam AppID (lub skrót gry spoza Steam), stosuje profil dopasowany do kontekstu z rygorystycznymi zabezpieczeniami sterowników, upscalerów i systemów anti-cheat, a następnie uruchamia istniejące polecenie gry. Narzędzie nigdy nie dołącza ani nie wstrzykuje zewnętrznego środowiska uruchomieniowego Proton.

---

## Wymagania

- Sesja pulpitu Linux (KDE Plasma 6 / Wayland, GNOME, wlroots lub X11), Bash 5+, Python 3.10+, Steam oraz standardowe narzędzia systemowe.
- Opcjonalny natywny interfejs GUI Centrum Sterowania: `PyQt6` lub `PySide6` (w razie braku następuje automatyczne przełączenie na bezależnościowe TUI `curses` z biblioteki standardowej).
- Opcjonalne okna listy kontrolnej przed uruchomieniem: `kdialog` lub `zenity`.
- Opcjonalne ciche testowanie czasów klatek (benchmarking): `mangohud`.
- Opcjonalny pomocnik sieciowy sesji: `tc`, `ip` oraz `ethtool` (`sudo` jest wymagane wyłącznie podczas instalacji z flagą `--with-net-boost`).

---

## Instalacja i aktualizacje

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

Skrypt `./install.sh` kopiuje wszystkie sześć plików wykonywalnych (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` oraz `steam-auto-ui`) do `~/.local/bin`, instaluje aktywator pulpitu (`~/.local/share/applications/steam-auto-profiler.desktop`), tworzy katalog `~/.config/steam-auto-profiler/profiles` oraz dodaje domyślne presety vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Upewnij się, że katalog `~/.local/bin` znajduje się w zmiennej `PATH`.

Opcjonalne flagi instalatora można ze sobą łączyć:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: instaluje `/usr/local/bin/steam-net-boost` (oraz systemowe kopie pozostałych skryptów) i wąsko ograniczoną regułę sudoers bez hasła dla `steam-net-boost`.
- `--compat-cachy-run`: zachowuje istniejący plik `/usr/local/bin/cachy-run` jako `/usr/local/bin/cachy-run.bak` (o ile nie jest już warstwą przekierowującą Steam Auto-Profiler) i instaluje przekierowanie do `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): instaluje i włącza jednostkę użytkownika systemd `steam-auto-profiler-sync.path` wraz z powiązaną usługą oneshot monitorującą wszystkie wykryte biblioteki Steam.
- `--uninstall`: usuwa zainstalowane pliki wykonywalne, wpis pulpitu, opcjonalny pomocnik sieciowy i regułę sudoers, warstwę zgodności oraz jednostki auto-synchronizacji systemd użytkownika.

Aby zaktualizować istniejącą kopię repozytorium:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Przed synchronizacją gier sprawdź gotowość hosta:

```bash
steam-auto-run --doctor
```

---

## Kompletny potok uruchamiania (End-to-End)

1. **Rozpoznawanie AppID:** Sprawdza kolejno `SteamAppId`, `STEAM_COMPAT_APP_ID`, a następnie `GAMEID` (usuwając prefiks `umu-` dla Lutris/Heroic/UMU).
2. **Wykrywanie bibliotek i skrótów:** `steam-auto-detect` przeszukuje katalogi główne Steam oraz dodatkowe biblioteki z `libraryfolders.vdf`, odczytuje `appmanifest_<APPID>.acf` lub w trybie tylko do odczytu sprawdza binarny plik `userdata/*/config/shortcuts.vdf`, a następnie wykonuje jednoprzebiegowe wyszukiwanie `find` do głębokości 10 poziomów (pomijając katalogi `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Pięciopoziomowa hierarchia klasyfikacji:**
   - **1. `competitive-anticheat`:** Znany turniejowy AppID lub wykryte środowisko anti-cheat (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE itp.). Wyłącza OptiScaler, MLFG, vkBasalt oraz asynchroniczny DXVK; włącza niskie opóźnienia oraz sesyjny QoS sieciowy.
   - **2. `vr`:** Wykryte biblioteki `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, pliki `*.vrmanifest` lub flagi skrótu `vr-run`/`-vr`. Eksportuje `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modularny FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Włącza aktualizację FSR4 na poziomie sterownika (`PROTON_FSR4_UPGRADE=1` lub `PROTON_FSR4_RDNA3_UPGRADE=1` na kartach AMD RDNA 3).
   - **4. `legacy-upscaler`:** Starsze biblioteki DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) lub FSR 2/3.0 DLL. Ustawia `AUTO_OPTISCALER=1` oraz wskazówki w `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Bezpieczny profil natywnego Wine Wayland + VRR o niskim opóźnieniu.
4. **Limit klatek pod VRR:** Jawnie podane `VRR_CAP=<fps>` ma zawsze najwyższy priorytet (`VRR_CAP=0` wyłącza limitowanie). W przeciwnym razie aktywna częstotliwość odświeżania ekranu jest wykrywana przez `kscreen-doctor` (aktywny tryb `*` w KDE Plasma 6 lub starszy `Hz`), `wlr-randr` albo `xrandr` i domyślnie stosowana w skali 1:1 (`240 FPS` przy 240 Hz). Włącz `VRR_MINUS_MARGIN=1`, aby aktywować opcjonalny zapas bezpieczeństwa VRR `-6%` (`hz * 94 / 100`, np. `225 FPS` przy 240 Hz). W sesjach Gamescope limity DXVK/VKD3D są pomijane, chyba że `VRR_CAP` zostało ustawione jawnie.
5. **Zabezpieczenia wzajemnego wykluczania:**
   - **FSR 4 / OptiScaler + vkBasalt:** Wymusza `ENABLE_VKBASALT=0` zawsze, gdy aktywne jest `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` lub `USE_OPTISCALER=1` (zapobiega podwójnemu wyostrzaniu i obcinaniu zakresu HDR10).
   - **MLFG + niskie opóźnienia / limity VRR:** `MLFG=1` (`USE_MLFG=1`) eksportuje `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, usuwa zmienne `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` i `DXVK_FRAME_PACE` oraz eksportuje `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` na AMD RDNA 3. Gdy `USE_MLFG=0` i limitowanie VRR jest aktywne, eksportowana jest zmienna `DXVK_FRAME_PACE=low-latency-vrr`.
   - **Nowoczesny DX12 + Safe DX12:** Eksportuje `PROTON_NATIVE_AGS=1` na kartach AMD oraz `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, gdy `USE_SAFEDX12=0` (czysto pomijane przy `SAFEDX12=1`).
6. **Mapowanie tokenów kompatybilności:** Zarządzane funkcje są dopisywane bez nadpisywania istniejących wartości użytkownika do obu zmiennych `PROTON_ADD_CONFIG` oraz `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Automatyczny HDR w KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Po włączeniu poza sesją Gamescope wraz z `DXVK_HDR=1` (lub `USE_HDR=1`) sprawdza główne aktywne wyjście ekranu poleceniem `kscreen-doctor -o`; jeśli HDR jest wyłączony, aktywuje go przed uruchomieniem gry i przywraca SDR w pułapce `EXIT`/`INT`/`TERM`.
8. **Cichy pomiar czasów klatek (`BENCH=1`):** Uruchamia MangoHud w ukrytym trybie zapisu CSV (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), po zakończeniu gry analizuje czasy klatek, dopisuje `Avg FPS`, `1% Low FPS` oraz `P99 (ms)` do `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` i usuwa tymczasowe pliki CSV.
9. **Automatyczne odzyskiwanie w trybie bezpiecznym po szybkiej awarii:** Jeśli gra Proton/Windows zakończy się niezerowym kodem wyjścia w czasie poniżej `20s` (konfigurowalne przez `SAP_CRASH_THRESHOLD_SEC`), gdy aktywne są eksperymentalne flagi Wayland lub DX12 (`USE_XWAYLAND=0` lub `USE_SAFEDX12=0`), narzędzie zapisuje `crash_hint` w `last-<APPID>.log` oraz `last-launch.log`, a przy aktywnym GUI proponuje zapisanie `USE_XWAYLAND=1` + `USE_SAFEDX12=1` dla kolejnego uruchomienia.
10. **Cykl życia planisty i sieci:** Uruchamia grę przez łańcuch `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (tylko gdy usługa `ananicy-cpp.service` jest nieaktywna) -> bezpośrednie uruchomienie, z opcjonalnym `PRIME=1` (`prime-run`). Gdy `USE_NET_OPT=1`, `steam-net-boost` wykonuje zliczane referencyjnie wywołania `on`/`off` chronione przez `flock`, zachowując istniejące statyczne hierarchie głównego CAKE oraz HTB + liści CAKE.

---

## Zunifikowane Centrum Sterowania (`steam-auto-ui`)

Uruchom `steam-auto-ui` z menu aplikacji pulpitu, poleceniem `steam-auto-run --ui` lub bezpośrednio z terminala:

```bash
steam-auto-ui                 # Automatycznie wykrywa Qt6 GUI (PyQt6/PySide6) lub curses TUI
steam-auto-ui --gui           # Wymusza natywne okno Qt6 GUI
steam-auto-ui --tui           # Wymusza curses TUI ze stdlib (działa przez SSH)
steam-auto-ui --lang fi       # Uruchamia z jawnym językiem interfejsu (obsługiwanych 27 języków)
steam-auto-ui --check         # Wykonuje bezgłowy autotest (wypisuje diagnostykę JSON)
```

`steam-auto-ui` automatycznie wykrywa ustawienia regionalne z `LC_ALL` / `LC_MESSAGES` / `LANG` oraz oferuje rozwijaną listę wyboru języka na żywo w Qt6 GUI (oraz skrót klawiszowy `L` w `curses` TUI), pozwalając przełączać się między wszystkimi 27 językami (w tym `pl`) w trakcie działania bez ponownego uruchamiania.

### Pięć zsynchronizowanych widoków

1. **Gry i profile (Games & Profiles):** Filtrowana tabela tytułów Steam oraz wpisów spoza Steam odczytywanych tylko do odczytu z `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), etykieta SDK upscalera (`AUTO_UPSCALER_INFO`), walidacja wzajemnego wykluczania na żywo dla wszystkich 10 przełączników profilu + `VRR_CAP`, podgląd `Dry-Run Preview`, przycisk przejścia do `Benchmarks` oraz `Reset Profile`.
2. **System i telemetria (System & Telemetry):** Nieblokujący odczyt na żywo wyników `steam-auto-run --doctor`, stanu `scxctl get` / `sched_ext`, wersji zainstalowanego stosu (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), rozmiaru pamięci podręcznej shaderów (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), alertów obniżenia wersji git/AUR z `/var/log/pacman.log`, użycia VRAM/GPU/temperatury, przepustowości i `av_delay` z `tc -s qdisc` dla LAN (`10:`) vs WAN (`20:`/root) oraz stanu `vr-mode status`.
3. **Synchronizacja biblioteki (Library Sync):** Baner na żywo chroniący przed zapisem przy uruchomionym Steam oraz przyciski jednego kliknięcia: `--report`, `--sanitize --dry-run`, `--sanitize` (blokowane, gdy Steam działa) oraz `--migrate-cachy-run`.
4. **Logi i odzyskiwanie (Logs & Recovery):** Przeglądanie `last-launch.log` oraz `last-<APPID>.log`, inspekcja alertów `crash_hint` oraz włączanie trybu bezpiecznego jednym kliknięciem (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarki (Benchmarks):** Filtrowana tabela porównawcza pomiarów czasów klatek z `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Orkiestracja VR (`vr-run`)

W Steam ustaw **Właściwości > Ogólne > Opcje uruchamiania** dla tytułów VR na:

```text
vr-run %command%
```

- Czyści odziedziczone nadpisania płaskoekranowe (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Automatycznie wybiera dyskretną kartę graficzną z największą ilością VRAM poprzez `MESA_VK_DEVICE_SELECT`, a na GPU AMD ustawia `AMD_VULKAN_ICD=RADV` i `RADV_PERFTEST=sam`.
- Dynamicznie wykrywa ścieżki OpenXR/OpenVR dla WiVRn i xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) i konfiguruje `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` oraz `LD_LIBRARY_PATH` bez nadpisywania jawnych ustawień użytkownika.
- Zlicza referencyjnie sesje `vr-mode on` / `vr-mode off` w `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (z blokadą `flock`), gdy zainstalowane jest `vr-mode` (`VR_AUTO_MODE=0` wyłącza tę funkcję).
- Korzysta z tego samego łańcucha planisty świadomego `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> bezpośrednie `exec`).
- W dowolnym momencie możesz podejrzeć wyliczone zmienne poleceniem `vr-run --dry-run`.

`steam-auto-run` automatycznie pomija SteamVR (`250820`) oraz uruchomienia z `-vr`/`--vr`, a `steam-auto-sync` samoczynnie przypisuje i zachowuje `vr-run %command%` dla tytułów VR.

---

## Synchronizacja biblioteki Steam (`steam-auto-sync`)

Przed zapisem do `localconfig.vdf` całkowicie zamknij Steam:

```bash
steam-auto-sync --report              # Audyt biblioteki i shortcuts.vdf tylko do odczytu
steam-auto-sync --print-library-paths # Wyświetla wszystkie wykryte biblioteki Steam
steam-auto-sync --dry-run             # Podgląd planowanych zmian
steam-auto-sync                       # Wstawia steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Podgląd czyszczenia starych flag
steam-auto-sync --sanitize            # Czyści niepoprawne/osierocone flagi (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migruje stare profile cachy-run
steam-auto-sync --remove              # Usuwa wrapper steam-auto-run
```

- Kopie zapasowe z sygnaturą czasu `localconfig.vdf.bak.*` są automatycznie przycinane flagą `--keep-backups N` (domyślnie `10`; `0` zachowuje wszystkie).
- Możesz wykluczyć wybrane AppID, dopisując je (po jednym na wiersz, dozwolone komentarze `#`) w pliku `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Obserwator auto-synchronizacji systemd (`./install.sh --with-auto-sync` lub `steam-auto-sync --install-systemd`) uruchamia `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` przy zmianie manifestów Steam.

---

## Referencja CLI i profili

### Polecenia

| Zastosowanie | Polecenie |
| --- | --- |
| Audyt gotowości systemu | `steam-auto-run --doctor` (alias `--check-system`) |
| Uruchomienie Centrum Sterowania (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` lub `steam-auto-run --ui` |
| Inspekcja gry (czytelna dla człowieka) | `steam-auto-run --inspect APPID` |
| Inspekcja gry (JSON) | `steam-auto-detect --inspect --json APPID` |
| Interaktywna zmiana profilu | `steam-auto-run --configure APPID` |
| Podgląd wyliczonego środowiska uruchomieniowego | `steam-auto-run --dry-run APPID` |
| Reset zapisanego profilu | `steam-auto-run --reset APPID` |
| Lista zapisanych profili | `steam-auto-run --list-profiles` |
| Pokaż ostatni log uruchomienia | `steam-auto-run --last-log [APPID]` |
| Podgląd środowiska uruchomieniowego VR | `vr-run --dry-run` |
| Podgląd pomocnika sieciowego (tylko do odczytu) | `steam-net-boost status [IFACE]` |

### Klucze zapisanych profili `.env` i nadpisania środowiskowe

Pliki profili znajdują się w `~/.config/steam-auto-profiler/profiles/<APPID>.env` i akceptują wyłącznie dozwoloną listę wpisów w formacie `KEY=VALUE` (podstawienia poleceń powłoki i nieznane klucze są bezpiecznie ignorowane):

| Klucz `.env` | Nadpisanie Env | Efekt |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Wymusza XWayland zamiast natywnego Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Wyłącza aktualizację FSR 4 na poziomie sterownika (domyślnie `1`) |
| `USE_MLFG=1` | `MLFG=1` | Włącza generowanie klatek (wyłącza Anti-Lag, tryb niskich opóźnień i limity VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Włącza mostek OptiScaler (blokowany dla `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Włącza wyostrzanie vkBasalt (wyłączane przy aktywnym FSR 4 lub OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Pomija eksperymentalne flagi `VKD3D_CONFIG` oraz token `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Aktywuje sesyjny QoS sieciowy przez `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Preferuje natywną emulację SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Zachowuje `LD_PRELOAD` nakładki Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Dopisuje `--in-process-gpu` dla launcherów opartych na CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Wyłącza NTSync dla starszych tytułów |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Wyłącza dekoracje menedżera okien |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Własny limit klatek DXVK/VKD3D (`0` wyłącza limitowanie) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Stosuje zapas `-6%` względem odświeżania monitora (np. `225 FPS` przy 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Zezwala na przechwytywanie skrótów pod Wine Wayland (domyślnie `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Automatycznie włącza HDR w KDE Plasma 6 przy starcie i przywraca SDR po wyjściu |
| — | `BENCH=1`, `BENCH_DURATION=60` | Uruchamia cichy benchmark CSV MangoHud i zapisuje podsumowanie JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Ukrywa lub wymusza ponowne otwarcie okna `kdialog`/`zenity` przed uruchomieniem |
| — | `FSR_HUD=1` | Eksportuje zmienne wskaźnika HUD dla FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Dopisuje `-vulkan` / uruchamia przez `prime-run` |
| — | `GAMEID=umu-<appid>` | Rozpoznaje AppID dla UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus i UMU

- **Lutris:** Włącz opcje zaawansowane, wybierz `proton-cachyos-slr` (lub swoją wersję Proton), wyłącz środowisko uruchomieniowe Lutris (Lutris runtime), włącz preferowanie bibliotek systemowych i ustaw prefiks polecenia na `steam-auto-run`.
- **Heroic / Faugus:** Wybierz `proton-cachyos-slr` i dodaj `steam-auto-run` jako wrapper / prefiks polecenia.
- **UMU / Protonfixes:** W razie potrzeby wyeksportuj `PROTON_VERB=waitforexitandrun` oraz `GAMEID=umu-<appid>`.

---

## Rozwiązywanie problemów

- **Szybka awaria na Wayland lub DX12:** Otwórz zakładkę **Logs & Recovery** w `steam-auto-ui` (lub uruchom `steam-auto-run --last-log APPID`) i włącz tryb bezpieczny (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), albo uruchom grę z `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Gry z anti-cheat nie uruchamiają się:** Użyj `proton-cachyos-slr` (Steam Linux Runtime) i uruchom `steam-auto-run --doctor`, aby zweryfikować EAC v2, `/dev/ntsync` oraz `vm.max_map_count`.
- **Steam przywraca stare opcje uruchamiania:** Całkowicie zamknij Steam przed wywołaniem `steam-auto-sync` lub `steam-auto-sync --sanitize`.
- **Błędny lub brakujący limit VRR:** Ustaw jawnie `VRR_CAP=<fps>`, wpisz `VRR_CAP=0`, aby go wyłączyć, lub użyj `VRR_MINUS_MARGIN=1` dla zapasu `-6%`. W sesji Gamescope tylko jawnie ustawione `VRR_CAP` eksportuje limity DXVK/VKD3D.
- **Weryfikacja QoS sieciowego:** Uruchom `steam-net-boost status` (bez uprawnień roota, tylko do odczytu). Jeśli chcesz korzystać z automatycznego sesyjnego QoS, zainstaluj pomocnik root poleceniem `./install.sh --with-net-boost`.

Zobacz także [English User Guide](../../USER_GUIDE.md), [ARCHITECTURE.md](../../ARCHITECTURE.md) oraz [i18n Index](../README.md) ze wszystkimi 27 wersjami językowymi.
