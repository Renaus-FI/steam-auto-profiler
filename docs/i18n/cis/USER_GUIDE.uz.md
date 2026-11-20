# Steam Auto-Profiler foydalanuvchi qo'llanmasi

To'liq texnik ma'lumot [inglizcha qo'llanmada](../../USER_GUIDE.md) berilgan.

## O'rnatish

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` ixtiyoriy tarmoq QoS yordamchisini o'rnatadi. `--compat-cachy-run` mavjud `/usr/local/bin/cachy-run`ni `.bak` sifatida saqlaydi va moslik shimini o'rnatadi. `--with-auto-sync` systemd foydalanuvchi watcherini yoqadi. `--uninstall` o'rnatilgan qismlarni o'chiradi.

## Ishlash tartibi

`steam-auto-detect` Steam manifestlari va kutubxonalarida AppID ni topadi, o'yin papkasini o'n darajagacha skanerlaydi va tartib bo'yicha tasniflaydi: `competitive-anticheat`, keyin native FSR/FidelityFX (`native-fsr4`/`native-fsr`), keyin `legacy-upscaler`, aks holda `standard`.

`steam-auto-run` AppID ni `SteamAppId`, `STEAM_COMPAT_APP_ID` va `GAMEID` orqali aniqlaydi, `umu-` prefiksini olib tashlaydi. U `kdialog` yoki `zenity` ko'rsatishi va sozlamalarni `~/.config/steam-auto-profiler/profiles/<APPID>.env`ga saqlashi mumkin.

Moslik sozlamalari mavjud qiymatlar saqlanib, `PROTON_ADD_CONFIG` va `STEAM_COMPAT_CONFIG`ga yoziladi. Tokenlar: `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`.

## Steam avtomatlashtirish

Steam ishga tushirish parametri:

```text
steam-auto-run %command%
```

UMU uchun: `GAMEID=umu-2357570 steam-auto-run %command%`. `localconfig.vdf`ni o'zgartirishdan oldin Steamni to'liq yoping.

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` — `--sanitize` taxallusi, `--remove` wrapperni o'chiradi, `--print-library-paths` kutubxonalarni ko'rsatadi, `--keep-backups N` zaxira sonini belgilaydi (`0` hammasini saqlaydi).

Watcher `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` bajaradi. Unitlarni o'rnatish: `steam-auto-sync --install-systemd`.

## Buyruqlar va o'zgaruvchilar

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Asosiylar: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP` ustun. Aks holda `kscreen-doctor`, `wlr-randr` yoki `xrandr` chastotani aniqlaydi; 60 Hz dan yuqori bo'lsa 94% chegara qo'llaniladi. Gamescope'da DXVK/VKD3D cheklovi faqat aniq `VRR_CAP` bilan qo'llanadi.

Tarmoq profili uchun `--with-net-boost` o'rnating yoki `NETOPT=1` ishlating. `steam-net-boost` CAKE yoki `fq_codel` qo'llaydi, EEE va tx queue lengthni vaqtincha o'zgartiradi, oxirgi seans tugaganda tiklaydi: `sudo steam-net-boost status [IFACE]`.
