# Guide de l'utilisateur Steam Auto-Profiler

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Ce guide couvre l'installation complète, l'orchestration des lancements écran plat et VR, le centre de contrôle `steam-auto-ui`, la synchronisation de bibliothèque, le benchmarking et le dépannage pour **Steam Auto-Profiler v2.1**.

Steam Auto-Profiler est un lanceur et centre de contrôle léger en Bash/Python pour Linux qui inspecte un AppID Steam (ou un raccourci non-Steam), applique un profil adapté au contexte avec des garde-fous stricts pour les pilotes, les upscalers et l'anti-triche, puis lance la commande du jeu existante. Il n'embarque ni n'injecte jamais de runtime Proton tiers.

---

## Prérequis

- Session de bureau Linux (KDE Plasma 6 / Wayland, GNOME, wlroots ou X11), Bash 5+, Python 3.10+, Steam et utilitaires système standard.
- Interface graphique native optionnelle pour le centre de contrôle : `PyQt6` ou `PySide6` (bascule automatiquement sur la TUI `curses` de la bibliothèque standard, sans dépendance).
- Boîtes de dialogue optionnelles de liste de contrôle avant lancement : `kdialog` ou `zenity`.
- Benchmarking silencieux optionnel des temps d'image (frametime) : `mangohud`.
- Assistant réseau de session optionnel : `tc`, `ip` et `ethtool` (`sudo` requis uniquement lors de l'installation avec `--with-net-boost`).

---

## Installation et mises à jour

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` copie les six exécutables (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` et `steam-auto-ui`) dans `~/.local/bin`, installe le lanceur de bureau (`~/.local/share/applications/steam-auto-profiler.desktop`), crée `~/.config/steam-auto-profiler/profiles` et ajoute les préréglages vkBasalt par défaut (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Vérifiez que `~/.local/bin` figure dans `PATH`.

Les options de l'installeur peuvent être combinées :

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost` : installe `/usr/local/bin/steam-net-boost` (ainsi que des copies système des autres scripts) et une règle `sudoers` strictement limitée sans mot de passe pour `steam-net-boost`.
- `--compat-cachy-run` : conserve un éventuel `/usr/local/bin/cachy-run` existant sous `/usr/local/bin/cachy-run.bak` (sauf s'il s'agit déjà du shim Steam Auto-Profiler) et installe un shim de redirection vers `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`) : installe et active le moniteur systemd utilisateur `steam-auto-profiler-sync.path` et son service `oneshot` associé sur toutes les bibliothèques Steam détectées.
- `--uninstall` : supprime les binaires installés, l'entrée de bureau, l'assistant réseau / la règle sudoers optionnels, le shim de compatibilité et les unités systemd utilisateur de synchronisation automatique.

Pour mettre à jour un dépôt existant :

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Vérifiez l'état de l'hôte avant de synchroniser vos jeux :

```bash
steam-auto-run --doctor
```

---

## Pipeline de lancement de bout en bout

1. **Résolution de l'AppID :** Vérifie `SteamAppId`, `STEAM_COMPAT_APP_ID`, puis `GAMEID` (en retirant tout préfixe `umu-` pour Lutris/Heroic/UMU).
2. **Découverte des bibliothèques et raccourcis :** `steam-auto-detect` explore les racines Steam et les bibliothèques secondaires déclarées dans `libraryfolders.vdf`, lit `appmanifest_<APPID>.acf` ou se rabat en lecture seule sur le fichier binaire `userdata/*/config/shortcuts.vdf`, puis effectue un `find` en une seule passe jusqu'à 10 niveaux de profondeur (en élaguant `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Priorité de classification en cinq niveaux :**
   - **1. `competitive-anticheat` :** AppID compétitif connu ou runtime anti-triche détecté (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE, etc.). Désactive OptiScaler, MLFG, vkBasalt et DXVK asynchrone ; active la faible latence et la QoS réseau de session.
   - **2. `vr` :** Détection de `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` ou des indicateurs `vr-run`/`-vr` dans le raccourci. Exporte `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr` :** FidelityFX SDK 3.1+ modulaire (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Active la mise à niveau FSR4 côté pilote (`PROTON_FSR4_UPGRADE=1` ou `PROTON_FSR4_RDNA3_UPGRADE=1` sur AMD RDNA 3).
   - **4. `legacy-upscaler` :** Bibliothèques DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) ou DLL FSR 2/3.0 héritées. Définit `AUTO_OPTISCALER=1` et renseigne les recommandations `AUTO_UPSCALER_INFO`.
   - **5. `standard` :** Profil sûr Wine Wayland natif + VRR faible latence.
4. **Limitation de fréquence de rafraîchissement VRR :** Un `VRR_CAP=<fps>` explicite l'emporte toujours (`VRR_CAP=0` désactive le plafond). Sinon, la fréquence active de l'écran est détectée via `kscreen-doctor` (mode actif `*` de KDE Plasma 6 ou `Hz` classique), `wlr-randr` ou `xrandr` et appliquée en 1:1 par défaut (`240 FPS` sur 240 Hz). Activez `VRR_MINUS_MARGIN=1` pour appliquer la marge de sécurité VRR optionnelle de `-6%` (`hz * 94 / 100`, p. ex. `225 FPS` sur 240 Hz). Dans les sessions Gamescope, les limites DXVK/VKD3D sont omises sauf si `VRR_CAP` est défini explicitement.
5. **Garde-fous d'exclusion mutuelle :**
   - **FSR 4 / OptiScaler + vkBasalt :** `ENABLE_VKBASALT=0` est imposé dès que `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` ou `USE_OPTISCALER=1` est actif (évite le double renforcement de netteté et l'écrêtage HDR10).
   - **MLFG + Faible latence / Limites VRR :** `MLFG=1` (`USE_MLFG=1`) exporte `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, supprime `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` et `DXVK_FRAME_PACE`, et exporte `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` sur AMD RDNA 3. Lorsque `USE_MLFG=0` et qu'une limite VRR est active, `DXVK_FRAME_PACE=low-latency-vrr` est exporté.
   - **DX12 moderne + Safe DX12 :** Exporte `PROTON_NATIVE_AGS=1` sur AMD et `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` lorsque `USE_SAFEDX12=0` (proprement omis lorsque `SAFEDX12=1`).
6. **Mappage des jetons de compatibilité :** Les fonctionnalités gérées sont ajoutées sans écraser les valeurs utilisateur existantes dans `PROTON_ADD_CONFIG` et `STEAM_COMPAT_CONFIG` : `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **HDR automatique KDE Plasma 6 (`AUTO_HDR_SWITCH=1`) :** Activé hors Gamescope avec `DXVK_HDR=1` (ou `USE_HDR=1`), sonde la sortie principale active via `kscreen-doctor -o` ; si le HDR est désactivé, l'active avant le lancement et restaure le SDR via un trap `EXIT`/`INT`/`TERM`.
8. **Benchmarking silencieux des frametimes (`BENCH=1`) :** Lance MangoHud en mode CSV masqué (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), analyse les temps d'image à la fermeture, ajoute `Avg FPS`, `1% Low FPS` et `P99 (ms)` à `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` et supprime les CSV temporaires.
9. **Récupération automatique en Mode Sans Échec après crash rapide :** Si un jeu Proton/Windows se termine avec un code non nul en moins de `20s` (configurable via `SAP_CRASH_THRESHOLD_SEC`) alors que des options expérimentales Wayland ou DX12 sont actives (`USE_XWAYLAND=0` ou `USE_SAFEDX12=0`), enregistre un `crash_hint` dans `last-<APPID>.log` et `last-launch.log`, et propose (si la GUI est active) d'enregistrer `USE_XWAYLAND=1` + `USE_SAFEDX12=1` pour le lancement suivant.
10. **Cycle de vie de l'ordonnanceur et du réseau :** Enchaîne `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (uniquement si `ananicy-cpp.service` est inactif) -> exécution directe, avec prise en charge optionnelle de `PRIME=1` (`prime-run`). Si `USE_NET_OPT=1`, `steam-net-boost` exécute `on`/`off` avec comptage de références et `flock` tout en préservant les hiérarchies statiques root CAKE et HTB + leaf CAKE.

---

## Centre de contrôle unifié (`steam-auto-ui`)

Lancez `steam-auto-ui` depuis le menu d'applications du bureau, via `steam-auto-run --ui` ou directement :

```bash
steam-auto-ui                 # Détecte automatiquement la GUI Qt6 (PyQt6/PySide6) ou la TUI curses
steam-auto-ui --gui           # Force la fenêtre graphique native Qt6
steam-auto-ui --tui           # Force la TUI curses de stdlib (fonctionne via SSH)
steam-auto-ui --lang fi       # Lance avec une langue d'interface explicite (27 langues prises en charge)
steam-auto-ui --check         # Exécute un autodiagnostic headless (sortie JSON)
```

`steam-auto-ui` détecte automatiquement la locale du système via `LC_ALL` / `LC_MESSAGES` / `LANG` et propose un menu déroulant de langue en direct dans la GUI Qt6 (ainsi que le raccourci `L` dans la TUI `curses`) pour basculer entre les 27 langues à la volée sans redémarrer.

### Cinq vues synchronisées

1. **Jeux et profils :** Tableau filtrable des titres Steam et des entrées non-Steam `shortcuts.vdf` en lecture seule (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), badge SDK d'upscaling (`AUTO_UPSCALER_INFO`), validation en direct des exclusions mutuelles sur les 10 bascules de profil + `VRR_CAP`, `Dry-Run Preview`, bouton d'accès rapide `Benchmarks` et `Reset Profile`.
2. **Système et télémétrie :** Affichage en direct non bloquant de `steam-auto-run --doctor`, état `scxctl get` / `sched_ext`, versions installées de la pile (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), espace du cache de shaders (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), alertes de rétrogradation git/AUR depuis `/var/log/pacman.log`, VRAM/utilisation/température GPU, débit LAN (`10:`) vs WAN (`20:`/root) et `av_delay` issus de `tc -s qdisc`, ainsi que `vr-mode status`.
3. **Synchronisation de bibliothèque :** Bannière en direct surveillant si Steam est en cours d'exécution, plus actions en un clic pour `--report`, `--sanitize --dry-run`, `--sanitize` (refusé tant que Steam est ouvert) et `--migrate-cachy-run`.
4. **Journaux et récupération :** Consultez `last-launch.log` et `last-<APPID>.log`, examinez les alertes `crash_hint` et appliquez le Mode Sans Échec en un clic (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarks :** Tableau comparatif filtrable côte à côte des mesures frametime `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Orchestration VR (`vr-run`)

Définissez dans Steam **Propriétés > Général > Options de lancement** pour les titres VR :

```text
vr-run %command%
```

- Nettoie les surcharges héritées du mode écran plat (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Sélectionne automatiquement le GPU dédié disposant du plus de VRAM via `MESA_VK_DEVICE_SELECT` et définit `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` sur les GPU AMD.
- Détecte dynamiquement les chemins OpenXR/OpenVR de WiVRn et xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) et configure `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` et `LD_LIBRARY_PATH` sans écraser les variables définies explicitement par l'utilisateur.
- Gère `vr-mode on` / `vr-mode off` avec comptage de références dans `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (avec `flock`) lorsque `vr-mode` est installé (`VR_AUTO_MODE=0` le désactive).
- Passe par la même chaîne d'ordonnanceurs tenant compte d'`ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> `exec` direct).
- Prévisualisez à tout moment les variables résolues avec `vr-run --dry-run`.

`steam-auto-run` contourne automatiquement SteamVR (`250820`) et les lancements `-vr`/`--vr`, et `steam-auto-sync` attribue et préserve automatiquement `vr-run %command%` pour les jeux VR.

---

## Synchronisation de la bibliothèque Steam (`steam-auto-sync`)

Fermez complètement Steam avant d'écrire dans `localconfig.vdf` :

```bash
steam-auto-sync --report              # Audit en lecture seule de la bibliothèque + shortcuts.vdf
steam-auto-sync --print-library-paths # Affiche toutes les bibliothèques Steam détectées
steam-auto-sync --dry-run             # Prévisualise les modifications
steam-auto-sync                       # Injecte steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Prévisualise le nettoyage des anciens paramètres
steam-auto-sync --sanitize            # Nettoie les paramètres obsolètes/orphelins (alias : --clean)
steam-auto-sync --migrate-cachy-run   # Migre les anciens profils cachy-run
steam-auto-sync --remove              # Retire le wrapper steam-auto-run
```

- Les sauvegardes horodatées `localconfig.vdf.bak.*` sont purgées automatiquement via `--keep-backups N` (`10` par défaut ; `0` les conserve toutes).
- Excluez des AppID spécifiques en les listant (un par ligne, commentaires `#` autorisés) dans `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Le moniteur d'auto-synchronisation systemd (`./install.sh --with-auto-sync` ou `steam-auto-sync --install-systemd`) exécute `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` dès que les manifestes Steam changent.

---

## Référence CLI et profils

### Commandes

| Usage | Commande |
| --- | --- |
| Audit de préparation du système | `steam-auto-run --doctor` (alias `--check-system`) |
| Lancer le centre de contrôle (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` ou `steam-auto-run --ui` |
| Inspecter un jeu (lisible) | `steam-auto-run --inspect APPID` |
| Inspecter un jeu (JSON) | `steam-auto-detect --inspect --json APPID` |
| Reconfigurer un profil de manière interactive | `steam-auto-run --configure APPID` |
| Prévisualiser l'environnement résolu | `steam-auto-run --dry-run APPID` |
| Réinitialiser un profil enregistré | `steam-auto-run --reset APPID` |
| Lister les profils enregistrés | `steam-auto-run --list-profiles` |
| Afficher le dernier journal de lancement | `steam-auto-run --last-log [APPID]` |
| Prévisualiser l'environnement VR | `vr-run --dry-run` |
| Inspecter l'assistant réseau (lecture seule) | `steam-net-boost status [IFACE]` |

### Clés de profil `.env` enregistrées et surcharges d'environnement

Les fichiers de profil se trouvent dans `~/.config/steam-auto-profiler/profiles/<APPID>.env` et acceptent un format `KEY=VALUE` sur liste blanche (les substitutions de commandes shell et les clés inconnues sont ignorées en toute sécurité) :

| Clé `.env` | Variable d'environnement | Effet |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Force XWayland au lieu de Wine Wayland natif |
| `USE_FSR4=0` | `FSR4=0` | Désactive la mise à niveau FSR 4 côté pilote (`1` par défaut) |
| `USE_MLFG=1` | `MLFG=1` | Active la génération d'images (désactive Anti-Lag, faible latence et limites VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Active la passerelle OptiScaler (désactivée pour `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Active la netteté vkBasalt (désactivée si FSR 4 ou OptiScaler est actif) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Omet les options expérimentales `VKD3D_CONFIG` et le jeton `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Active la QoS réseau de session via `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Privilégie l'émulation native SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Conserve `LD_PRELOAD` de l'overlay Steam |
| `USE_CEF_FIX=1` | `CEF=1` | Ajoute `--in-process-gpu` pour les lanceurs CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Désactive NTSync pour les anciens jeux |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Désactive les décorations du gestionnaire de fenêtres |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Plafond d'images personnalisé DXVK/VKD3D (`0` désactive le plafond) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Applique une marge de `-6%` sous la fréquence de l'écran (ex. `225 FPS` à 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Autorise l'inhibition des raccourcis sous Wine Wayland (`0` par défaut) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Active automatiquement le HDR KDE Plasma 6 au lancement et restaure le SDR à la sortie |
| — | `BENCH=1`, `BENCH_DURATION=60` | Exécute un benchmark CSV silencieux MangoHud et enregistre un résumé JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Masque ou force la réouverture de la liste `kdialog`/`zenity` avant lancement |
| — | `FSR_HUD=1` | Exporte les variables d'affichage HUD FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Ajoute `-vulkan` / encapsule avec `prime-run` |
| — | `GAMEID=umu-<appid>` | Résout les AppID UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus et UMU

- **Lutris :** Activez les options avancées, choisissez `proton-cachyos-slr` (ou votre version de Proton), désactivez le runtime Lutris, privilégiez les bibliothèques système et définissez le préfixe de commande sur `steam-auto-run`.
- **Heroic / Faugus :** Choisissez `proton-cachyos-slr` et ajoutez `steam-auto-run` comme wrapper / préfixe de commande.
- **UMU / Protonfixes :** Exportez `PROTON_VERB=waitforexitandrun` et `GAMEID=umu-<appid>` si nécessaire.

---

## Dépannage

- **Crash rapide sous Wayland ou DX12 :** Ouvrez **Journaux et récupération** dans `steam-auto-ui` (ou exécutez `steam-auto-run --last-log APPID`) et appliquez le Mode Sans Échec (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), ou lancez `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Les jeux avec anti-triche ne démarrent pas :** Utilisez `proton-cachyos-slr` (Steam Linux Runtime) et lancez `steam-auto-run --doctor` pour vérifier EAC v2, `/dev/ntsync` et `vm.max_map_count`.
- **Steam réinitialise les options de lancement :** Fermez complètement Steam avant d'exécuter `steam-auto-sync` ou `steam-auto-sync --sanitize`.
- **Limite VRR incorrecte ou absente :** Définissez explicitement `VRR_CAP=<fps>`, `VRR_CAP=0` pour la désactiver ou `VRR_MINUS_MARGIN=1` pour une marge de `-6%`. Sous Gamescope, seul un `VRR_CAP` explicite exporte les limites DXVK/VKD3D.
- **Vérification QoS réseau :** Exécutez `steam-net-boost status` (lecture seule, sans privilèges). Installez l'assistant root avec `./install.sh --with-net-boost` pour bénéficier de la QoS automatique par session.

---

## Nouveautés de la v2.1 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 & Steam Controller 2026)

- **Options Mesa 27.0 / RDNA 4 :** `TRANSFER_QUEUE=1` (`RADV_PERFTEST=sam,transfer_queue` dédupliqué sur RDNA 3/4), `NATIVE_ANTILAG=1` (`VK_AMD_anti_lag` natif), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, bloqué sous anti-triche et MLFG) et `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`) :** pile expérimentale hors anti-triche (`VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, `WAYLANDDRV_RAWINPUT=1` uniquement en Wayland natif hors Gamescope).
- **Protection Hunt: Showdown 1896 (`AppID 594650`) :** impose `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0` et `USE_NET_OPT=1` ; `--doctor` et `steam-auto-ui` vérifient `config.vdf` (recommandant `Proton 11.0-2` ou `Proton Hotfix`).
- **Steam Controller 2026 (`Triton`/`Proteus`) & Wireless Steam Puck (`28de:{1302,1304,1005,1007}`) :** 4 modes (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`) : `wayland-hdr` conserve Wayland natif + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`, sans `sdlinput`), déclenche `steam://forceinputappid/<APPID>` avec reconnexion automatique `udevadm` et réinitialise `steam://forceinputappid/0` à la sortie. Manuel : `steam-auto-run --reapply-input <APPID|0>` ; udev : `./install.sh --with-steam-controller`.

---

Consultez [ARCHITECTURE.md](../../ARCHITECTURE.md) pour les détails techniques internes, le [English User Guide](../../USER_GUIDE.md) pour la référence anglaise et [i18n Index](../README.md) pour les 27 guides localisés.
