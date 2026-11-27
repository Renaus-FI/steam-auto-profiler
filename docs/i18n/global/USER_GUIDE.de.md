# Steam Auto-Profiler Benutzerhandbuch

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Dieses Handbuch behandelt die vollständige Installation, Flatscreen- und VR-Start-Orchestrierung, das Kontrollzentrum `steam-auto-ui`, die Bibliothekssynchronisierung, Benchmarking und die Fehlerbehebung für **Steam Auto-Profiler v2.0**.

Steam Auto-Profiler ist ein schlanker Bash/Python-Launcher samt Kontrollzentrum für Linux, der eine Steam-AppID (oder eine Non-Steam-Verknüpfung) analysiert, ein kontextbewusstes Profil mit strengen Treiber-, Upscaler- und Anti-Cheat-Schutzmechanismen anwendet und anschließend den bestehenden Spielbefehl startet. Es bündelt oder injiziert niemals eine Drittanbieter-Proton-Runtime.

---

## Voraussetzungen

- Linux-Desktop-Sitzung (KDE Plasma 6 / Wayland, GNOME, wlroots oder X11), Bash 5+, Python 3.10+, Steam sowie Standard-Systemwerkzeuge.
- Optionale native GUI für das Kontrollzentrum: `PyQt6` oder `PySide6` (fällt automatisch auf die abhängigkeitsfreie `curses`-TUI aus der Python-Standardbibliothek zurück).
- Optionale Vorab-Checklisten-Dialoge vor dem Spielstart: `kdialog` oder `zenity`.
- Optionales stilles Frametime-Benchmarking: `mangohud`.
- Optionaler Sitzungs-Netzwerkhelfer: `tc`, `ip` und `ethtool` (`sudo` wird nur während der Installation mit `--with-net-boost` benötigt).

---

## Installation & Aktualisierungen

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` kopiert alle sechs ausführbaren Dateien (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` und `steam-auto-ui`) nach `~/.local/bin`, installiert den Desktop-Eintrag (`~/.local/share/applications/steam-auto-profiler.desktop`), legt `~/.config/steam-auto-profiler/profiles` an und ergänzt Standard-vkBasalt-Presets (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Stelle sicher, dass `~/.local/bin` in `PATH` enthalten ist.

Optionale Installations-Flags können kombiniert werden:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: installiert `/usr/local/bin/steam-net-boost` (sowie Systemkopien der übrigen Skripte) und eine eng begrenzte, passwortlose `sudoers`-Regel für `steam-net-boost`.
- `--compat-cachy-run`: sichert ein bestehendes `/usr/local/bin/cachy-run` als `/usr/local/bin/cachy-run.bak` (sofern es nicht bereits der Steam Auto-Profiler-Shim ist) und installiert einen Weiterleitungs-Shim auf `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): installiert und aktiviert den systemd-Benutzer-Watcher `steam-auto-profiler-sync.path` samt zugehörigem Oneshot-Dienst für alle erkannten Steam-Bibliotheken.
- `--uninstall`: entfernt installierte Binärdateien, Desktop-Eintrag, optionalen Netzwerkhelfer/sudoers-Regel, Kompatibilitäts-Shim und die systemd-Benutzereinheiten für Auto-Sync.

Zum Aktualisieren eines vorhandenen Klons:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Systembereitschaft vor der Synchronisierung prüfen:

```bash
steam-auto-run --doctor
```

---

## End-to-End-Startpipeline

1. **AppID-Auflösung:** Prüft `SteamAppId`, `STEAM_COMPAT_APP_ID` und danach `GAMEID` (entfernt ein etwaiges `umu-`-Präfix für Lutris/Heroic/UMU).
2. **Bibliotheks- & Verknüpfungserkennung:** `steam-auto-detect` durchsucht Steam-Stammverzeichnisse und sekundäre Bibliotheken aus `libraryfolders.vdf`, liest `appmanifest_<APPID>.acf` oder greift schreibgeschützt auf binäre `userdata/*/config/shortcuts.vdf` zurück und führt anschließend ein Single-Pass-`find` bis zu einer Tiefe von 10 Ebenen aus (unter Auslassung von `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Fünfstufige Klassifizierungsrangfolge:**
   - **1. `competitive-anticheat`:** Bekannte kompetitive AppID oder erkannte Anti-Cheat-Runtime (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE usw.). Deaktiviert OptiScaler, MLFG, vkBasalt und asynchrones DXVK; aktiviert Low-Latency und Sitzungs-Netzwerk-QoS.
   - **2. `vr`:** Erkannte `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` oder `vr-run`/`-vr`-Verknüpfungs-Flags. Exportiert `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** Modulares FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Aktiviert das treiberseitige FSR4-Upgrade (`PROTON_FSR4_UPGRADE=1` bzw. `PROTON_FSR4_RDNA3_UPGRADE=1` auf AMD RDNA 3).
   - **4. `legacy-upscaler`:** Ältere DLSS- (`nvngx_dlss*.dll`), XeSS- (`libxess*.dll`), Streamline- (`sl.interposer.dll`) oder FSR-2/3.0-DLLs. Setzt `AUTO_OPTISCALER=1` und befüllt die Hinweise in `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Sicheres natives Wine-Wayland-Profil mit Low-Latency-VRR.
4. **VRR-Bildwiederholraten-Begrenzung:** Ein explizites `VRR_CAP=<fps>` hat immer Vorrang (`VRR_CAP=0` deaktiviert die Begrenzung). Andernfalls wird die aktive Bildschirmfrequenz über `kscreen-doctor` (KDE Plasma 6 aktiver `*`-Modus oder klassisches `Hz`), `wlr-randr` oder `xrandr` ermittelt und standardmäßig 1:1 angewendet (`240 FPS` bei 240 Hz). Mit `VRR_MINUS_MARGIN=1` wird die optionale VRR-Sicherheitsreserve von `-6%` aktiviert (`hz * 94 / 100`, z. B. `225 FPS` bei 240 Hz). In Gamescope-Sitzungen werden DXVK/VKD3D-Limits weggelassen, sofern `VRR_CAP` nicht explizit gesetzt ist.
5. **Schutzmechanismen gegen Konflikte (Mutual-Exclusion):**
   - **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` wird erzwungen, sobald `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` oder `USE_OPTISCALER=1` aktiv ist (verhindert doppeltes Nachschärfen und HDR10-Clipping).
   - **MLFG + Low-Latency / VRR-Caps:** `MLFG=1` (`USE_MLFG=1`) exportiert `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, entfernt `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` sowie `DXVK_FRAME_PACE` und exportiert auf AMD RDNA 3 `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`. Wenn `USE_MLFG=0` und ein VRR-Cap aktiv ist, wird `DXVK_FRAME_PACE=low-latency-vrr` exportiert.
   - **Modernes DX12 + Safe DX12:** Exportiert `PROTON_NATIVE_AGS=1` auf AMD sowie `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, wenn `USE_SAFEDX12=0` ist (wird bei `SAFEDX12=1` sauber ausgelassen).
6. **Zuordnung der Compat-Tokens:** Verwaltete Funktionen werden ohne Überschreiben vorhandener Benutzerwerte sowohl an `PROTON_ADD_CONFIG` als auch an `STEAM_COMPAT_CONFIG` angehängt: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Automatisches KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** Außerhalb von Gamescope und bei `DXVK_HDR=1` (oder `USE_HDR=1`) wird der primäre aktivierte Ausgang über `kscreen-doctor -o` abgefragt; ist HDR deaktiviert, wird es vor dem Start eingeschaltet und per `EXIT`/`INT`/`TERM`-Trap wieder auf SDR zurückgestellt.
8. **Stilles Frametime-Benchmarking (`BENCH=1`):** Startet MangoHud im verdeckten CSV-Modus (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), wertet die Frametimes nach Beendigung aus, hängt `Avg FPS`, `1% Low FPS` und `P99 (ms)` an `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` an und entfernt temporäre CSV-Dateien.
9. **Safe-Mode-Autowiederherstellung bei Schnellabsturz:** Beendet sich ein Proton/Windows-Spiel in unter `20s` (konfigurierbar über `SAP_CRASH_THRESHOLD_SEC`) mit einem Exit-Code ungleich Null, während experimentelle Wayland- oder DX12-Flags aktiv sind (`USE_XWAYLAND=0` oder `USE_SAFEDX12=0`), wird ein `crash_hint` in `last-<APPID>.log` und `last-launch.log` protokolliert und (bei aktiver GUI) angeboten, `USE_XWAYLAND=1` + `USE_SAFEDX12=1` für den nächsten Start zu speichern.
10. **Scheduler- & Netzwerk-Lebenszyklus:** Läuft über `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (nur wenn `ananicy-cpp.service` inaktiv ist) -> direkte Ausführung, optional mit `PRIME=1` (`prime-run`). Bei `USE_NET_OPT=1` führt `steam-net-boost` referenzgezähltes `on`/`off` mit `flock` aus und bewahrt dabei statische Root-CAKE- sowie HTB + Leaf-CAKE-Hierarchien.

---

## Einheitliches Kontrollzentrum (`steam-auto-ui`)

Starte `steam-auto-ui` über das Anwendungsmenü, via `steam-auto-run --ui` oder direkt:

```bash
steam-auto-ui                 # Erkennt automatisch Qt6-GUI (PyQt6/PySide6) oder curses-TUI
steam-auto-ui --gui           # Erzwingt das native Qt6-GUI-Fenster
steam-auto-ui --tui           # Erzwingt die stdlib-curses-TUI (funktioniert über SSH)
steam-auto-ui --lang fi       # Start mit expliziter UI-Sprache (27 Sprachen unterstützt)
steam-auto-ui --check         # Headless-Selbstprüfung (gibt JSON-Diagnose aus)
```

`steam-auto-ui` erkennt die System-Locale automatisch über `LC_ALL` / `LC_MESSAGES` / `LANG` und bietet in der Qt6-GUI ein Live-Sprachauswahl-Dropdown (sowie das Tastenkürzel `L` in der `curses`-TUI), um zur Laufzeit ohne Neustart zwischen allen 27 Sprachen zu wechseln.

### Fünf synchronisierte Ansichten

1. **Spiele & Profile:** Filterbare Tabelle aller Steam-Titel und schreibgeschützter Non-Steam-`shortcuts.vdf`-Einträge (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), Upscaler-SDK-Badge (`AUTO_UPSCALER_INFO`), Live-Validierung gegenseitiger Ausschlüsse über alle 10 Profilschalter + `VRR_CAP`, `Dry-Run Preview`, Direkt-Sprung zu `Benchmarks` sowie `Reset Profile`.
2. **System & Telemetrie:** Nicht-blockierende Live-Anzeige von `steam-auto-run --doctor`, `scxctl get` / `sched_ext`-Status, installierten Stack-Versionen (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), Shader-Cache-Belegung (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), git/AUR-Downgrade-Warnungen aus `/var/log/pacman.log`, GPU-VRAM/Auslastung/Temperatur, `tc -s qdisc` LAN- (`10:`) vs. WAN- (`20:`/root) Durchsatz und `av_delay` sowie `vr-mode status`.
3. **Bibliothekssynchronisierung:** Live-Warnbanner für laufendes Steam plus Ein-Klick-Aktionen für `--report`, `--sanitize --dry-run`, `--sanitize` (bei laufendem Steam gesperrt) und `--migrate-cachy-run`.
4. **Protokolle & Wiederherstellung:** Durchsuche `last-launch.log` und `last-<APPID>.log`, prüfe `crash_hint`-Warnungen und aktiviere per Klick den Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarks:** Filterbare Vergleichstabelle der Frametime-Messungen aus `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR-Orchestrierung (`vr-run`)

Setze in Steam unter **Eigenschaften > Allgemein > Startoptionen** für VR-Titel:

```text
vr-run %command%
```

- Bereinigt geerbte Flatscreen-Überschreibungen (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Wählt über `MESA_VK_DEVICE_SELECT` automatisch die dedizierte GPU mit dem größten VRAM und setzt auf AMD-GPUs `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`.
- Ermittelt dynamisch WiVRn- und xrizer-OpenXR/OpenVR-Pfade (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) und konfiguriert `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` sowie `LD_LIBRARY_PATH`, ohne explizite Benutzerwerte zu überschreiben.
- Führt referenzgezähltes `vr-mode on` / `vr-mode off` in `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (mit `flock`) aus, sofern `vr-mode` installiert ist (`VR_AUTO_MODE=0` deaktiviert dies).
- Nutzt dieselbe `ananicy-cpp`-bewusste Scheduler-Kette (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> direktes `exec`).
- Aufgelöste Variablen jederzeit vorab prüfen mit `vr-run --dry-run`.

`steam-auto-run` umgeht SteamVR (`250820`) und `-vr`/`--vr`-Starts automatisch, und `steam-auto-sync` weist VR-Titeln automatisch `vr-run %command%` zu und behält es bei.

---

## Steam-Bibliothekssynchronisierung (`steam-auto-sync`)

Schließe Steam vollständig, bevor in `localconfig.vdf` geschrieben wird:

```bash
steam-auto-sync --report              # Schreibgeschütztes Audit von Bibliothek + shortcuts.vdf
steam-auto-sync --print-library-paths # Alle erkannten Steam-Bibliotheken anzeigen
steam-auto-sync --dry-run             # Änderungen vorab anzeigen
steam-auto-sync                       # steam-auto-run / vr-run eintragen
steam-auto-sync --sanitize --dry-run  # Bereinigung veralteter Flags vorab anzeigen
steam-auto-sync --sanitize            # Veraltete/verwaiste Flags bereinigen (Alias: --clean)
steam-auto-sync --migrate-cachy-run   # Alte cachy-run-Profile migrieren
steam-auto-sync --remove              # steam-auto-run-Wrapper entfernen
```

- Zeitgestempelte Sicherungen `localconfig.vdf.bak.*` werden über `--keep-backups N` automatisch bereinigt (Standard `10`; `0` behält alle).
- Schließe einzelne AppIDs aus, indem du sie zeilenweise (`#`-Kommentare erlaubt) in `~/.config/steam-auto-profiler/ignore_appids.txt` einträgst.
- Der systemd-Auto-Sync-Watcher (`./install.sh --with-auto-sync` oder `steam-auto-sync --install-systemd`) führt bei Änderungen an Steam-Manifesten `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` aus.

---

## CLI- & Profilreferenz

### Befehle

| Zweck | Befehl |
| --- | --- |
| Systembereitschaft prüfen | `steam-auto-run --doctor` (Alias `--check-system`) |
| Kontrollzentrum starten (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` oder `steam-auto-run --ui` |
| Spiel inspizieren (lesbar) | `steam-auto-run --inspect APPID` |
| Spiel inspizieren (JSON) | `steam-auto-detect --inspect --json APPID` |
| Profil interaktiv neu konfigurieren | `steam-auto-run --configure APPID` |
| Aufgelöste Startumgebung anzeigen | `steam-auto-run --dry-run APPID` |
| Gespeichertes Profil zurücksetzen | `steam-auto-run --reset APPID` |
| Gespeicherte Profile auflisten | `steam-auto-run --list-profiles` |
| Letztes Startprotokoll anzeigen | `steam-auto-run --last-log [APPID]` |
| VR-Startumgebung vorab anzeigen | `vr-run --dry-run` |
| Netzwerkhelfer prüfen (schreibgeschützt) | `steam-net-boost status [IFACE]` |

### Gespeicherte `.env`-Profilschlüssel & Umgebungs-Overrides

Profildateien liegen unter `~/.config/steam-auto-profiler/profiles/<APPID>.env` und akzeptieren ein Allowlist-Format `KEY=VALUE` (Shell-Befehlssubstitutionen und unbekannte Schlüssel werden sicher ignoriert):

| `.env`-Schlüssel | Umgebungs-Override | Wirkung |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Erzwingt XWayland statt nativem Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | Deaktiviert das treiberseitige FSR-4-Upgrade (Standard `1`) |
| `USE_MLFG=1` | `MLFG=1` | Aktiviert Frame Generation (deaktiviert Anti-Lag, Low-Latency und VRR-Caps) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Aktiviert die OptiScaler-Brücke (bei `competitive-anticheat` gesperrt) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Aktiviert vkBasalt-Nachschärfung (deaktiviert bei aktivem FSR 4 oder OptiScaler) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Lässt experimentelle `VKD3D_CONFIG`-Flags und das Token `vkd3dbindlesstb` weg |
| `USE_NET_OPT=1` | `NETOPT=1` | Aktiviert Sitzungs-Netzwerk-QoS über `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Bevorzugt native SDL- / Steam-Input-Emulation |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Behält Steam-Overlay-`LD_PRELOAD` bei |
| `USE_CEF_FIX=1` | `CEF=1` | Hängt `--in-process-gpu` für CEF-Launcher an |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Deaktiviert NTSync für ältere Titel |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Deaktiviert Fenstermanager-Dekorationen |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Benutzerdefiniertes DXVK/VKD3D-FPS-Limit (`0` deaktiviert das Limit) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Wendet `-6%` Spielraum zur Monitor-Refresh-Rate an (z. B. `225 FPS` bei 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Erlaubt Tastenkürzel-Inhibition unter Wine Wayland (Standard `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Aktiviert KDE Plasma 6 HDR beim Start automatisch und stellt beim Beenden SDR wieder her |
| — | `BENCH=1`, `BENCH_DURATION=60` | Führt einen stillen MangoHud-CSV-Benchmark aus und speichert eine JSON-Zusammenfassung |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Unterdrückt oder erzwingt die Vorab-Checkliste über `kdialog`/`zenity` |
| — | `FSR_HUD=1` | Exportiert HUD-Indikatorvariablen für FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Hängt `-vulkan` an / umschließt den Start mit `prime-run` |
| — | `GAMEID=umu-<appid>` | Löst UMU- / Lutris- / Heroic-AppIDs auf |

---

## Lutris, Heroic, Faugus & UMU

- **Lutris:** Erweiterte Optionen aktivieren, `proton-cachyos-slr` (oder deinen Proton-Build) wählen, Lutris-Runtime deaktivieren, Systembibliotheken bevorzugen und als Befehlspräfix `steam-auto-run` eintragen.
- **Heroic / Faugus:** `proton-cachyos-slr` auswählen und `steam-auto-run` als Wrapper/Befehlspräfix hinzufügen.
- **UMU / Protonfixes:** Bei Bedarf `PROTON_VERB=waitforexitandrun` und `GAMEID=umu-<appid>` exportieren.

---

## Fehlerbehebung

- **Schnellabsturz unter Wayland oder DX12:** Öffne **Protokolle & Wiederherstellung** in `steam-auto-ui` (oder führe `steam-auto-run --last-log APPID` aus) und aktiviere den Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), oder starte mit `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Anti-Cheat-Titel starten nicht:** Verwende `proton-cachyos-slr` (Steam Linux Runtime) und prüfe mit `steam-auto-run --doctor` EAC v2, `/dev/ntsync` und `vm.max_map_count`.
- **Steam setzt Startoptionen zurück:** Beende Steam vollständig, bevor du `steam-auto-sync` oder `steam-auto-sync --sanitize` ausführst.
- **Falsches oder fehlendes VRR-Limit:** Setze `VRR_CAP=<fps>` explizit, `VRR_CAP=0` zum Deaktivieren oder `VRR_MINUS_MARGIN=1` für `-6%` Reserve. Unter Gamescope exportiert nur ein explizites `VRR_CAP` DXVK/VKD3D-Limits.
- **Netzwerk-QoS prüfen:** Führe `steam-net-boost status` aus (unprivilegiert, schreibgeschützt). Installiere den Root-Helfer mit `./install.sh --with-net-boost`, wenn automatisches Sitzungs-QoS gewünscht ist.

Weitere Architekturdetails findest du in [ARCHITECTURE.md](../../ARCHITECTURE.md), das englische Original im [English User Guide](../../USER_GUIDE.md) und alle 27 Sprachversionen im [i18n Index](../README.md).
