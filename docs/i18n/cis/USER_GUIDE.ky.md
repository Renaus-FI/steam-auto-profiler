# Steam Auto-Profiler колдонуучу колдонмосу

Толук техникалык маалымат [англисче колдонмодо](../../USER_GUIDE.md).

## Орнотуу

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` кошумча тармактык QoS жардамчысын орнотот. `--compat-cachy-run` учурдагы `/usr/local/bin/cachy-run` файлын `.bak` катары сактап, совместимдүүлүк shim орнотот. `--with-auto-sync` systemd колдонуучу watcher орнотот. `--uninstall` компоненттерди өчүрөт.

## Кантип иштейт

`steam-auto-detect` Steam манифесттери жана китепканаларынан AppID издейт, оюн каталогун он деңгээлге чейин сканерлейт жана артыкчылык ырааттуулугу боюнча классификациялайт: `competitive-anticheat`, андан кийин native FSR/FidelityFX (`native-fsr4`/`native-fsr`), андан кийин `legacy-upscaler`, болбосо `standard`.

`steam-auto-run` AppIDди `SteamAppId`, `STEAM_COMPAT_APP_ID` жана `GAMEID` аркылуу аныктайт, `umu-` префиксин алып салат. Ал `kdialog` же `zenity` көрсөтүп, тандооңузду `~/.config/steam-auto-profiler/profiles/<APPID>.env` ичинде сактай алат.

Шайкештик параметрлерин бар маанилер сакталган учурда `PROTON_ADD_CONFIG` жана `STEAM_COMPAT_CONFIG` ичине кошот. Токендер: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Steam автоматташтыруу

Steam иштетүү параметрине:

```text
steam-auto-run %command%
```

UMU үчүн: `GAMEID=umu-2357570 steam-auto-run %command%`. `localconfig.vdf` өзгөртүүдөн мурун Steamди толук жабыңыз.

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` — `--sanitize` псевдоними, `--remove` wrapper өчүрөт, `--print-library-paths` китепканаларды көрсөтөт, `--keep-backups N` резервдик нуска санын берет (`0` баарын сактайт).

Watcher `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` аткарат. Unit орнотуу: `steam-auto-sync --install-systemd`.

## Командалар жана өзгөрмөлөр

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Негизги өзгөрмөлөр: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` артыкчылыкка ээ. Ал жокто `kscreen-doctor`, `wlr-randr` же `xrandr` жыштыгын аныктайт; 60 Гцдан жогору 94% чеги колдонулат. Gamescopeте DXVK/VKD3D чеги так `VRR_CAP` көрсөтүлгөндө гана кошулат.

Тармак профили үчүн `--with-net-boost` орнотуңуз же `NETOPT=1` колдонуңуз. `steam-net-boost` CAKE же `fq_codel` колдонот, EEE жана tx queue length убактылуу өзгөртөт, акыркы сеанс аяктагандан кийин мурунку абалга кайтараат: `sudo steam-net-boost status [IFACE]`.
