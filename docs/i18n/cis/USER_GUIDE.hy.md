# Steam Auto-Profiler օգտագործողի ուղեցույց

Լրիվ տեխնիկական տեղեկությունները տրված են [անգլերեն ուղեցույցում](../../USER_GUIDE.md)։

## Տեղադրում

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` տեղադրում է ընտրովի ցանցային QoS օգնականը։ `--compat-cachy-run` պահում է գոյություն ունեցող `/usr/local/bin/cachy-run`-ը որպես `.bak` և տեղադրում համատեղելիության shim։ `--with-auto-sync` տեղադրում է systemd օգտատիրոջ watcher։ `--uninstall` հեռացնում է բաղադրիչները։

## Ինչպես է այն աշխատում

`steam-auto-detect`-ը որոնում է AppID-ն Steam-ի manifest-ներում և գրադարաններում, սկանում է խաղի գրացուցակը մինչև տասը մակարդակ և դասակարգում նախապատվության կարգով՝ `competitive-anticheat`, հետո native FSR/FidelityFX (`native-fsr4`/`native-fsr`), հետո `legacy-upscaler`, հակառակ դեպքում `standard`։

`steam-auto-run`-ը AppID-ն որոշում է `SteamAppId`, `STEAM_COMPAT_APP_ID` և `GAMEID` աղբյուրներից՝ հեռացնելով `umu-` նախածանցը։ Կարող է ցուցադրել `kdialog` կամ `zenity` և պահել կարգավորումները `~/.config/steam-auto-profiler/profiles/<APPID>.env`ում։

Համատեղելիության տոքենները ավելացվում են `PROTON_ADD_CONFIG` և `STEAM_COMPAT_CONFIG`ում՝ պահպանելով գոյություն ունեցող արժեքները։ Օգտագործվում են `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`։

## Steam-ի ավտոմատացում

Steam-ի launch options-ում՝

```text
steam-auto-run %command%
```

UMU-ի համար՝ `GAMEID=umu-2357570 steam-auto-run %command%`։ `localconfig.vdf` փոփոխելուց առաջ ամբողջությամբ փակեք Steam-ը։

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean`-ը `--sanitize` այլանունն է, `--remove`-ը հեռացնում է wrapper-ը, `--print-library-paths`-ը ցուցադրում է գրադարանները, իսկ `--keep-backups N`-ը պահում է N պահուստային օրինակ (`0`՝ բոլորը)։

Watcher-ը կատարում է `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`։ Unit-երը տեղադրելու համար՝ `steam-auto-sync --install-systemd`։

## Հրամաններ և փոփոխականներ

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`։ JSON՝ `steam-auto-detect --inspect --json APPID`։

Հիմնական փոփոխականներ՝ `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`։

`VRR_CAP`-ը առաջնահերթ է։ Առանց դրա օգտագործվում են `kscreen-doctor`, `wlr-randr` կամ `xrandr` տվյալները. 60 Հց-ից բարձր է սահմանվում 94%։ Gamescope-ում DXVK/VKD3D սահմանափակումն ավելացվում է միայն explicit `VRR_CAP`ով։

Ցանցային պրոֆիլի համար տեղադրեք `--with-net-boost` կամ օգտագործեք `NETOPT=1`։ `steam-net-boost`-ը կիրառում է CAKE կամ `fq_codel`, ժամանակավորապես փոխում է EEE-ն և tx queue length-ը, ապա վերջին սեսիայի ավարտին վերականգնում է նախորդ վիճակը՝ `sudo steam-net-boost status [IFACE]`։
