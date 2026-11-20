# Guide utilisateur Steam Auto-Profiler

Ce guide couvre l'installation et l'utilisation quotidienne. Les détails techniques sont disponibles dans le [guide anglais](../../USER_GUIDE.md).

## Installation

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` installe l'outil facultatif de QoS réseau. `--compat-cachy-run` conserve `/usr/local/bin/cachy-run` sous `.bak` puis installe le shim. `--with-auto-sync` installe le watcher systemd utilisateur. `--uninstall` retire les composants.

## Fonctionnement

`steam-auto-detect` recherche l'AppID dans les manifestes et bibliothèques Steam, parcourt le dossier du jeu jusqu'à dix niveaux et applique la priorité : (1) `competitive-anticheat`, (2) FSR/FidelityFX natif (`native-fsr4`/`native-fsr`), (3) `legacy-upscaler`, (4) `standard`.

`steam-auto-run` résout `SteamAppId`, `STEAM_COMPAT_APP_ID`, puis `GAMEID`, en supprimant le préfixe `umu-`. Il affiche `kdialog` ou `zenity` si possible et conserve les réglages dans `~/.config/steam-auto-profiler/profiles/<APPID>.env`. Le format est `KEY=VALUE`; les clés inconnues sont ignorées.

Les réglages sont ajoutés à `PROTON_ADD_CONFIG` et `STEAM_COMPAT_CONFIG` tout en préservant les valeurs utilisateur. Les jetons sont notamment `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire` et `vkreflex`.

## Steam et automatisation

Dans les options de lancement Steam :

```text
steam-auto-run %command%
```

Pour UMU : `GAMEID=umu-2357570 steam-auto-run %command%`.

Fermez Steam avant toute modification de `localconfig.vdf` :

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` est l'alias de `--sanitize`; `--remove` retire le wrapper; `--print-library-paths` affiche les bibliothèques; `--keep-backups N` conserve N sauvegardes (`0` les conserve toutes).

Le watcher exécute `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`. Installez ses unités avec `steam-auto-sync --install-systemd`.

## Commandes et variables

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles` et `--last-log [APPID]`. JSON : `steam-auto-detect --inspect --json APPID`.

Variables principales : `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1` et `NO_NTSYNC=1`.

`VRR_CAP` est prioritaire. Sinon, `kscreen-doctor`, `wlr-randr` ou `xrandr` fournit le taux de rafraîchissement; au-dessus de 60 Hz, la limite vaut 94 %. Sous Gamescope, aucun plafond DXVK/VKD3D n'est ajouté sans `VRR_CAP`.

## Réseau et dépannage

Avec `NETOPT=1` ou `netopt`, `steam-net-boost` active CAKE ou `fq_codel`, désactive temporairement EEE et ajuste tx queue length. Après la dernière session, il restaure l'état précédent.

État : `sudo steam-net-boost status [IFACE]`. Fermez Steam complètement avant la synchronisation. Pour corriger un profil, utilisez `FORCE_GUI=1` ou `--reset APPID`. Pour les anti-cheats, privilégiez `proton-cachyos-slr` et vérifiez avec `--doctor`.
