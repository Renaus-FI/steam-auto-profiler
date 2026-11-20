# Steam Auto-Profiler пайдаланушы нұсқаулығы

Толық техникалық ақпарат [ағылшын тіліндегі нұсқаулықта](../../USER_GUIDE.md).

## Орнату

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` қосымша желілік QoS көмекшісін орнатады. `--compat-cachy-run` бар `/usr/local/bin/cachy-run` файлын `.bak` ретінде сақтап, үйлесімділік shim орнатады. `--with-auto-sync` systemd пайдаланушы watcher орнатады. `--uninstall` компоненттерді өшіреді.

## Қалай жұмыс істейді

`steam-auto-detect` Steam манифесттері мен кітапханаларынан AppID іздейді, ойын каталогын он деңгейге дейін сканерлейді және басымдық ретімен жіктейді: `competitive-anticheat`, содан кейін нативті FSR/FidelityFX (`native-fsr4`/`native-fsr`), содан кейін `legacy-upscaler`, әйтпесе `standard`.

`steam-auto-run` AppID-ді `SteamAppId`, `STEAM_COMPAT_APP_ID` және `GAMEID` арқылы шешіп, `umu-` префиксін алып тастайды. Ол `kdialog` немесе `zenity` көрсете алады және параметрлерді `~/.config/steam-auto-profiler/profiles/<APPID>.env` ішіне сақтайды.

Үйлесімділік параметрлері бар мәндер сақталғанда `PROTON_ADD_CONFIG` және `STEAM_COMPAT_CONFIG` ішіне жазылады. Токендер: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Steam автоматизациясы

Steam іске қосу опциясына:

```text
steam-auto-run %command%
```

UMU үшін: `GAMEID=umu-2357570 steam-auto-run %command%`. `localconfig.vdf` өзгертер алдында Steam-тен толығымен шығыңыз.

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` — `--sanitize` баламасы, `--remove` wrapper алып тастайды, `--print-library-paths` кітапханаларды көрсетеді, `--keep-backups N` сақтық көшірме санын береді (`0` барлығын сақтайды).

Watcher `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` орындайды. Units орнату: `steam-auto-sync --install-systemd`.

## Командалар мен айнымалылар

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Негізгі айнымалылар: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` басым. Оны көрсетпесе, `kscreen-doctor`, `wlr-randr` немесе `xrandr` жиілікті анықтайды; 60 Гц-тен жоғары жағдайында 94% шегі қолданылады. Gamescope-те нақты `VRR_CAP` болмаса DXVK/VKD3D шектері қосылмайды.

Желі профилі үшін `--with-net-boost` орнатыңыз немесе `NETOPT=1` пайдаланыңыз. `steam-net-boost` CAKE немесе `fq_codel` қолданып, EEE мен tx queue length уақытша өзгертеді де соңғы сеанс аяқталған соң қайтарады: `sudo steam-net-boost status [IFACE]`.
