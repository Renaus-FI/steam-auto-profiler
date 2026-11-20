# Дапаможнік карыстальніка Steam Auto-Profiler

Поўныя тэхнічныя звесткі глядзіце ў [англамоўным даведніку](../../USER_GUIDE.md).

## Усталяванне

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` усталёўвае дадатковы сеткаваны QoS-памочнік. `--compat-cachy-run` захоўвае `/usr/local/bin/cachy-run` як `.bak` і ставіць shim сумяшчальнасці. `--with-auto-sync` наладжвае карыстальніцкі watcher systemd. `--uninstall` выдаляе кампаненты.

## Прынцып працы

`steam-auto-detect` шукае AppID у маніфестах і бібліятэках Steam, аглядае каталог гульні да дзесяці ўзроўняў і класіфікуе ў парадку прыярытэту: `competitive-anticheat`, натыўны FSR/FidelityFX (`native-fsr4`/`native-fsr`), `legacy-upscaler`, потым `standard`.

`steam-auto-run` вызначае AppID праз `SteamAppId`, `STEAM_COMPAT_APP_ID` і `GAMEID`, выдаляючы прэфікс `umu-`. Ён можа паказаць `kdialog` або `zenity` і захаваць налады ў `~/.config/steam-auto-profiler/profiles/<APPID>.env`.

Налады сумяшчальнасці запісваюцца ў `PROTON_ADD_CONFIG` і `STEAM_COMPAT_CONFIG` са захаваннем існых значэнняў. Токены: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Аўтаматызацыя Steam

У параметрах запуску Steam:

```text
steam-auto-run %command%
```

Для UMU: `GAMEID=umu-2357570 steam-auto-run %command%`. Перад запісам у `localconfig.vdf` поўнасцю закрыйце Steam.

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` — альтэрнатыва `--sanitize`; `--remove` выдаляе wrapper; `--print-library-paths` паказвае бібліятэкі; `--keep-backups N` задае колькасць рэзервовых копій (`0` захоўвае ўсе).

Watcher выконвае `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`. Устаноўка units: `steam-auto-sync --install-systemd`.

## Каманды і зменныя

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Асноўныя зменныя: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` мае найвышэйшы прыярытэт. Інакш бяруцца дадзеныя `kscreen-doctor`, `wlr-randr` або `xrandr`; вышэй за 60 Гц мяжа складае 94 %. У Gamescope межы DXVK/VKD3D не дадаюцца без явнага `VRR_CAP`.

Для сеткавага профілю ўжывайце `--with-net-boost` або `NETOPT=1`. `steam-net-boost` ужывае CAKE або `fq_codel`, часова мяняе EEE і tx queue length, потым аднаўляе стан: `sudo steam-net-boost status [IFACE]`.
