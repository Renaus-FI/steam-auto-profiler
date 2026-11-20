# Podręcznik Steam Auto-Profiler

Ten przewodnik opisuje instalację i codzienne używanie. Szczegóły techniczne znajdziesz w [przewodniku angielskim](../../USER_GUIDE.md).

## Instalacja

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` instaluje opcjonalnego pomocnika QoS sieci. `--compat-cachy-run` zachowuje istniejący `/usr/local/bin/cachy-run` jako `.bak` i instaluje shim. `--with-auto-sync` konfiguruje użytkowy watcher systemd. `--uninstall` usuwa zainstalowane elementy.

## Jak działa

`steam-auto-detect` wyszukuje AppID w manifestach i bibliotekach Steam, skanuje katalog gry do dziesięciu poziomów i stosuje kolejność: (1) `competitive-anticheat`, (2) natywne FSR/FidelityFX (`native-fsr4`/`native-fsr`), (3) `legacy-upscaler`, (4) `standard`.

`steam-auto-run` rozwiązuje AppID z `SteamAppId`, `STEAM_COMPAT_APP_ID` i `GAMEID`, usuwając prefiks `umu-`. Może wyświetlić `kdialog` lub `zenity` i zapisać profil w `~/.config/steam-auto-profiler/profiles/<APPID>.env`. Profil to `KEY=VALUE`; nieznane klucze i składnia powłoki są ignorowane.

Ustawienia kompatybilności trafiają do `PROTON_ADD_CONFIG` i `STEAM_COMPAT_CONFIG` przy zachowaniu wartości użytkownika. Ważne tokeny: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire` i `vkreflex`.

## Automatyzacja Steam

Opcje uruchamiania Steam:

```text
steam-auto-run %command%
```

Dla UMU: `GAMEID=umu-2357570 steam-auto-run %command%`.

Przed zmianą `localconfig.vdf` całkowicie zamknij Steam:

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` to alias `--sanitize`; `--remove` usuwa wrapper; `--print-library-paths` pokazuje biblioteki; `--keep-backups N` zachowuje N kopii (`0` wszystkie).

Watcher uruchamia `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`. Jednostki zainstaluj przez `steam-auto-sync --install-systemd`.

## Polecenia i zmienne

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Najważniejsze zmienne: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` ma najwyższy priorytet. Bez niego używane są `kscreen-doctor`, `wlr-randr` lub `xrandr`; ponad 60 Hz limit wynosi 94 % częstotliwości. W Gamescope limity DXVK/VKD3D są ustawiane tylko przy `VRR_CAP`.

## Sieć i rozwiązywanie problemów

Przy `NETOPT=1` lub `netopt` program `steam-net-boost` używa CAKE lub `fq_codel`, tymczasowo zmienia EEE i tx queue length. Po zakończeniu ostatniej sesji przywraca stan poprzedni.

Status: `sudo steam-net-boost status [IFACE]`. Przed synchronizacją zamknij Steam. Przy błędnym profilu użyj `FORCE_GUI=1` lub `--reset APPID`. Dla anti-cheat wybierz `proton-cachyos-slr` i sprawdź system przez `--doctor`.
