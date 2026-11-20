# Дастури корбарии Steam Auto-Profiler

Маълумоти муфассали техникӣ дар [дастури англисӣ](../../USER_GUIDE.md) оварда шудааст.

## Насб

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` ёварии ихтиёрии QoS-и шабакаро насб мекунад. `--compat-cachy-run` `/usr/local/bin/cachy-run`-и мавҷударо ҳамчун `.bak` нигоҳ медорад ва shim-и мутобиқатро насб мекунад. `--with-auto-sync` watcher-и systemd-и корбарро насб мекунад. `--uninstall` ҷузъҳоро тоза мекунад.

## Чӣ тавр кор мекунад

`steam-auto-detect` AppID-ро дар манифестҳо ва китобхонаҳои Steam меҷӯяд, ҷузвдони бозиро то даҳ қадар санҷида, бо тартиби афзалият тасниф мекунад: `competitive-anticheat`, сипас FSR/FidelityFX-и native (`native-fsr4`/`native-fsr`), баъд `legacy-upscaler`, вагарна `standard`.

`steam-auto-run` AppID-ро аз `SteamAppId`, `STEAM_COMPAT_APP_ID` ва `GAMEID` муайян карда, пешванди `umu-`-ро ҳазф мекунад. Он метавонад `kdialog` ё `zenity` намоиш диҳад ва танзимотро дар `~/.config/steam-auto-profiler/profiles/<APPID>.env` нигоҳ дорад.

Танзимоти мувофиқатӣ бо нигоҳ доштани қиматҳои мавҷуд дар `PROTON_ADD_CONFIG` ва `STEAM_COMPAT_CONFIG` сабт мешаванд. Токенҳо: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Автоматизатсияи Steam

Дар имконотҳои запуски Steam:

```text
steam-auto-run %command%
```

Барои UMU: `GAMEID=umu-2357570 steam-auto-run %command%`. Пеш аз тағйири `localconfig.vdf` Steam-ро пурра пӯшед.

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` — алтернативаи `--sanitize`, `--remove` wrapper-ро тоза мекунад, `--print-library-paths` китобхонаҳоро нишон медиҳад, `--keep-backups N` шумораи нусхаи эҳтиётиро муайян мекунад (`0` ҳамаашро нигоҳ медорад).

Watcher фармони `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` иҷро мекунад. Unit-ҳо: `steam-auto-sync --install-systemd`.

## Фармонҳо ва тағйирёбандаҳо

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Тағйирёбандаҳои асосӣ: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` афзалият дорад. Бе он `kscreen-doctor`, `wlr-randr` ё `xrandr` истифода мешавад; аз 60 Гц боло маҳдудияти 94% татбиқ мегардад. Дар Gamescope лимити DXVK/VKD3D танҳо бо `VRR_CAP`-и ошкор илова мешавад.

Барои профили шабака `--with-net-boost` насб кунед ё `NETOPT=1` истифода баред. `steam-net-boost` CAKE ё `fq_codel`-ро татбиқ мекунад, EEE ва tx queue length-ро муваққатан тағйир медиҳад ва пас аз анҷоми сессияи охирин ҳолати пешинаро барқарор мекунад: `sudo steam-net-boost status [IFACE]`.
