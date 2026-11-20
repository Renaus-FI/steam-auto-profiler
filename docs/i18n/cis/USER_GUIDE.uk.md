# Посібник користувача Steam Auto-Profiler

Повні технічні відомості наведено в [англійському посібнику](../../USER_GUIDE.md).

## Встановлення

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` встановлює необов'язковий помічник мережевого QoS. `--compat-cachy-run` зберігає `/usr/local/bin/cachy-run` як `.bak` і встановлює shim сумісності. `--with-auto-sync` налаштовує користувацький watcher systemd. `--uninstall` видаляє компоненти.

## Принцип роботи

`steam-auto-detect` шукає AppID у маніфестах і бібліотеках Steam, переглядає папку гри до десяти рівнів і класифікує за пріоритетом: `competitive-anticheat`, нативний FSR/FidelityFX (`native-fsr4`/`native-fsr`), `legacy-upscaler`, а потім `standard`.

`steam-auto-run` визначає AppID через `SteamAppId`, `STEAM_COMPAT_APP_ID` і `GAMEID`, прибираючи префікс `umu-`. Він може показати `kdialog` або `zenity` та зберегти профіль у `~/.config/steam-auto-profiler/profiles/<APPID>.env`.

Параметри сумісності передаються в `PROTON_ADD_CONFIG` і `STEAM_COMPAT_CONFIG` зі збереженням наявних значень. Токени: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Автоматизація Steam

У параметрах запуску Steam:

```text
steam-auto-run %command%
```

Для UMU: `GAMEID=umu-2357570 steam-auto-run %command%`.

Повністю закрийте Steam перед зміною `localconfig.vdf`:

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` є псевдонімом `--sanitize`; `--remove` видаляє wrapper; `--print-library-paths` показує бібліотеки; `--keep-backups N` задає резервні копії (`0` зберігає всі).

Watcher виконує `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`. Units можна встановити через `steam-auto-sync --install-systemd`.

## Команди та змінні

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Змінні: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` має найвищий пріоритет. Інакше використовуються частота з `kscreen-doctor`, `wlr-randr` або `xrandr`; понад 60 Гц межа становить 94 %. У Gamescope DXVK/VKD3D-обмеження не додаються без явного `VRR_CAP`.

Для мережі встановіть `--with-net-boost` або увімкніть `NETOPT=1`. `steam-net-boost` застосовує CAKE або `fq_codel`, тимчасово змінює EEE й tx queue length і відновлює стан після останньої сесії: `sudo steam-net-boost status [IFACE]`.
