# Steam Auto-Profiler Kullanıcı Kılavuzu

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Bu kılavuz, **Steam Auto-Profiler v2.1** için eksiksiz kurulumu, düz ekran ve VR başlatma orkestrasyonunu, `steam-auto-ui` Kontrol Merkezini, kütüphane senkronizasyonunu, kıyaslama (benchmark) ölçümlerini ve sorun giderme adımlarını kapsar.

Steam Auto-Profiler; bir Steam AppID'sini (veya Steam dışı bir kısayolu) inceleyen, sürücü/ölçekleyici/anti-cheat için sıkı koruma kurallarıyla bağlama duyarlı bir profil uygulayan ve mevcut oyun komutunu başlatan hafif bir Linux Bash/Python başlatıcısı ve kontrol merkezidir. Asla üçüncü taraf bir Proton çalışma zamanı paketlemez veya enjekte etmez.

---

## Gereksinimler

- Linux masaüstü oturumu (KDE Plasma 6 / Wayland, GNOME, wlroots veya X11), Bash 5+, Python 3.10+, Steam ve standart temel araçlar.
- İsteğe bağlı yerel Kontrol Merkezi arayüzü (GUI): `PyQt6` veya `PySide6` (kurulu değilse bağımlılıksız standart kütüphane `curses` TUI'sine otomatik olarak geçer).
- İsteğe bağlı başlatma öncesi kontrol listesi pencereleri: `kdialog` veya `zenity`.
- İsteğe bağlı sessiz kare süresi (frametime) benchmark ölçümü: `mangohud`.
- İsteğe bağlı oturum ağ yardımcısı: `tc`, `ip` ve `ethtool` (`sudo` yalnızca `--with-net-boost` kurulumu sırasında gerekir).

---

## Kurulum ve Güncellemeler

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` altı çalıştırılabilir dosyanın tamamını (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` ve `steam-auto-ui`) `~/.local/bin` dizinine kopyalar, masaüstü kısayolunu (`~/.local/share/applications/steam-auto-profiler.desktop`) kurar, `~/.config/steam-auto-profiler/profiles` dizinini oluşturur ve varsayılan vkBasalt ön ayarlarını (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`) ekler. `~/.local/bin` dizininin `PATH` içinde olduğundan emin olun.

İsteğe bağlı kurulum bayrakları birleştirilebilir:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: `/usr/local/bin/steam-net-boost` dosyasını (diğer betiklerin sistem kopyalarıyla birlikte) ve `steam-net-boost` için dar kapsamlı, parolasız bir `sudoers` kuralını kurar.
- `--compat-cachy-run`: Mevcut bir `/usr/local/bin/cachy-run` dosyasını (zaten Steam Auto-Profiler yönlendirme katmanı değilse) `/usr/local/bin/cachy-run.bak` olarak yedekler ve `steam-auto-run` komutuna yönlendiren bir uyumluluk katmanı (shim) kurar.
- `--with-auto-sync` (`--enable-auto-sync`): Keşfedilen tüm Steam kütüphanelerinde `steam-auto-profiler-sync.path` systemd kullanıcı izleyicisini ve eşleşen oneshot hizmetini kurup etkinleştirir.
- `--uninstall`: Kurulu ikili dosyaları, masaüstü kısayolunu, isteğe bağlı ağ yardımcısını/sudoers kuralını, uyumluluk katmanını ve otomatik senkronizasyon systemd kullanıcı birimlerini kaldırır.

Mevcut bir depoyu güncellemek için:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Oyunları senkronize etmeden önce sistemin hazır olduğunu doğrulayın:

```bash
steam-auto-run --doctor
```

---

## Uçtan Uca Başlatma Hattı

1. **AppID Çözümleme:** Sırasıyla `SteamAppId`, `STEAM_COMPAT_APP_ID` ve ardından `GAMEID` değerlerini kontrol eder (Lutris/Heroic/UMU için `umu-` önekini temizler).
2. **Kütüphane ve Kısayol Keşfi:** `steam-auto-detect`, Steam kök dizinlerini ve `libraryfolders.vdf` içindeki ikincil kütüphaneleri tarar, `appmanifest_<APPID>.acf` dosyasını okur veya salt okunur olarak ikili `userdata/*/config/shortcuts.vdf` dosyasına geçer; ardından en fazla 10 düzey derinlikte tek geçişli bir `find` çalıştırır (`screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization` dizinlerini atlar).
3. **Beş Katmanlı Sınıflandırma Önceliği:**
   - **1. `competitive-anticheat`:** Bilinen rekabetçi AppID veya algılanan anti-cheat çalışma zamanı (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE vb.). OptiScaler, MLFG, vkBasalt ve asenkron DXVK'yi devre dışı bırakır; düşük gecikmeyi ve oturum ağı QoS'unu etkinleştirir.
   - **2. `vr`:** `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` veya `vr-run`/`-vr` kısayol bayraklarını algılar. `AUTO_IS_VR=1` değişkenini dışa aktarır.
   - **3. `native-fsr4` / `native-fsr`:** Modüler FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Sürücü düzeyinde FSR4 yükseltmesini etkinleştirir (`PROTON_FSR4_UPGRADE=1` veya AMD RDNA 3 üzerinde `PROTON_FSR4_RDNA3_UPGRADE=1`).
   - **4. `legacy-upscaler`:** Eski DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) veya FSR 2/3.0 DLL'leri. `AUTO_OPTISCALER=1` olarak işaretler ve `AUTO_UPSCALER_INFO` rehberliğini ayarlar.
   - **5. `standard`:** Güvenli yerel Wine Wayland + düşük gecikmeli VRR profili.
4. **VRR Yenileme Hızı Sınırlama:** Açıkça belirtilen `VRR_CAP=<fps>` her zaman önceliklidir (`VRR_CAP=0` sınırlamayı devre dışı bırakır). Aksi halde etkin ekran yenileme hızı `kscreen-doctor` (KDE Plasma 6 etkin `*` modu veya eski `Hz`), `wlr-randr` ya da `xrandr` üzerinden algılanır ve varsayılan olarak 1:1 uygulanır (240 Hz üzerinde `240 FPS`). İsteğe bağlı `-6%` VRR güvenlik payı (`hz * 94 / 100`, örn. 240 Hz'de `225 FPS`) için `VRR_MINUS_MARGIN=1` etkinleştirilir. Gamescope oturumlarında, açıkça `VRR_CAP` verilmedikçe DXVK/VKD3D sınırları eklenmez.
5. **Karşılıklı Dışlama Korumaları:**
   - **FSR 4 / OptiScaler + vkBasalt:** `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` veya `USE_OPTISCALER=1` etkin olduğunda `ENABLE_VKBASALT=0` zorunlu tutulur (çift keskinleştirme ve HDR10 kırpılmasını önler).
   - **MLFG + Düşük Gecikme / VRR Sınırları:** `MLFG=1` (`USE_MLFG=1`) etkin olduğunda `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0` dışa aktarılır; `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` ve `DXVK_FRAME_PACE` kaldırılır; AMD RDNA 3 üzerinde `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` dışa aktarılır. `USE_MLFG=0` ve VRR sınırlaması etkinse `DXVK_FRAME_PACE=low-latency-vrr` dışa aktarılır.
   - **Modern DX12 + Safe DX12:** `USE_SAFEDX12=0` iken AMD üzerinde `PROTON_NATIVE_AGS=1` ve `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` dışa aktarılır (`SAFEDX12=1` iken temiz biçimde atlanır).
6. **Uyumluluk Belirteci (Compat-Token) Eşleme:** Yönetilen özellikler mevcut kullanıcı değerlerini ezmeden hem `PROTON_ADD_CONFIG` hem de `STEAM_COMPAT_CONFIG` değişkenlerine eklenir: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **Otomatik KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** Gamescope dışında `DXVK_HDR=1` (veya `USE_HDR=1`) ile etkinleştirildiğinde `kscreen-doctor -o` üzerinden birincil etkin çıkışı sorgular; HDR kapalıysa başlatmadan önce açar ve çıkışta `EXIT`/`INT`/`TERM` tuzağı ile SDR'ye geri döndürür.
8. **Sessiz Kare Süresi Kıyaslaması (`BENCH=1`):** MangoHud'u gizli CSV modunda (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`) çalıştırır, çıkışta kare sürelerini ayrıştırır, `Avg FPS`, `1% Low FPS` ve `P99 (ms)` değerlerini `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` dosyasına ekler ve geçici CSV dosyalarını siler.
9. **Hızlı Çökmede Güvenli Mod Otomatik Kurtarma:** Deneysel Wayland veya DX12 bayrakları etkinken (`USE_XWAYLAND=0` veya `USE_SAFEDX12=0`) bir Proton/Windows oyunu `20s` altında (`SAP_CRASH_THRESHOLD_SEC` ile ayarlanabilir) sıfırdan farklı bir çıkış koduyla kapanırsa, `last-<APPID>.log` ve `last-launch.log` içine bir `crash_hint` kaydeder ve (GUI etkinken) sonraki başlatma için `USE_XWAYLAND=1` + `USE_SAFEDX12=1` kaydetmeyi önerir.
10. **Zamanlayıcı ve Ağ Yaşam Döngüsü:** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (yalnızca `ananicy-cpp.service` etkin değilse) -> doğrudan çalıştırma zincirini izler ve isteğe bağlı `PRIME=1` (`prime-run`) destekler. `USE_NET_OPT=1` ise `steam-net-boost`, statik root CAKE ile HTB + leaf CAKE hiyerarşilerini koruyarak `flock` ile başvuru sayaçlı `on`/`off` çalıştırır.

---

## Birleşik Kontrol Merkezi (`steam-auto-ui`)

`steam-auto-ui` uygulamasını masaüstü uygulama menüsünden, `steam-auto-run --ui` ile veya doğrudan başlatın:

```bash
steam-auto-ui                 # Qt6 GUI (PyQt6/PySide6) veya curses TUI'yi otomatik algılar
steam-auto-ui --gui           # Yerel Qt6 GUI penceresini zorlar
steam-auto-ui --tui           # Standart kütüphane curses TUI'sini zorlar (SSH üzerinden çalışır)
steam-auto-ui --lang fi       # Açık bir arayüz diliyle başlatır (27 dil desteklenir)
steam-auto-ui --check         # Başsız öz-denetim çalıştırır (JSON tanılama yazdırır)
```

`steam-auto-ui`, sistem yerel ayarını `LC_ALL` / `LC_MESSAGES` / `LANG` değişkenlerinden otomatik algılar ve yeniden başlatmaya gerek kalmadan tüm 27 dil arasında anlık geçiş için Qt6 GUI'de canlı dil açılır listesi (`curses` TUI'de `L` kısayolu) sunar.

### Beş Senkronize Görünüm

1. **Oyunlar ve Profiller:** Steam oyunları ve salt okunur Steam dışı `shortcuts.vdf` girişleri için filtrelenebilir tablo (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), Ölçekleyici SDK rozeti (`AUTO_UPSCALER_INFO`), 10 profil anahtarı + `VRR_CAP` genelinde canlı karşılıklı dışlama doğrulaması, `Dry-Run Preview`, `Benchmarks` geçiş düğmesi ve `Reset Profile`.
2. **Sistem ve Telemetri:** `steam-auto-run --doctor` için engellemesiz canlı çıktı, `scxctl get` / `sched_ext` durumu, kurulu yığın sürümleri (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), gölgelendirici önbellek kullanımı (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` git/AUR sürüm düşürme uyarıları, GPU VRAM/kullanım/sıcaklık, `tc -s qdisc` LAN (`10:`) - WAN (`20:`/root) aktarımı ve `av_delay`, ayrıca `vr-mode status`.
3. **Kütüphane Senkronizasyonu:** Canlı Steam çalışma durumu koruma şeridi ve `--report`, `--sanitize --dry-run`, `--sanitize` (Steam çalışırken engellenir) ile `--migrate-cachy-run` için tek tıkla eylemler.
4. **Günlükler ve Kurtarma:** `last-launch.log` ve `last-<APPID>.log` kayıtlarına göz atın, `crash_hint` uyarılarını inceleyin ve tek tıkla Güvenli Mod (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) uygulayın.
5. **Kıyaslamalar (Benchmarks):** `BENCH=1` kare süresi koşularının filtrelenebilir yan yana karşılaştırma tablosu (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR Orkestrasyonu (`vr-run`)

VR oyunları için Steam **Özellikler > Genel > Başlatma Seçenekleri** alanını şöyle ayarlayın:

```text
vr-run %command%
```

- Miras alınan düz ekran geçersiz kılmalarını temizler (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- `MESA_VK_DEVICE_SELECT` ile en yüksek VRAM'e sahip harici GPU'yu otomatik seçer ve AMD GPU'larda `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` ayarlar.
- WiVRn ve xrizer OpenXR/OpenVR yollarını (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) dinamik olarak algılar ve kullanıcının açıkça belirttiği değerleri ezmeden `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` ile `LD_LIBRARY_PATH` değişkenlerini yapılandırır.
- `vr-mode` kuruluysa `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` içinde (`flock` ile) `vr-mode on` / `vr-mode off` başvuru sayımı yapar (`VR_AUTO_MODE=0` bunu kapatır).
- Aynı `ananicy-cpp` duyarlı zamanlayıcı zincirinden (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> doğrudan `exec`) geçer.
- Çözümlenen değişkenleri istediğiniz zaman `vr-run --dry-run` ile önizleyin.

`steam-auto-run`, SteamVR (`250820`) ve `-vr`/`--vr` başlatmalarını otomatik olarak atlar; `steam-auto-sync` ise VR oyunlarına `vr-run %command%` seçeneğini otomatik atar ve korur.

---

## Steam Kütüphane Senkronizasyonu (`steam-auto-sync`)

`localconfig.vdf` dosyasına yazmadan önce Steam'i tamamen kapatın:

```bash
steam-auto-sync --report              # Salt okunur kütüphane + shortcuts.vdf denetimi
steam-auto-sync --print-library-paths # Keşfedilen tüm Steam kütüphanelerini göster
steam-auto-sync --dry-run             # Değişiklikleri önizle
steam-auto-sync                       # steam-auto-run / vr-run enjekte et
steam-auto-sync --sanitize --dry-run  # Eski bayrak temizliğini önizle
steam-auto-sync --sanitize            # Dağınık/artık bayrakları temizle (diğer ad: --clean)
steam-auto-sync --migrate-cachy-run   # Eski cachy-run profillerini taşı
steam-auto-sync --remove              # steam-auto-run sarmalayıcısını kaldır
```

- Zaman damgalı `localconfig.vdf.bak.*` yedekleri `--keep-backups N` ile otomatik budanır (varsayılan `10`; `0` tümünü saklar).
- Belirli AppID'leri dışlamak için bunları `~/.config/steam-auto-profiler/ignore_appids.txt` dosyasına satır başına bir tane olacak şekilde yazın (`#` yorumları desteklenir).
- Systemd otomatik senkronizasyon izleyicisi (`./install.sh --with-auto-sync` veya `steam-auto-sync --install-systemd`), Steam manifestleri değiştiğinde `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` komutunu çalıştırır.

---

## CLI ve Profil Başvuru Kılavuzu

### Komutlar

| Amaç | Komut |
| --- | --- |
| Sistem hazırlık denetimi | `steam-auto-run --doctor` (diğer ad `--check-system`) |
| Kontrol Merkezini başlat (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` veya `steam-auto-run --ui` |
| Oyunu incele (okunabilir) | `steam-auto-run --inspect APPID` |
| Oyunu incele (JSON) | `steam-auto-detect --inspect --json APPID` |
| Profili etkileşimli yeniden yapılandır | `steam-auto-run --configure APPID` |
| Çözümlenen başlatma ortamını önizle | `steam-auto-run --dry-run APPID` |
| Kayıtlı profili sıfırla | `steam-auto-run --reset APPID` |
| Kayıtlı profilleri listele | `steam-auto-run --list-profiles` |
| Son başlatma günlüğünü göster | `steam-auto-run --last-log [APPID]` |
| VR başlatma ortamını önizle | `vr-run --dry-run` |
| Ağ yardımcısını incele (salt okunur) | `steam-net-boost status [IFACE]` |

### Kayıtlı `.env` Profil Anahtarları ve Ortam Geçersiz Kılmaları

Profil dosyaları `~/.config/steam-auto-profiler/profiles/<APPID>.env` konumunda bulunur ve izin listeli `KEY=VALUE` biçimini kabul eder (kabuk komut ikameleri ve bilinmeyen anahtarlar güvenle yok sayılır):

| `.env` Anahtarı | Ortam Geçersiz Kılma | Etki |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Yerel Wine Wayland yerine XWayland zorlar |
| `USE_FSR4=0` | `FSR4=0` | Sürücü düzeyinde FSR 4 yükseltmesini kapatır (varsayılan `1`) |
| `USE_MLFG=1` | `MLFG=1` | Kare oluşturmayı açar (Anti-Lag, düşük gecikme ve VRR kare sınırlarını kapatır) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | OptiScaler köprüsünü etkinleştirir (`competitive-anticheat` için korumalı kapalı) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | vkBasalt keskinleştirmeyi açar (FSR 4 veya OptiScaler etkinken devre dışı) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Deneysel `VKD3D_CONFIG` bayraklarını ve `vkd3dbindlesstb` belirtecini atlar |
| `USE_NET_OPT=1` | `NETOPT=1` | `steam-net-boost` ile oturum ağı QoS'unu etkinleştirir |
| `USE_SDL=1` | `SDL=1` | Yerel SDL / Steam Input öykünmesini tercih eder |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Steam Arayüzü `LD_PRELOAD` değerini korur |
| `USE_CEF_FIX=1` | `CEF=1` | CEF başlatıcıları için `--in-process-gpu` ekler |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Eski oyunlar için NTSync'i devre dışı bırakır |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Pencere yöneticisi kenarlıklarını devre dışı bırakır |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Özel DXVK/VKD3D kare hızı sınırı (`0` sınırlamayı kapatır) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Monitör yenileme hızında `-6%` pay uygular (örn. 240 Hz'de `225 FPS`) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Wine Wayland altında kısayol engellemeye izin verir (varsayılan `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Başlatmada KDE Plasma 6 HDR'yi otomatik açar, çıkışta SDR'ye döner |
| — | `BENCH=1`, `BENCH_DURATION=60` | Sessiz MangoHud CSV kıyaslaması çalıştırır ve JSON özeti kaydeder |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Başlatma öncesi `kdialog`/`zenity` kontrol listesini gizler veya zorla açar |
| — | `FSR_HUD=1` | FSR/DLSS/MLFG HUD gösterge değişkenlerini dışa aktarır |
| — | `VULKAN=1` / `PRIME=1` | `-vulkan` ekler / `prime-run` ile sarar |
| — | `GAMEID=umu-<appid>` | UMU / Lutris / Heroic AppID'lerini çözümler |

---

## Lutris, Heroic, Faugus ve UMU

- **Lutris:** Gelişmiş seçenekleri etkinleştirin, `proton-cachyos-slr` (veya kendi Proton derlemenizi) seçin, Lutris çalışma zamanını devre dışı bırakın, sistem kütüphanelerini tercih edin ve komut önekini `steam-auto-run` olarak ayarlayın.
- **Heroic / Faugus:** `proton-cachyos-slr` seçin ve sarmalayıcı/komut öneki olarak `steam-auto-run` ekleyin.
- **UMU / Protonfixes:** Gerektiğinde `PROTON_VERB=waitforexitandrun` ve `GAMEID=umu-<appid>` dışa aktarın.

---

## Sorun Giderme

- **Wayland veya DX12 üzerinde hızlı çökme:** `steam-auto-ui` içinde **Günlükler ve Kurtarma** sekmesini açın (veya `steam-auto-run --last-log APPID` çalıştırın) ve Güvenli Mod (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`) uygulayın ya da `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%` ile başlatın.
- **Anti-cheat oyunları başlamıyor:** `proton-cachyos-slr` (Steam Linux Runtime) kullanın ve EAC v2, `/dev/ntsync` ile `vm.max_map_count` ayarlarını doğrulamak için `steam-auto-run --doctor` çalıştırın.
- **Steam başlatma seçeneklerini geri alıyor:** `steam-auto-sync` veya `steam-auto-sync --sanitize` çalıştırmadan önce Steam'i tamamen kapatın.
- **Yanlış veya eksik VRR sınırı:** Açıkça `VRR_CAP=<fps>` ayarlayın, kapatmak için `VRR_CAP=0` veya `-6%` pay için `VRR_MINUS_MARGIN=1` kullanın. Gamescope içinde yalnızca açıkça belirtilen `VRR_CAP` DXVK/VKD3D sınırlarını dışa aktarır.
- **Ağ QoS kontrolü:** `steam-net-boost status` (yetkisiz, salt okunur) çalıştırın. Otomatik oturum QoS'u istiyorsanız `./install.sh --with-net-boost` ile root yardımcısını kurun.

---

## v2.1 Yenilikleri (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650 ve Steam Controller 2026)

- **Mesa 27.0 / RDNA 4 Bayrakları:** `TRANSFER_QUEUE=1` (RDNA 3/4 için tekilleştirilmiş `RADV_PERFTEST=sam,transfer_queue`), `NATIVE_ANTILAG=1` (yerel `VK_AMD_anti_lag`), `REFLEX_LAYER=1` (`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, anti-cheat ve MLFG'de engellenir) ve `VK_VIDEO_DECODE=1` (`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** anti-cheat olmayan oyunlar için deneysel yığın (`VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, yalnızca Gamescope dışındaki yerel Wayland'da `WAYLANDDRV_RAWINPUT=1`).
- **Hunt: Showdown 1896 (`AppID 594650`) Koruması:** `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0` ve `USE_NET_OPT=1` zorlar; `--doctor` ve `steam-auto-ui`, `config.vdf` içinde `Proton 11.0-2` veya `Proton Hotfix` denetimi yapar.
- **Steam Controller 2026 / Wireless Steam Puck (`28de:{1302,1304,1005,1007}`):** 4 yönlendirme modu (`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr` yerel Wayland + HDR10'u (`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`, `sdlinput` hariç) korur, `steam://forceinputappid/<APPID>` ve `udevadm` yeniden bağlanma izleyicisini çalıştırır ve çıkışta `steam://forceinputappid/0` sıfırlar. Manuel: `steam-auto-run --reapply-input <APPID|0>`; udev: `./install.sh --with-steam-controller`.

---

İç tasarım ayrıntıları için [ARCHITECTURE.md](../../ARCHITECTURE.md), özgün İngilizce kaynak için [English User Guide](../../USER_GUIDE.md) ve tüm 27 yerelleştirilmiş kılavuz için [i18n Index](../README.md) sayfalarına bakın.
