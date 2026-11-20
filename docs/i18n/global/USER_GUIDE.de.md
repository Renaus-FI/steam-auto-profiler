# Benutzerhandbuch für Steam Auto-Profiler

Diese Anleitung fasst Installation und vollständigen Ablauf zusammen. Technische Details stehen in der [englischen Anleitung](../../USER_GUIDE.md).

## Installation

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` installiert den optionalen Netzwerk-QoS-Helfer. `--compat-cachy-run` bewahrt `/usr/local/bin/cachy-run` als `.bak` und installiert den Kompatibilitäts-Shim. `--with-auto-sync` richtet den systemd-Benutzer-Watcher ein. `--uninstall` entfernt alle installierten Komponenten.

## Arbeitsablauf

`steam-auto-detect` sucht AppIDs in Steam-Manifesten und Bibliotheken, prüft das Spielverzeichnis bis in zehn Ebenen und verwendet diese Priorität: (1) `competitive-anticheat`, (2) natives FSR/FidelityFX (`native-fsr4`/`native-fsr`), (3) `legacy-upscaler`, (4) `standard`.

`steam-auto-run` löst die AppID über `SteamAppId`, `STEAM_COMPAT_APP_ID` und `GAMEID` auf; der Präfix `umu-` wird entfernt. Es kann `kdialog` oder `zenity` öffnen und Einstellungen unter `~/.config/steam-auto-profiler/profiles/<APPID>.env` speichern. Das Profilformat ist `KEY=VALUE`; unbekannte Schlüssel werden ignoriert.

Kompatibilitätseinstellungen werden nach `PROTON_ADD_CONFIG` und `STEAM_COMPAT_CONFIG` übernommen. Bestehende Werte bleiben erhalten. Unterstützte Tokens sind `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire` und `vkreflex`.

## Steam-Automatisierung

Steam-Startoptionen:

```text
steam-auto-run %command%
```

Für UMU: `GAMEID=umu-2357570 steam-auto-run %command%`.

Steam vor Schreibzugriffen vollständig schließen:

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` ist ein Alias für `--sanitize`, `--remove` entfernt den Wrapper, `--print-library-paths` zeigt Bibliotheken, und `--keep-backups N` behält N Sicherungen (`0` alle).

Der Watcher führt `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` aus; die Einheiten lassen sich mit `steam-auto-sync --install-systemd` installieren.

## Befehle und Umgebungsvariablen

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON-Ausgabe: `steam-auto-detect --inspect --json APPID`.

Wichtige Variablen: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1` und `NO_NTSYNC=1`.

`VRR_CAP` hat Vorrang. Andernfalls werden `kscreen-doctor`, `wlr-randr` oder `xrandr` ausgewertet; über 60 Hz ergibt sich eine Obergrenze von 94 %. In Gamescope werden DXVK/VKD3D-Grenzen nur bei `VRR_CAP` exportiert.

## Netzwerk und Fehlersuche

Mit `NETOPT=1` oder `netopt` verwendet `steam-net-boost` CAKE oder `fq_codel`, ändert EEE vorübergehend und passt tx queue length an. Beim Ende der letzten Sitzung werden die Ausgangswerte wiederhergestellt.

Status: `sudo steam-net-boost status [IFACE]`. Bei Steam-Änderungen Steam vollständig schließen. Für ein falsches Profil `FORCE_GUI=1` oder `--reset APPID` verwenden. Bei Anti-Cheat-Titeln `proton-cachyos-slr` bevorzugen und mit `--doctor` prüfen.
