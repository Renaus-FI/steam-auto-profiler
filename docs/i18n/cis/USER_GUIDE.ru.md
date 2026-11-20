# Руководство пользователя Steam Auto-Profiler

Полные технические сведения приведены в [английском руководстве](../../USER_GUIDE.md).

## Установка

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` устанавливает необязательный помощник сетевого QoS. `--compat-cachy-run` сохраняет `/usr/local/bin/cachy-run` как `.bak` и ставит shim. `--with-auto-sync` включает пользовательский watcher systemd. `--uninstall` удаляет установленные компоненты.

## Как работает программа

`steam-auto-detect` ищет AppID в манифестах и библиотеках Steam, просматривает папку игры до десяти уровней и классифицирует по приоритету: `competitive-anticheat`, затем нативный FSR/FidelityFX (`native-fsr4`/`native-fsr`), затем `legacy-upscaler`, иначе `standard`.

`steam-auto-run` определяет AppID через `SteamAppId`, `STEAM_COMPAT_APP_ID` и `GAMEID`, удаляя префикс `umu-`. При первом запуске может показать `kdialog` или `zenity`, а выбранные параметры сохранить в `~/.config/steam-auto-profiler/profiles/<APPID>.env`.

Совместимость передаётся в `PROTON_ADD_CONFIG` и `STEAM_COMPAT_CONFIG` с сохранением существующих значений. Токены: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Настройка Steam

В параметрах запуска Steam:

```text
steam-auto-run %command%
```

Для UMU: `GAMEID=umu-2357570 steam-auto-run %command%`.

Перед записью в `localconfig.vdf` полностью закройте Steam:

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` заменяет `--sanitize`, `--remove` удаляет wrapper, `--print-library-paths` показывает библиотеки, `--keep-backups N` задаёт число резервных копий (`0` сохраняет все).

watcher выполняет `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`. Установить units отдельно можно командой `steam-auto-sync --install-systemd`.

## Команды и переменные

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Основные переменные: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` имеет приоритет. Без него используется частота из `kscreen-doctor`, `wlr-randr` или `xrandr`; выше 60 Гц применяется предел 94 %. В Gamescope ограничения DXVK/VKD3D не добавляются, если не задан `VRR_CAP`.

Для сетевого профиля установите `--with-net-boost`, используйте `NETOPT=1` или пункт `netopt`. `steam-net-boost` применяет CAKE или `fq_codel`, временно меняет EEE и tx queue length, а после завершения последней сессии восстанавливает прежнее состояние: `sudo steam-net-boost status [IFACE]`.
