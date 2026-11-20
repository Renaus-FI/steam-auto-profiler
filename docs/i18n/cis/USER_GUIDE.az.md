# Steam Auto-Profiler İstifadəçi Təlimatı

Tam texniki məlumatlar [ingilisdilli təlimatda](../../USER_GUIDE.md) verilmişdir.

## Quraşdırma

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` seçmə şəbəkə QoS köməkçisini quraşdırır. `--compat-cachy-run` mövcud `/usr/local/bin/cachy-run` faylını `.bak` kimi saxlayır və uyğunluq shimini quraşdırır. `--with-auto-sync` systemd istifadəçi watcherini quraşdırır. `--uninstall` komponentləri silir.

## Necə işləyir

`steam-auto-detect` Steam manifestləri və kitabxanalarında AppID axtarır, oyun qovluğunu 10 səviyyəyə qədər skan edir və prioritet sırası ilə təsnif edir: `competitive-anticheat`, sonra native FSR/FidelityFX (`native-fsr4`/`native-fsr`), sonra `legacy-upscaler`, əks halda `standard`.

`steam-auto-run` AppID-ni `SteamAppId`, `STEAM_COMPAT_APP_ID` və `GAMEID` vasitəsilə həll edir və `umu-` prefiksini çıxarır. O, `kdialog` və ya `zenity` göstərə və seçimləri `~/.config/steam-auto-profiler/profiles/<APPID>.env`də saxlaya bilər.

Uyğunluq tokenləri mövcud dəyərlər qorunmaqla `PROTON_ADD_CONFIG` və `STEAM_COMPAT_CONFIG`ə əlavə olunur. Tokenlər: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Steam avtomatlaşdırması

Steam işə salma seçimində:

```text
steam-auto-run %command%
```

UMU üçün: `GAMEID=umu-2357570 steam-auto-run %command%`. `localconfig.vdf` dəyişilməmişdən əvvəl Steam-i tamamilə bağlayın.

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` `--sanitize` üçün alternativdir; `--remove` wrapperi silir; `--print-library-paths` kitabxanaları göstərir; `--keep-backups N` ehtiyat sayı verir (`0` hamısını saxlayır).

Watcher `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` əmri icra edir. Unitləri ayrıca: `steam-auto-sync --install-systemd`.

## Əmrlər və dəyişənlər

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Əsas dəyişənlər: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` üstünlük tutur. Əks halda `kscreen-doctor`, `wlr-randr` və ya `xrandr` tezliyini oxuyur; 60 Hz-dən yuxarı olduqda 94% limit tətbiq olunur. Gamescope-də DXVK/VKD3D limiti yalnız açıq `VRR_CAP` ilə əlavə olunur.

Şəbəkə profili üçün `--with-net-boost` qurun və ya `NETOPT=1` istifadə edin. `steam-net-boost` CAKE və ya `fq_codel` tətbiq edir, EEE və tx queue length-i müvəqqəti dəyişdirir və son sessiya bitəndə əvvəlki vəziyyəti bərpa edir: `sudo steam-net-boost status [IFACE]`.
