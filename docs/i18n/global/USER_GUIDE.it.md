# Guida utente di Steam Auto-Profiler

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Questa guida copre l'installazione completa, l'orchestrazione dei lanci su schermo piatto e VR, il Centro di controllo `steam-auto-ui`, la sincronizzazione della libreria, il benchmarking e la risoluzione dei problemi per **Steam Auto-Profiler v2.0**.

Steam Auto-Profiler è un launcher e centro di controllo leggero in Bash/Python per Linux che analizza uno Steam AppID (o un collegamento Non-Steam), applica un profilo consapevole del contesto con protezioni rigorose per driver, upscaler e anti-cheat e avvia il comando di gioco esistente. Non include né inietta mai un runtime Proton di terze parti.

---

## Requisiti

- Sessione desktop Linux (KDE Plasma 6 / Wayland, GNOME, wlroots o X11), Bash 5+, Python 3.10+, Steam e utility di sistema standard.
- GUI nativa opzionale per il Centro di controllo: `PyQt6` o `PySide6` (ripiega automaticamente sulla TUI `curses` della libreria standard senza dipendenze).
- Finestre di dialogo opzionali per la checklist pre-lancio: `kdialog` o `zenity`.
- Benchmarking silenzioso opzionale del frametime: `mangohud`.
- Helper di rete di sessione opzionale: `tc`, `ip` ed `ethtool` (`sudo` è richiesto solo durante l'installazione con `--with-net-boost`).

---

## Installazione e aggiornamenti

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` copia tutti e sei gli eseguibili (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` e `steam-auto-ui`) in `~/.local/bin`, installa il lanciatore desktop (`~/.local/share/applications/steam-auto-profiler.desktop`), crea `~/.config/steam-auto-profiler/profiles` e aggiunge i preset predefiniti di vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Assicurati che `~/.local/bin` sia nel `PATH`.

I flag opzionali dell'installer possono essere combinati:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: installa `/usr/local/bin/steam-net-boost` (più copie di sistema degli altri script) e una regola `sudoers` strettamente circoscritta senza password per `steam-net-boost`.
- `--compat-cachy-run`: preserva un eventuale `/usr/local/bin/cachy-run` esistente come `/usr/local/bin/cachy-run.bak` (a meno che non sia già lo shim di Steam Auto-Profiler) e installa uno shim di inoltro verso `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): installa e abilita il watcher utente systemd `steam-auto-profiler-sync.path` e il relativo servizio `oneshot` su tutte le librerie Steam rilevate.
- `--uninstall`: rimuove i binari installati, la voce desktop, l'helper di rete/regola sudoers opzionali, lo shim di compatibilità e le unità utente systemd di sincronizzazione automatica.

Per aggiornare un repository già clonato:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Verifica lo stato del sistema prima di sincronizzare i giochi:

```bash
steam-auto-run --doctor
```

---

## Pipeline di lancio end-to-end

1. **Risoluzione AppID:** Controlla `SteamAppId`, `STEAM_COMPAT_APP_ID`, poi `GAMEID` (rimuovendo l'eventuale prefisso `umu-` per Lutris/Heroic/UMU).
2. **Rilevamento di librerie e collegamenti:** `steam-auto-detect` esamina le radici Steam e le librerie secondarie in `libraryfolders.vdf`, legge `appmanifest_<APPID>.acf` oppure ripiega in sola lettura sul file binario `userdata/*/config/shortcuts.vdf`, quindi esegue un `find` a passaggio singolo fino a 10 livelli di profondità (escludendo `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Priorità di classificazione a cinque livelli:**
   - **1. `competitive-anticheat`:** AppID competitivo noto o runtime anti-cheat rilevato (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE, ecc.). Disattiva OptiScaler, MLFG, vkBasalt e DXVK asincrono; abilita bassa latenza e QoS di rete di sessione.
   - **2. `vr`:** Rilevamento di `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` o flag `vr-run`/`-vr` nel collegamento. Esporta `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** FidelityFX SDK 3.1+ modulare (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Abilita l'upgrade FSR4 a livello di driver (`PROTON_FSR4_UPGRADE=1` o `PROTON_FSR4_RDNA3_UPGRADE=1` su AMD RDNA 3).
   - **4. `legacy-upscaler`:** DLL legacy DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) o FSR 2/3.0. Imposta `AUTO_OPTISCALER=1` e popola le indicazioni in `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Profilo sicuro Wine Wayland nativo + VRR a bassa latenza.
4. **Limitazione frequenza di aggiornamento VRR:** Un `VRR_CAP=<fps>` esplicito prevale sempre (`VRR_CAP=0` disattiva il limite). Altrimenti la frequenza attiva del display viene rilevata tramite `kscreen-doctor` (modalità attiva `*` di KDE Plasma 6 o `Hz` legacy), `wlr-randr` o `xrandr` e applicata 1:1 per impostazione predefinita (`240 FPS` su 240 Hz). Abilita `VRR_MINUS_MARGIN=1` per il margine di sicurezza VRR opzionale del `-6%` (`hz * 94 / 100`, ad es. `225 FPS` su 240 Hz). Nelle sessioni Gamescope i limiti DXVK/VKD3D vengono omessi salvo `VRR_CAP` esplicito.
5. **Protezioni di mutua esclusione:**
   - **FSR 4 / OptiScaler + vkBasalt:** Viene imposto `ENABLE_VKBASALT=0` ogni volta che `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` o `USE_OPTISCALER=1` è attivo (evita doppio sharpening e clipping HDR10).
   - **MLFG + Bassa latenza / Limiti VRR:** `MLFG=1` (`USE_MLFG=1`) esporta `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, rimuove `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` e `DXVK_FRAME_PACE`, ed esporta `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` su AMD RDNA 3. Quando `USE_MLFG=0` e il limite VRR è attivo, viene esportato `DXVK_FRAME_PACE=low-latency-vrr`.
   - **DX12 moderno + Safe DX12:** Esporta `PROTON_NATIVE_AGS=1` su AMD e `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` quando `USE_SAFEDX12=0` (omesso in modo pulito quando `SAFEDX12=1`).
6. **Mappatura dei token di compatibilità:** Le funzionalità gestite vengono aggiunte senza sovrascrivere i valori esistenti dell'utente sia in `PROTON_ADD_CONFIG` sia in `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **HDR automatico KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Se abilitato fuori da Gamescope con `DXVK_HDR=1` (o `USE_HDR=1`), interroga l'uscita principale abilitata tramite `kscreen-doctor -o`; se HDR è disattivo, lo abilita prima del lancio e ripristina SDR tramite trap `EXIT`/`INT`/`TERM`.
8. **Benchmarking silenzioso del frametime (`BENCH=1`):** Avvia MangoHud in modalità CSV nascosta (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), elabora i frametime all'uscita, aggiunge `Avg FPS`, `1% Low FPS` e `P99 (ms)` in `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` e rimuove i CSV temporanei.
9. **Auto-ripristino in Modalità Sicura dopo crash rapido:** Se un titolo Proton/Windows termina con codice diverso da zero in meno di `20s` (configurabile tramite `SAP_CRASH_THRESHOLD_SEC`) con flag sperimentali Wayland o DX12 attivi (`USE_XWAYLAND=0` o `USE_SAFEDX12=0`), registra un `crash_hint` in `last-<APPID>.log` e `last-launch.log` e propone (se la GUI è attiva) di salvare `USE_XWAYLAND=1` + `USE_SAFEDX12=1` per il lancio successivo.
10. **Ciclo di vita dello scheduler e della rete:** Esegue tramite `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (solo se `ananicy-cpp.service` è inattivo) -> esecuzione diretta, con supporto opzionale per `PRIME=1` (`prime-run`). Se `USE_NET_OPT=1`, `steam-net-boost` esegue `on`/`off` con conteggio dei riferimenti e `flock`, preservando le gerarchie statiche root CAKE e HTB + leaf CAKE.

---

## Centro di controllo unificato (`steam-auto-ui`)

Avvia `steam-auto-ui` dal menu applicazioni del desktop, tramite `steam-auto-run --ui` o direttamente:

```bash
steam-auto-ui                 # Rileva automaticamente la GUI Qt6 (PyQt6/PySide6) o la TUI curses
steam-auto-ui --gui           # Forza la finestra GUI nativa Qt6
steam-auto-ui --tui           # Forza la TUI curses stdlib (funziona via SSH)
steam-auto-ui --lang fi       # Avvia con lingua interfaccia esplicita (27 lingue supportate)
steam-auto-ui --check         # Esegue autocontrollo headless (stampa diagnostica JSON)
```

`steam-auto-ui` rileva automaticamente la localizzazione di sistema da `LC_ALL` / `LC_MESSAGES` / `LANG` e offre un menu a discesa per la lingua in tempo reale nella GUI Qt6 (e il tasto rapido `L` nella TUI `curses`) per cambiare tra tutte le 27 lingue senza riavviare.

### Cinque viste sincronizzate

1. **Giochi e profili:** Tabella filtrabile dei titoli Steam e delle voci Non-Steam `shortcuts.vdf` in sola lettura (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), badge SDK upscaler (`AUTO_UPSCALER_INFO`), validazione in tempo reale di mutua esclusione su tutti i 10 selettori profilo + `VRR_CAP`, `Dry-Run Preview`, pulsante diretto per `Benchmarks` e `Reset Profile`.
2. **Sistema e telemetria:** Lettura live non bloccante di `steam-auto-run --doctor`, stato `scxctl get` / `sched_ext`, versioni installate dello stack (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), utilizzo della shader cache (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), avvisi di downgrade git/AUR da `/var/log/pacman.log`, VRAM/utilizzo/temperatura GPU, throughput LAN (`10:`) vs WAN (`20:`/root) e `av_delay` da `tc -s qdisc`, e `vr-mode status`.
3. **Sincronizzazione libreria:** Banner live di controllo sullo stato di esecuzione di Steam più pulsanti con un clic per `--report`, `--sanitize --dry-run`, `--sanitize` (bloccato mentre Steam è aperto) e `--migrate-cachy-run`.
4. **Log e ripristino:** Consulta `last-launch.log` e `last-<APPID>.log`, controlla gli avvisi `crash_hint` e applica la Modalità Sicura con un clic (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarks:** Tabella comparativa filtrabile affiancata delle esecuzioni frametime `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Orchestrazione VR (`vr-run`)

Imposta su Steam **Proprietà > Generali > Opzioni di avvio** per i titoli VR su:

```text
vr-run %command%
```

- Rimuove le sovrascritture ereditate per schermo piatto (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Seleziona automaticamente la GPU dedicata con la maggiore VRAM tramite `MESA_VK_DEVICE_SELECT` e imposta `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` su GPU AMD.
- Rileva dinamicamente i percorsi OpenXR/OpenVR di WiVRn e xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) e configura `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` e `LD_LIBRARY_PATH` senza sovrascrivere override espliciti dell'utente.
- Gestisce `vr-mode on` / `vr-mode off` con conteggio riferimenti in `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (con `flock`) quando `vr-mode` è installato (`VR_AUTO_MODE=0` lo disattiva).
- Passa attraverso la stessa catena di scheduler compatibile con `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> `exec` diretto).
- Visualizza in anteprima le variabili risolte in qualsiasi momento con `vr-run --dry-run`.

`steam-auto-run` ignora automaticamente SteamVR (`250820`) e i lanci `-vr`/`--vr`, mentre `steam-auto-sync` assegna e preserva automaticamente `vr-run %command%` per i titoli VR.

---

## Sincronizzazione libreria Steam (`steam-auto-sync`)

Chiudi completamente Steam prima di scrivere su `localconfig.vdf`:

```bash
steam-auto-sync --report              # Audit in sola lettura della libreria + shortcuts.vdf
steam-auto-sync --print-library-paths # Mostra tutte le librerie Steam rilevate
steam-auto-sync --dry-run             # Anteprima delle modifiche
steam-auto-sync                       # Inietta steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Anteprima pulizia flag obsoleti
steam-auto-sync --sanitize            # Pulisce flag disordinati/orfani (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migra vecchi profili cachy-run
steam-auto-sync --remove              # Rimuove il wrapper steam-auto-run
```

- I backup con timestamp `localconfig.vdf.bak.*` vengono sfoltiti automaticamente tramite `--keep-backups N` (predefinito `10`; `0` li conserva tutti).
- Escludi specifici AppID elencandoli (uno per riga, commenti `#` consentiti) in `~/.config/steam-auto-profiler/ignore_appids.txt`.
- Il watcher systemd di sincronizzazione automatica (`./install.sh --with-auto-sync` o `steam-auto-sync --install-systemd`) esegue `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` quando i manifesti di Steam cambiano.

---

## Riferimento CLI e profili

### Comandi

| Scopo | Comando |
| --- | --- |
| Audit di prontezza del sistema | `steam-auto-run --doctor` (alias `--check-system`) |
| Avvia Centro di controllo (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` o `steam-auto-run --ui` |
| Ispeziona un gioco (leggibile) | `steam-auto-run --inspect APPID` |
| Ispeziona un gioco (JSON) | `steam-auto-detect --inspect --json APPID` |
| Riconfigura profilo interattivamente | `steam-auto-run --configure APPID` |
| Anteprima ambiente di lancio risolto | `steam-auto-run --dry-run APPID` |
| Ripristina profilo salvato | `steam-auto-run --reset APPID` |
| Elenca profili salvati | `steam-auto-run --list-profiles` |
| Mostra ultimo log di lancio | `steam-auto-run --last-log [APPID]` |
| Anteprima ambiente di lancio VR | `vr-run --dry-run` |
| Ispeziona helper di rete (sola lettura) | `steam-net-boost status [IFACE]` |

### Chiavi profilo `.env` salvate e override di ambiente

I file di profilo si trovano in `~/.config/steam-auto-profiler/profiles/<APPID>.env` e accettano un formato `KEY=VALUE` con allowlist (le sostituzioni di comandi shell e le chiavi sconosciute vengono ignorate in sicurezza):

| Chiave `.env` | Variabile d'ambiente | Effetto |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Forza XWayland invece di Wine Wayland nativo |
| `USE_FSR4=0` | `FSR4=0` | Disattiva l'upgrade FSR 4 a livello di driver (predefinito `1`) |
| `USE_MLFG=1` | `MLFG=1` | Abilita frame generation (disattiva Anti-Lag, bassa latenza e limiti VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Abilita il bridge OptiScaler (bloccato per `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Abilita sharpening vkBasalt (disattivato se FSR 4 o OptiScaler è attivo) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Omette flag sperimentali `VKD3D_CONFIG` e il token `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Attiva QoS di rete di sessione tramite `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Preferisce emulazione nativa SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Mantiene `LD_PRELOAD` dello Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Aggiunge `--in-process-gpu` per launcher CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Disattiva NTSync per titoli legacy |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Disattiva le decorazioni del window manager |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Limite FPS personalizzato DXVK/VKD3D (`0` disattiva il limite) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Applica un margine del `-6%` sulla frequenza del monitor (es. `225 FPS` su 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Consente inibizione scorciatoie sotto Wine Wayland (predefinito `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Abilita automaticamente HDR KDE Plasma 6 all'avvio e ripristina SDR all'uscita |
| — | `BENCH=1`, `BENCH_DURATION=60` | Esegue benchmark CSV silenzioso con MangoHud e salva riepilogo JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Nasconde o forza la riapertura della checklist `kdialog`/`zenity` pre-lancio |
| — | `FSR_HUD=1` | Esporta le variabili indicatore HUD FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Aggiunge `-vulkan` / avvolge con `prime-run` |
| — | `GAMEID=umu-<appid>` | Risolve gli AppID UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus e UMU

- **Lutris:** Abilita le opzioni avanzate, seleziona `proton-cachyos-slr` (o la tua build Proton), disattiva il runtime Lutris, preferisci le librerie di sistema e imposta il prefisso comando su `steam-auto-run`.
- **Heroic / Faugus:** Scegli `proton-cachyos-slr` e aggiungi `steam-auto-run` come wrapper/prefisso comando.
- **UMU / Protonfixes:** Esporta `PROTON_VERB=waitforexitandrun` e `GAMEID=umu-<appid>` quando necessario.

---

## Risoluzione dei problemi

- **Crash rapido su Wayland o DX12:** Apri **Log e ripristino** in `steam-auto-ui` (oppure esegui `steam-auto-run --last-log APPID`) e applica la Modalità Sicura (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), oppure avvia con `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **I giochi con anti-cheat non si avviano:** Usa `proton-cachyos-slr` (Steam Linux Runtime) ed esegui `steam-auto-run --doctor` per verificare EAC v2, `/dev/ntsync` e `vm.max_map_count`.
- **Steam ripristina le opzioni di avvio:** Chiudi completamente Steam prima di eseguire `steam-auto-sync` o `steam-auto-sync --sanitize`.
- **Limite VRR errato o mancante:** Imposta esplicitamente `VRR_CAP=<fps>`, `VRR_CAP=0` per disattivarlo o `VRR_MINUS_MARGIN=1` per il margine del `-6%`. In Gamescope, solo un `VRR_CAP` esplicito esporta i limiti DXVK/VKD3D.
- **Verifica QoS di rete:** Esegui `steam-net-boost status` (sola lettura senza privilegi). Installa l'helper root con `./install.sh --with-net-boost` se desideri QoS automatico di sessione.

Consulta [ARCHITECTURE.md](../../ARCHITECTURE.md) per i dettagli architetturali interni, [English User Guide](../../USER_GUIDE.md) per la guida canonica in inglese e [i18n Index](../README.md) per tutte le 27 guide localizzate.
