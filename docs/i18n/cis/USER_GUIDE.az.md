# Steam Auto-Profiler — İstifadəçi Təlimatı

> [English User Guide](../../USER_GUIDE.md) · [i18n Index](../README.md)

Bu təlimat **Steam Auto-Profiler v2.1** üçün tam quraşdırma, ənənəvi ekran (flatscreen) və VR başlatma orkestrasiyası, `steam-auto-ui` İdarəetmə Mərkəzi, kitabxana sinxronizasiyası, performans testi (benchmarking) və problemlərin aradan qaldırılması proseslərini əhatə edir.

Steam Auto-Profiler Linux üçün yüngül Bash/Python başlatıcısı və idarəetmə mərkəzidir: Steam AppID-ni (və ya qeyri-Steam qısayolunu) yoxlayır, ciddi drayver/miqyaslayıcı (upscaler)/anti-cheat qoruyucuları ilə kontekstə uyğun profil tətbiq edir və oyunun mövcud əmrini işə salır. O, heç vaxt üçüncü tərəf Proton mühitini paketləmir və ya yeritmir.

---

## Tələblər

- Linux iş masası sessiyası (KDE Plasma 6 / Wayland, GNOME, wlroots və ya X11), Bash 5+, Python 3.10+, Steam və standart sistem utilitləri.
- İstəyə bağlı yerli İdarəetmə Mərkəzi GUI: `PyQt6` və ya `PySide6` (olmadıqda avtomatik olaraq xarici asılılıqsız standart kitabxana `curses` TUI rejiminə keçir).
- İstəyə bağlı başlatma öncəsi yoxlama siyahısı pəncərələri: `kdialog` və ya `zenity`.
- İstəyə bağlı səssiz kadr vaxtı (frametime) testi: `mangohud`.
- İstəyə bağlı sessiya şəbəkə köməkçisi: `tc`, `ip` və `ethtool` (`sudo` yalnız `--with-net-boost` quraşdırılması zamanı tələb olunur).

---

## Quraşdırma və Yeniləmələr

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` bütün altı icraolunan faylı (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` və `steam-auto-ui`) `~/.local/bin` qovluğuna köçürür, iş masası qısayolunu (`~/.local/share/applications/steam-auto-profiler.desktop`) quraşdırır, `~/.config/steam-auto-profiler/profiles` qovluğunu yaradır və standart vkBasalt hazır tənzimləmələrini (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`) əlavə edir. `~/.local/bin` yolunun `PATH` dəyişənində olduğundan əmin olun.

İstəyə bağlı quraşdırıcı bayraqları birləşdirilə bilər:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: `/usr/local/bin/steam-net-boost` faylını (və digər skriptlərin sistem nüsxələrini), həmçinin `steam-net-boost` üçün dar çərçivəli şifrəsiz sudoers qaydasını quraşdırır.
- `--compat-cachy-run`: mövcud `/usr/local/bin/cachy-run` faylını `/usr/local/bin/cachy-run.bak` kimi qoruyur (əgər o artıq Steam Auto-Profiler yönləndiricisi deyilsə) və `steam-auto-run`-a yönləndirən uyğunluq qatı (shim) quraşdırır.
- `--with-auto-sync` (`--enable-auto-sync`): aşkar edilmiş bütün Steam kitabxanaları üzrə istifadəçi systemd `steam-auto-profiler-sync.path` izləyicisini və uyğun birdəfəlik xidməti quraşdırıb aktivləşdirir.
- `--uninstall`: quraşdırılmış icraolunan faylları, iş masası qısayolunu, istəyə bağlı şəbəkə köməkçisini/sudoers qaydasını, uyğunluq shim-ini və istifadəçi systemd auto-sync vahidlərini silir.

Mövcud quraşdırmanı yeniləmək üçün:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Oyunları sinxronlaşdırmadan əvvəl sistemin hazırlığını yoxlayın:

```bash
steam-auto-run --doctor
```

---

## Başdan-başa Başlatma Konveyeri

1. **AppID Təyini:** Ardıcıllıqla `SteamAppId`, `STEAM_COMPAT_APP_ID`, sonra `GAMEID` dəyişənlərini yoxlayır (Lutris/Heroic/UMU üçün `umu-` prefiksini təmizləyir).
2. **Kitabxana və Qısayol Aşkarlanması:** `steam-auto-detect` əsas Steam qovluqlarını və `libraryfolders.vdf` faylındakı əlavə kitabxanaları axtarır, `appmanifest_<APPID>.acf` faylını oxuyur və ya yalnız-oxuma rejimində ikili `userdata/*/config/shortcuts.vdf` faylına müraciət edir; daha sonra 10 səviyyə dərinliyə qədər təkkeçidli `find` icra edir (`screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization` qovluqlarını ötürərək).
3. **Beşpilləli Təsnifat Prioriteti:**
   - **1. `competitive-anticheat`:** Tanınmış rəqabətli AppID və ya aşkar edilmiş anti-cheat modulu (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE və s.). OptiScaler, MLFG, vkBasalt və asinxron DXVK-nı söndürür; aşağı gecikmə rejimini və sessiya şəbəkə QoS-unu aktivləşdirir.
   - **2. `vr`:** Aşkar edilmiş `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` və ya `vr-run`/`-vr` qısayol bayraqları. `AUTO_IS_VR=1` ixrac edir.
   - **3. `native-fsr4` / `native-fsr`:** Modullu FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Drayver səviyyəli FSR 4 yüksəltməsini aktivləşdirir (`PROTON_FSR4_UPGRADE=1` və ya AMD RDNA 3-də `PROTON_FSR4_RDNA3_UPGRADE=1`).
   - **4. `legacy-upscaler`:** Köhnə DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) və ya FSR 2/3.0 DLL faylları. `AUTO_OPTISCALER=1` işarələyir və `AUTO_UPSCALER_INFO` yönləndirmə məlumatını təyin edir.
   - **5. `standard`:** Təhlükəsiz yerli Wine Wayland + aşağı gecikməli VRR profili.
4. **VRR Yenilənmə Tezliyi Məhdudiyyəti:** Açıq şəkildə təyin edilmiş `VRR_CAP=<fps>` həmişə üstünlük təşkil edir (`VRR_CAP=0` məhdudiyyəti söndürür). Əks halda aktiv ekranın yenilənmə tezliyi `kscreen-doctor` (KDE Plasma 6 aktiv `*` rejimi və ya ənənəvi `Hz`), `wlr-randr` və ya `xrandr` vasitəsilə yoxlanılır və standart olaraq 1:1 nisbətində tətbiq edilir (240 Hz ekranda `240 FPS`). İstəyə bağlı `-6%` VRR təhlükəsizlik ehtiyatı üçün `VRR_MINUS_MARGIN=1` aktivləşdirin (`hz * 94 / 100`, məsələn 240 Hz-də `225 FPS`). Gamescope sessiyalarında `VRR_CAP` açıq göstərilmədikcə DXVK/VKD3D limitləri tətbiq olunmur.
5. **Qarşılıqlı İstisna Qoruyucuları:**
   - **FSR 4 / OptiScaler + vkBasalt:** `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` və ya `USE_OPTISCALER=1` aktiv olduqda `ENABLE_VKBASALT=0` məcburi tətbiq edilir (ikiqat kəskinləşdirmənin və HDR10 kəsilməsinin qarşısını alır).
   - **MLFG + Aşağı Gecikmə / VRR Limitləri:** `MLFG=1` (`USE_MLFG=1`) dəyişənləri `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0` olaraq ixrac edir, `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` və `DXVK_FRAME_PACE` dəyişənlərini silir və AMD RDNA 3-də `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` ixrac edir. `USE_MLFG=0` olduqda və VRR limiti aktivləşdikdə `DXVK_FRAME_PACE=low-latency-vrr` ixrac edilir.
   - **Müasir DX12 + Safe DX12:** AMD-də `PROTON_NATIVE_AGS=1` və `USE_SAFEDX12=0` olduqda `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` ixrac edir (`SAFEDX12=1` olduqda təmiz şəkildə buraxılır).
6. **Compat-Token Xəritələməsi:** İdarə olunan funksiyalar istifadəçinin mövcud dəyərlərini pozmadan həm `PROTON_ADD_CONFIG`, həm də `STEAM_COMPAT_CONFIG` dəyişənlərinə əlavə edilir: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Avtomatik KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** Gamescope xaricində `DXVK_HDR=1` (və ya `USE_HDR=1`) ilə aktivləşdirildikdə `kscreen-doctor -o` vasitəsilə əsas aktiv ekranı yoxlayır; HDR hazırda söndürülübsə, başlatmadan əvvəl onu aktivləşdirir və çıxışda `EXIT`/`INT`/`TERM` tutucusu (trap) ilə SDR-i bərpa edir.
8. **Səssiz Kadr Vaxtı Testi (`BENCH=1`):** MangoHud-u gizli CSV rejimində işə salır (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), çıxış zamanı kadr vaxtlarını təhlil edir, `Avg FPS`, `1% Low FPS` və `P99 (ms)` nəticələrini `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` faylına əlavə edir və müvəqqəti CSV fayllarını silir.
9. **Sürətli Çökmə Üçün Təhlükəsiz Rejim (Safe Mode) Avto-Bərpası:** Əgər Proton/Windows oyunu eksperimental Wayland və ya DX12 bayraqları aktiv ikən (`USE_XWAYLAND=0` və ya `USE_SAFEDX12=0`) `20s`-dən az müddətdə (`SAP_CRASH_THRESHOLD_SEC` ilə tənzimlənir) sıfırdan fərqli kodla bağlanarsa, `last-<APPID>.log` və `last-launch.log` fayllarına `crash_hint` qeyd edir və (GUI aktiv olduqda) növbəti başlatma üçün `USE_XWAYLAND=1` + `USE_SAFEDX12=1` saxlamağı təklif edir.
10. **Planlaşdırıcı və Şəbəkə Həyat Dövrü:** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (yalnız `ananicy-cpp.service` qeyri-aktiv olduqda) -> birbaşa icra zənciri ilə, istəyə bağlı `PRIME=1` (`prime-run`) dəstəyi ilə işləyir. `USE_NET_OPT=1` olduqda `steam-net-boost` statik root CAKE və HTB + leaf CAKE iyerarxiyalarını qoruyaraq `flock` kilidi ilə istinad sayğaclı `on`/`off` əməliyyatını icra edir.

---

## Vahid İdarəetmə Mərkəzi (`steam-auto-ui`)

`steam-auto-ui` proqramını iş masasının tətbiq menyusundan, `steam-auto-run --ui` əmri ilə və ya birbaşa başladın:

```bash
steam-auto-ui                 # Qt6 GUI (PyQt6/PySide6) və ya curses TUI rejimini avtomatik seçir
steam-auto-ui --gui           # Yerli Qt6 GUI pəncərəsini məcburi aç
steam-auto-ui --tui           # Standart kitabxana curses TUI rejimini məcburi aç (SSH üzərindən işləyir)
steam-auto-ui --lang az       # Açıq şəkildə seçilmiş UI dili ilə başlat (27 dil dəstəklənir)
steam-auto-ui --check         # Başsız özünüyoxlama icra et (JSON diaqnostikasını çap edir)
```

`steam-auto-ui` sistem dilini `LC_ALL` / `LC_MESSAGES` / `LANG` dəyişənlərindən avtomatik müəyyən edir və proqramı yenidən başlatmadan 27 dil arasında canlı keçid etmək üçün Qt6 GUI-də dil seçici siyahısı (`curses` TUI-də isə `L` qısayol düyməsi) təqdim edir.

### Beş Sinxronlaşdırılmış Görünüş

1. **Games & Profiles:** Steam oyunlarının və yalnız-oxuma qeyri-Steam `shortcuts.vdf` qeydlərinin filtrlənə bilən cədvəli (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), Upscaler SDK nişanı (`AUTO_UPSCALER_INFO`), bütün 10 profil açarı + `VRR_CAP` üzrə canlı qarşılıqlı istisna yoxlaması, `Dry-Run Preview`, `Benchmarks` keçid düyməsi və `Reset Profile`.
2. **System & Telemetry:** Bloklamayan canlı göstəricilər: `steam-auto-run --doctor`, `scxctl get` / `sched_ext` statusu, quraşdırılmış paket versiyaları (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), şeyder keşi istifadəsi (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` git/AUR versiya enməsi xəbərdarlıqları, GPU VRAM/yüklənmə/temperatur, `tc -s qdisc` LAN (`10:`) və WAN (`20:`/root) ötürmə qabiliyyəti ilə `av_delay`, həmçinin `vr-mode status`.
3. **Library Sync:** Steam-in işlək vəziyyətini göstərən canlı qoruyucu banner və bir kliklə `--report`, `--sanitize --dry-run`, `--sanitize` (Steam işləyərkən rədd edilir) və `--migrate-cachy-run` əməliyyatları.
4. **Logs & Recovery:** `last-launch.log` və `last-<APPID>.log` jurnallarına baxın, `crash_hint` xəbərdarlıqlarını yoxlayın və bir kliklə Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) tətbiq edin.
5. **Benchmarks:** `BENCH=1` kadr vaxtı sınaqlarının filtrlənə bilən yan-yana müqayisə cədvəli (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR Orkestrasiyası (`vr-run`)

VR oyunları üçün Steam-də **Xüsusiyyətlər > Ümumi > Başlatma Seçimləri** bölməsinə bunu daxil edin:

```text
vr-run %command%
```

- Miras qalmış flatscreen tənzimləmələrini təmizləyir (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- `MESA_VK_DEVICE_SELECT` vasitəsilə ən yüksək VRAM-a malik diskret GPU-nu avtomatik seçir və AMD GPU-larında `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` təyin edir.
- WiVRn və xrizer OpenXR/OpenVR yollarını dinamik yoxlayır (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) və istifadəçinin açıq seçimlərini pozmadan `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` və `LD_LIBRARY_PATH` dəyişənlərini konfiqurasiya edir.
- `vr-mode` quraşdırıldıqda `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` faylında (`flock` ilə) istinad sayğaclı `vr-mode on` / `vr-mode off` idarə edir (`VR_AUTO_MODE=0` bunu söndürür).
- Eyni `ananicy-cpp` nəzərə alan planlaşdırıcı zəncirindən keçir (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> birbaşa `exec`).
- İstənilən vaxt həll edilmiş dəyişənləri `vr-run --dry-run` ilə önizləyin.

`steam-auto-run` SteamVR (`250820`) və `-vr`/`--vr` başlatmalarını avtomatik ötürür, `steam-auto-sync` isə VR oyunları üçün `vr-run %command%` əmrini avtomatik təyin edib qoruyur.

---

## Steam Kitabxana Sinxronizasiyası (`steam-auto-sync`)

`localconfig.vdf` faylına yazmazdan əvvəl Steam-i tamamilə bağlayın:

```bash
steam-auto-sync --report              # Yalnız-oxuma kitabxana + shortcuts.vdf auditi
steam-auto-sync --print-library-paths # Aşkar edilmiş bütün Steam kitabxanalarını göstər
steam-auto-sync --dry-run             # Dəyişiklikləri önizlə
steam-auto-sync                       # steam-auto-run / vr-run əlavə et
steam-auto-sync --sanitize --dry-run  # Köhnə bayraqların təmizlənməsini önizlə
steam-auto-sync --sanitize            # Qarışıq/yetim bayraqları təmizlə (alternativ: --clean)
steam-auto-sync --migrate-cachy-run   # Köhnə cachy-run profillərini miqrasiya et
steam-auto-sync --remove              # steam-auto-run qabığını sil
```

- Zaman damğalı `localconfig.vdf.bak.*` ehtiyat nüsxələri `--keep-backups N` parametri ilə avtomatik azaldılır (standart `10`; `0` hamısını saxlayır).
- Müəyyən AppID-ləri istisna etmək üçün onları (hər sətirdə bir ədəd, `#` şərhlərinə icazə verilir) `~/.config/steam-auto-profiler/ignore_appids.txt` faylında siyahılayın.
- Systemd auto-sync izləyicisi (`./install.sh --with-auto-sync` və ya `steam-auto-sync --install-systemd`) Steam manifestləri dəyişdikdə `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` əmrini işə salır.

---

## CLI və Profil Arayışı

### Əmrlər

| Məqsəd | Əmr |
| --- | --- |
| Sistemin hazırlıq yoxlaması | `steam-auto-run --doctor` (alternativ `--check-system`) |
| İdarəetmə Mərkəzini başlat (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` və ya `steam-auto-run --ui` |
| Oyunu yoxla (oxunaqlı format) | `steam-auto-run --inspect APPID` |
| Oyunu yoxla (JSON) | `steam-auto-detect --inspect --json APPID` |
| Profili interaktiv yenidən qur | `steam-auto-run --configure APPID` |
| Başlatma mühitini önizlə | `steam-auto-run --dry-run APPID` |
| Saxlanmış profili sıfırla | `steam-auto-run --reset APPID` |
| Saxlanmış profilləri siyahıla | `steam-auto-run --list-profiles` |
| Son başlatma jurnalını göstər | `steam-auto-run --last-log [APPID]` |
| VR başlatma mühitini önizlə | `vr-run --dry-run` |
| Şəbəkə köməkçisini yoxla (yalnız-oxuma) | `steam-net-boost status [IFACE]` |

### Saxlanmış `.env` Profil Açarları və Mühit Ötürmələri

Profil faylları `~/.config/steam-auto-profiler/profiles/<APPID>.env` yolunda saxlanılır və icazə verilən açarlar siyahısı üzrə `KEY=VALUE` formatını qəbul edir (shell əmr əvəzetmələri və naməlum açarlar təhlükəsiz şəkildə iqnor edilir):

| `.env` Açarı | Mühit Ötürməsi | Təsir |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Yerli Wine Wayland əvəzinə XWayland-ı məcbur et |
| `USE_FSR4=0` | `FSR4=0` | Drayver səviyyəli FSR 4 yüksəltməsini söndür (standart `1`) |
| `USE_MLFG=1` | `MLFG=1` | Kadr generasiyasını aktivləşdir (Anti-Lag, aşağı gecikmə və VRR limitlərini söndürür) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | OptiScaler körpüsünü aktivləşdir (`competitive-anticheat` üçün qoruyucu ilə bağlıdır) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | vkBasalt kəskinləşdirməsini aktivləşdir (FSR 4 və ya OptiScaler aktiv olduqda söndürülür) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Eksperimental `VKD3D_CONFIG` bayraqlarını və `vkd3dbindlesstb` tokenini burax |
| `USE_NET_OPT=1` | `NETOPT=1` | `steam-net-boost` vasitəsilə sessiya şəbəkə QoS-unu aktivləşdir |
| `USE_SDL=1` | `SDL=1` | Yerli SDL / Steam Input emulyasiyasına üstünlük ver |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Steam Overlay `LD_PRELOAD` dəyərini qoru |
| `USE_CEF_FIX=1` | `CEF=1` | CEF başlatıcıları üçün `--in-process-gpu` əlavə et |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Köhnə oyunlar üçün NTSync-i söndür |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Pəncərə idarəedicisinin çərçivələrini söndür |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Fərdi DXVK/VKD3D kadr limiti (`0` məhdudiyyəti söndürür) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Monitor tezliyinə `-6%` ehtiyat tətbiq et (məs. 240 Hz-də `225 FPS`) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Wine Wayland altında qısayol bloklamasına icazə ver (standart `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Başlatmada KDE Plasma 6 HDR-i avtomatik aç və çıxışda SDR-i bərpa et |
| — | `BENCH=1`, `BENCH_DURATION=60` | Səssiz MangoHud CSV testi icra et və JSON xülasəsini saxla |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Başlatma öncəsi `kdialog`/`zenity` yoxlama siyahısını gizlət və ya məcburi aç |
| — | `FSR_HUD=1` | FSR/DLSS/MLFG HUD göstərici dəyişənlərini ixrac et |
| — | `VULKAN=1` / `PRIME=1` | `-vulkan` əlavə et / `prime-run` ilə sar |
| — | `GAMEID=umu-<appid>` | UMU / Lutris / Heroic AppID-lərini təyin et |

---

## Lutris, Heroic, Faugus və UMU

- **Lutris:** Təkmil seçimləri aktivləşdirin, `proton-cachyos-slr` (və ya öz Proton quruluşunuzu) seçin, Lutris runtime-ı söndürün, sistem kitabxanalarına üstünlük verin və əmr prefiksini `steam-auto-run` təyin edin.
- **Heroic / Faugus:** `proton-cachyos-slr` seçin və qabıq/əmr prefiksi kimi `steam-auto-run` əlavə edin.
- **UMU / Protonfixes:** Lazım olduqda `PROTON_VERB=waitforexitandrun` və `GAMEID=umu-<appid>` dəyişənlərini ixrac edin.

---

## Problemlərin Aradan Qaldırılması

- **Wayland və ya DX12-də sürətli çökmə:** `steam-auto-ui` daxilində **Logs & Recovery** bölməsini açın (və ya `steam-auto-run --last-log APPID` icra edin) və Safe Mode (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) tətbiq edin, yaxud `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%` ilə başladın.
- **Anti-cheat oyunları açılmır:** `proton-cachyos-slr` (Steam Linux Runtime) istifadə edin və EAC v2, `/dev/ntsync` və `vm.max_map_count` parametrlərini yoxlamaq üçün `steam-auto-run --doctor` icra edin.
- **Steam başlatma seçimlərini geri qaytarır:** `steam-auto-sync` və ya `steam-auto-sync --sanitize` əmrlərini işə salmadan əvvəl Steam-i tamamilə bağlayın.
- **Yanlış və ya çatışmayan VRR limiti:** `VRR_CAP=<fps>` dəyərini açıq təyin edin, söndürmək üçün `VRR_CAP=0`, `-6%` ehtiyat üçün isə `VRR_MINUS_MARGIN=1` istifadə edin. Gamescope-da yalnız açıq təyin edilmiş `VRR_CAP` DXVK/VKD3D limitlərini ixrac edir.
- **Şəbəkə QoS yoxlaması:** `steam-net-boost status` əmrini icra edin (imtiyazsız, yalnız-oxuma). Avtomatik sessiya QoS-u istəyirsinizsə, root köməkçisini `./install.sh --with-net-boost` ilə quraşdırın.

---

## v2.1 yenilikləri (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 və Steam Controller 2026)

- **Mesa 27.0 / RDNA 4 bayraqları:** `TRANSFER_QUEUE=1` (RDNA 3/4 üçün təkrarsız `RADV_PERFTEST=sam,transfer_queue`), `NATIVE_ANTILAG=1` (yerli `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, anti-cheat və MLFG-də bloklanır) və `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** anti-cheatsiz oyunlar üçün eksperimental stek (`VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1` və `WAYLANDDRV_RAWINPUT=1` yalnız Gamescope xaricindəki yerli Wayland-da).
- **Hunt: Showdown 1896 (`AppID 594650`) qoruması:** `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, `USE_NET_OPT=1` tətbiq edir; `--doctor` və `steam-auto-ui` `config.vdf` içində `Proton 11.0-2` / `Proton Hotfix` yoxlayır.
- **Steam Controller 2026 / Wireless Puck (`28de:{1302,1304,1005,1007}`):** 4 rejim (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` yerli Wayland + HDR10 (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`) saxlayır, `steam://forceinputappid/<APPID>` və `udevadm` yenidən qoşulma izləyicisini işə salır, çıxışda `steam://forceinputappid/0` sıfırlayır. Əllə: `steam-auto-run --reapply-input <APPID|0>`; udev: `./install.sh --with-steam-controller`.

---

Dizayn detalları üçün [ARCHITECTURE.md](../../ARCHITECTURE.md), əsas ingiliscə təlimat üçün [English User Guide](../../USER_GUIDE.md) və bütün 27 tərcümə edilmiş bələdçi üçün [i18n Index](../README.md) səhifəsinə baxın.
