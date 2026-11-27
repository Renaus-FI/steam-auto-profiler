# Steam Auto-Profiler 사용자 가이드

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

이 가이드는 **Steam Auto-Profiler v2.1**의 전체 설치, 일반 화면(flatscreen) 및 VR 실행 오케스트레이션, `steam-auto-ui` 제어 센터, 라이브러리 동기화, 벤치마킹 및 문제 해결 워크플로를 다룹니다.

Steam Auto-Profiler는 Steam AppID(또는 비-Steam 바로가기)를 검사하고, 드라이버/업스케일러/안티치트에 대한 엄격한 안전장치(guardrail)가 적용된 상황별 프로파일을 설정한 뒤 기존 게임 명령을 실행하는 가벼운 리눅스용 Bash/Python 런처이자 제어 센터입니다. 서드파티 Proton 런타임을 번들링하거나 주입하지 않습니다.

---

## 요구 사항

- 리눅스 데스크톱 세션(KDE Plasma 6 / Wayland, GNOME, wlroots 또는 X11), Bash 5+, Python 3.10+, Steam 및 표준 코어 유틸리티.
- 선택적 네이티브 제어 센터 GUI: `PyQt6` 또는 `PySide6` (미설치 시 의존성 없는 표준 라이브러리 `curses` TUI로 자동 폴백).
- 선택적 실행 전 체크리스트 대화 상자: `kdialog` 또는 `zenity`.
- 선택적 무음 프레임타임 벤치마킹: `mangohud`.
- 선택적 세션 네트워크 도우미: `tc`, `ip`, `ethtool` (`sudo`는 `--with-net-boost` 설치 시에만 필요).

---

## 설치 및 업데이트

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh`는 6개의 실행 파일(`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run`, `steam-auto-ui`)을 `~/.local/bin`에 복사하고, 데스크톱 항목(`~/.local/share/applications/steam-auto-profiler.desktop`)을 설치하며, `~/.config/steam-auto-profiler/profiles` 디렉터리를 생성하고 기본 vkBasalt 프리셋(`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`)을 추가합니다. `~/.local/bin`이 `PATH`에 포함되어 있는지 확인하세요.

설치 프로그램의 선택적 플래그는 조합하여 사용할 수 있습니다:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: `/usr/local/bin/steam-net-boost`(및 기타 스크립트의 시스템 사본)와 `steam-net-boost` 전용 최소 권한 무비밀번호 `sudoers` 규칙을 설치합니다.
- `--compat-cachy-run`: 기존 `/usr/local/bin/cachy-run`이 이미 Steam Auto-Profiler 심(shim)이 아닌 경우 `/usr/local/bin/cachy-run.bak`으로 보존하고, `steam-auto-run`으로 전달하는 심을 설치합니다.
- `--with-auto-sync` (`--enable-auto-sync`): 감지된 모든 Steam 라이브러리를 대상으로 systemd 사용자 감시기 `steam-auto-profiler-sync.path` 및 대응하는 oneshot 서비스를 설치하고 활성화합니다.
- `--uninstall`: 설치된 바이너리, 데스크톱 항목, 선택적 네트워크 도우미/sudoers 규칙, 호환성 심, 자동 동기화 systemd 사용자 유닛을 제거합니다.

기존 저장소를 업데이트하려면:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

게임을 동기화하기 전에 호스트 준비 상태를 확인하세요:

```bash
steam-auto-run --doctor
```

---

## 엔드투엔드 실행 파이프라인

1. **AppID 확인:** `SteamAppId`, `STEAM_COMPAT_APP_ID`, 그리고 `GAMEID`(Lutris/Heroic/UMU의 `umu-` 접두사 제거) 순서로 확인합니다.
2. **라이브러리 및 바로가기 검색:** `steam-auto-detect`는 Steam 루트와 `libraryfolders.vdf`의 보조 라이브러리를 검색하여 `appmanifest_<APPID>.acf`를 읽거나, 바이너리 `userdata/*/config/shortcuts.vdf`를 읽기 전용으로 폴백 조회한 뒤 최대 10단계 깊이의 단일 패스 `find`를 수행합니다(`screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization` 제외).
3. **5단계 분류 우선순위:**
   - **1. `competitive-anticheat`:** 알려진 경쟁 게임 AppID 또는 감지된 안티치트 런타임(EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE 등). OptiScaler, MLFG, vkBasalt 및 비동기 DXVK를 비활성화하고 저지연과 세션 네트워크 QoS를 활성화합니다.
   - **2. `vr`:** `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` 또는 바로가기의 `vr-run`/`-vr` 플래그 감지. `AUTO_IS_VR=1`을 내보냅니다.
   - **3. `native-fsr4` / `native-fsr`:** 모듈식 FidelityFX SDK 3.1+ (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). 드라이버 수준 FSR4 업그레이드를 활성화합니다(`PROTON_FSR4_UPGRADE=1` 또는 AMD RDNA 3에서는 `PROTON_FSR4_RDNA3_UPGRADE=1`).
   - **4. `legacy-upscaler`:** 레거시 DLSS(`nvngx_dlss*.dll`), XeSS(`libxess*.dll`), Streamline(`sl.interposer.dll`) 또는 FSR 2/3.0 DLL 감지. `AUTO_OPTISCALER=1`을 표시하고 `AUTO_UPSCALER_INFO` 안내를 설정합니다.
   - **5. `standard`:** 안전한 네이티브 Wine Wayland + 저지연 VRR 프로파일.
4. **VRR 주사율 상한(Cap):** 명시적인 `VRR_CAP=<fps>`가 항상 우선합니다(`VRR_CAP=0`은 상한 비활성화). 지정되지 않으면 `kscreen-doctor`(KDE Plasma 6 활성 `*` 모드 또는 구형 `Hz`), `wlr-randr` 또는 `xrandr`로 활성 디스플레이 주사율을 조회하여 기본 1:1로 적용합니다(240 Hz에서 `240 FPS`). 선택적 `-6%` VRR 안전 여유(`hz * 94 / 100`, 예: 240 Hz에서 `225 FPS`)를 원하면 `VRR_MINUS_MARGIN=1`을 활성화하세요. Gamescope 세션에서는 `VRR_CAP`이 명시되지 않는 한 DXVK/VKD3D 상한을 생략합니다.
5. **상호 배제 안전장치(Mutual-Exclusion Guardrails):**
   - **FSR 4 / OptiScaler + vkBasalt:** `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` 또는 `USE_OPTISCALER=1`이 활성화될 때마다 `ENABLE_VKBASALT=0`을 강제합니다(이중 선명화 및 HDR10 클리핑 방지).
   - **MLFG + 저지연 / VRR 상한:** `MLFG=1` (`USE_MLFG=1`)은 `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`을 내보내고 `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`를 해제하며 AMD RDNA 3에서 `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`를 내보냅니다. `USE_MLFG=0`이고 VRR 상한이 활성화되어 있으면 `DXVK_FRAME_PACE=low-latency-vrr`를 내보냅니다.
   - **모던 DX12 + Safe DX12:** `USE_SAFEDX12=0`일 때 AMD에서 `PROTON_NATIVE_AGS=1`과 `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`를 내보냅니다(`SAFEDX12=1`일 때는 깔끔하게 생략).
6. **Compat 토큰 매핑:** 관리 대상 기능은 기존 사용자 값을 덮어쓰지 않고 `PROTON_ADD_CONFIG`와 `STEAM_COMPAT_CONFIG` 양쪽에 추가됩니다: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **자동 KDE Plasma 6 HDR (`AUTO_HDR_SWITCH=1`):** Gamescope 외부에서 `DXVK_HDR=1`(또는 `USE_HDR=1`)과 함께 활성화되면 `kscreen-doctor -o`로 기본 활성 출력을 확인합니다. HDR이 꺼져 있으면 실행 전 켜고, 종료 시 `EXIT`/`INT`/`TERM` 트랩으로 SDR을 복원합니다.
8. **무음 프레임타임 벤치마킹 (`BENCH=1`):** MangoHud를 숨김 CSV 모드(`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`)로 실행하고 종료 시 프레임타임을 파싱하여 `Avg FPS`, `1% Low FPS`, `P99 (ms)`를 `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`에 기록한 뒤 임시 CSV를 삭제합니다.
9. **빠른 충돌 시 안전 모드(Safe Mode) 자동 복구:** 실험적 Wayland 또는 DX12 플래그가 활성화된 상태(`USE_XWAYLAND=0` 또는 `USE_SAFEDX12=0`)에서 Proton/Windows 게임이 `20s` 미만(`SAP_CRASH_THRESHOLD_SEC`로 조정 가능)에 0이 아닌 코드로 종료되면, `last-<APPID>.log` 및 `last-launch.log`에 `crash_hint`를 기록하고(GUI 활성 시) 다음 실행을 위해 `USE_XWAYLAND=1` + `USE_SAFEDX12=1` 저장을 제안합니다.
10. **스케줄러 및 네트워크 수명 주기:** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun`(`ananicy-cpp.service`가 비활성일 때만) -> 직접 실행 순으로 실행하며 선택적으로 `PRIME=1` (`prime-run`)을 지원합니다. `USE_NET_OPT=1`이면 `steam-net-boost`가 정적 root CAKE 및 HTB + leaf CAKE 계층을 유지하면서 `flock` 기반 참조 카운트 `on`/`off`를 수행합니다.

---

## 통합 제어 센터 (`steam-auto-ui`)

데스크톱 앱 메뉴, `steam-auto-run --ui` 또는 터미널에서 직접 `steam-auto-ui`를 실행하세요:

```bash
steam-auto-ui                 # Qt6 GUI (PyQt6/PySide6) 또는 curses TUI 자동 감지
steam-auto-ui --gui           # 네이티브 Qt6 GUI 창 강제 실행
steam-auto-ui --tui           # 표준 라이브러리 curses TUI 강제 실행 (SSH에서 동작)
steam-auto-ui --lang fi       # 명시적 UI 언어로 실행 (27개 언어 지원)
steam-auto-ui --check         # 헤드리스 자가 점검 실행 (JSON 진단 출력)
```

`steam-auto-ui`는 `LC_ALL` / `LC_MESSAGES` / `LANG`에서 시스템 로케일을 자동 감지하며, Qt6 GUI의 실시간 언어 선택 드롭다운(`curses` TUI에서는 `L` 단축키)을 통해 재시작 없이 27개 모든 언어 간에 즉시 전환할 수 있습니다.

### 5개의 동기화된 보기

1. **게임 및 프로파일:** Steam 타이틀 및 읽기 전용 비-Steam `shortcuts.vdf` 항목의 필터링 가능한 테이블(`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), 업스케일러 SDK 배지(`AUTO_UPSCALER_INFO`), 10개 프로파일 토글 + `VRR_CAP` 전체에 대한 실시간 상호 배제 검증, `Dry-Run Preview`, `Benchmarks` 바로가기 버튼 및 `Reset Profile`.
2. **시스템 및 텔레메트리:** `steam-auto-run --doctor` 논블로킹 실시간 출력, `scxctl get` / `sched_ext` 상태, 설치된 스택 버전(`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), 셰이더 캐시 사용량(`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), `/var/log/pacman.log` git/AUR 다운그레이드 경고, GPU VRAM/사용률/온도, `tc -s qdisc` LAN(`10:`) 대 WAN(`20:`/root) 처리량 및 `av_delay`, `vr-mode status`.
3. **라이브러리 동기화:** 실시간 Steam 실행 상태 보호 배너와 `--report`, `--sanitize --dry-run`, `--sanitize`(Steam 실행 중 차단), `--migrate-cachy-run` 원클릭 실행.
4. **로그 및 복구:** `last-launch.log` 및 `last-<APPID>.log` 탐색, `crash_hint` 경고 확인, 원클릭 안전 모드 적용(`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **벤치마크:** `BENCH=1` 프레임타임 측정 결과의 필터링 가능한 나란히 비교 테이블(`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## VR 오케스트레이션 (`vr-run`)

VR 타이틀의 Steam **속성 > 일반 > 시작 옵션**을 다음으로 설정하세요:

```text
vr-run %command%
```

- 상속된 평면 화면용 오버라이드(`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`)를 제거합니다.
- `MESA_VK_DEVICE_SELECT`로 VRAM이 가장 큰 외장 GPU를 자동 선택하며 AMD GPU에서는 `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`을 설정합니다.
- WiVRn 및 xrizer OpenXR/OpenVR 경로(`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`)를 동적으로 탐색하고, 명시적인 사용자 설정을 덮어쓰지 않고 `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW`, `LD_LIBRARY_PATH`를 구성합니다.
- `vr-mode`가 설치된 경우 `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions`에서(`flock` 사용) `vr-mode on` / `vr-mode off`를 참조 카운트 관리합니다(`VR_AUTO_MODE=0`으로 비활성화).
- 동일한 `ananicy-cpp` 인식 스케줄러 체인(`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> 직접 `exec`)을 통해 실행합니다.
- 언제든 `vr-run --dry-run`으로 해석된 환경 변수를 미리 확인할 수 있습니다.

`steam-auto-run`은 SteamVR(`250820`) 및 `-vr`/`--vr` 실행을 자동으로 우회하며, `steam-auto-sync`는 VR 타이틀에 `vr-run %command%`를 자동 할당하고 유지합니다.

---

## Steam 라이브러리 동기화 (`steam-auto-sync`)

`localconfig.vdf`에 기록하기 전에 Steam을 완전히 종료하세요:

```bash
steam-auto-sync --report              # 라이브러리 + shortcuts.vdf 읽기 전용 감사
steam-auto-sync --print-library-paths # 감지된 모든 Steam 라이브러리 경로 표시
steam-auto-sync --dry-run             # 변경 사항 미리 보기
steam-auto-sync                       # steam-auto-run / vr-run 주입
steam-auto-sync --sanitize --dry-run  # 구형 플래그 정리 미리 보기
steam-auto-sync --sanitize            # 지저분한/고아 플래그 정리 (별칭: --clean)
steam-auto-sync --migrate-cachy-run   # 구형 cachy-run 프로파일 마이그레이션
steam-auto-sync --remove              # steam-auto-run 래퍼 제거
```

- 타임스탬프 백업 `localconfig.vdf.bak.*`는 `--keep-backups N`으로 자동 정리됩니다(기본값 `10`, `0`은 모두 유지).
- 특정 AppID를 제외하려면 `~/.config/steam-auto-profiler/ignore_appids.txt`에 한 줄씩 나열하세요(`#` 주석 허용).
- systemd 자동 동기화 감시기(`./install.sh --with-auto-sync` 또는 `steam-auto-sync --install-systemd`)는 Steam 매니페스트 변경 시 `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`을 실행합니다.

---

## CLI 및 프로파일 레퍼런스

### 명령어

| 용도 | 명령어 |
| --- | --- |
| 시스템 준비 상태 감사 | `steam-auto-run --doctor` (별칭 `--check-system`) |
| 제어 센터 실행 (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` 또는 `steam-auto-run --ui` |
| 게임 검사 (사람이 읽기 쉬운 형식) | `steam-auto-run --inspect APPID` |
| 게임 검사 (JSON) | `steam-auto-detect --inspect --json APPID` |
| 프로파일 대화형 재구성 | `steam-auto-run --configure APPID` |
| 해석된 실행 환경 미리 보기 | `steam-auto-run --dry-run APPID` |
| 저장된 프로파일 초기화 | `steam-auto-run --reset APPID` |
| 저장된 프로파일 목록 표시 | `steam-auto-run --list-profiles` |
| 최근 실행 로그 보기 | `steam-auto-run --last-log [APPID]` |
| VR 실행 환경 미리 보기 | `vr-run --dry-run` |
| 네트워크 도우미 확인 (읽기 전용) | `steam-net-boost status [IFACE]` |

### 저장된 `.env` 프로파일 키 및 환경 변수 오버라이드

프로파일 파일은 `~/.config/steam-auto-profiler/profiles/<APPID>.env`에 위치하며 허용 목록 기반 `KEY=VALUE` 형식만 수락합니다(셸 명령 치환 및 알 수 없는 키는 안전하게 무시됩니다):

| `.env` 키 | 환경 변수 오버라이드 | 효과 |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | 네이티브 Wine Wayland 대신 XWayland 강제 |
| `USE_FSR4=0` | `FSR4=0` | 드라이버 수준 FSR 4 업그레이드 비활성화 (기본값 `1`) |
| `USE_MLFG=1` | `MLFG=1` | 프레임 생성 활성화 (Anti-Lag, 저지연 및 VRR 프레임 상한 비활성화) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | OptiScaler 브리지 활성화 (`competitive-anticheat`에서는 자동 차단) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | vkBasalt 선명화 활성화 (FSR 4 또는 OptiScaler 활성 시 비활성화) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | 실험적 `VKD3D_CONFIG` 플래그와 `vkd3dbindlesstb` 토큰 생략 |
| `USE_NET_OPT=1` | `NETOPT=1` | `steam-net-boost`를 통한 세션 네트워크 QoS 활성화 |
| `USE_SDL=1` | `SDL=1` | 네이티브 SDL / Steam Input 에뮬레이션 선호 |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Steam 오버레이 `LD_PRELOAD` 유지 |
| `USE_CEF_FIX=1` | `CEF=1` | CEF 런처용 `--in-process-gpu` 추가 |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | 레거시 타이틀용 NTSync 비활성화 |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | 창 관리자 장식 비활성화 |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | 사용자 지정 DXVK/VKD3D 프레임 상한 (`0`은 상한 비활성화) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | 모니터 주사율 대비 `-6%` 여유 적용 (예: 240 Hz에서 `225 FPS`) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Wine Wayland에서 단축키 억제 허용 (기본값 `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | 실행 시 KDE Plasma 6 HDR 자동 활성화 및 종료 시 SDR 복원 |
| — | `BENCH=1`, `BENCH_DURATION=60` | 무음 MangoHud CSV 벤치마크 실행 및 JSON 요약 저장 |
| — | `NO_GUI=1` / `FORCE_GUI=1` | 실행 전 `kdialog`/`zenity` 체크리스트 숨기기 또는 강제 표시 |
| — | `FSR_HUD=1` | FSR/DLSS/MLFG HUD 표시 변수 내보내기 |
| — | `VULKAN=1` / `PRIME=1` | `-vulkan` 추가 / `prime-run`으로 래핑 |
| — | `GAMEID=umu-<appid>` | UMU / Lutris / Heroic AppID 확인 |

---

## Lutris, Heroic, Faugus 및 UMU

- **Lutris:** 고급 옵션을 켜고 `proton-cachyos-slr`(또는 사용 중인 Proton 빌드)를 선택한 뒤 Lutris 런타임을 끄고 시스템 라이브러리를 우선 사용하도록 설정하며 명령 접두사를 `steam-auto-run`으로 지정하세요.
- **Heroic / Faugus:** `proton-cachyos-slr`를 선택하고 래퍼/명령 접두사로 `steam-auto-run`을 추가하세요.
- **UMU / Protonfixes:** 필요 시 `PROTON_VERB=waitforexitandrun` 및 `GAMEID=umu-<appid>`를 내보내세요.

---

## 문제 해결

- **Wayland 또는 DX12에서 빠른 충돌 발생:** `steam-auto-ui`의 **로그 및 복구**를 열거나(`steam-auto-run --last-log APPID` 실행) 안전 모드(`USE_XWAYLAND=1`, `USE_SAFEDX12=1`)를 적용하거나 `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`로 실행하세요.
- **안티치트 타이틀 실행 실패:** `proton-cachyos-slr`(Steam Linux Runtime)를 사용하고 `steam-auto-run --doctor`로 EAC v2, `/dev/ntsync`, `vm.max_map_count`를 점검하세요.
- **Steam이 시작 옵션을 되돌림:** `steam-auto-sync` 또는 `steam-auto-sync --sanitize`를 실행하기 전에 Steam을 완전히 종료하세요.
- **잘못되었거나 누락된 VRR 상한:** `VRR_CAP=<fps>`를 명시적으로 지정하거나 `VRR_CAP=0`으로 비활성화하고, `-6%` 여유가 필요하면 `VRR_MINUS_MARGIN=1`을 설정하세요. Gamescope에서는 명시적 `VRR_CAP`만 DXVK/VKD3D 상한을 내보냅니다.
- **네트워크 QoS 점검:** `steam-net-boost status`(비권한 읽기 전용)를 실행하세요. 자동 세션 QoS를 원하면 `./install.sh --with-net-boost`로 root 도우미를 설치하세요.

---

## v2.1 새로운 기능 (Mesa 27.0 / RDNA 4, Ultra Bleeding-Edge, Hunt 594650, Steam Controller 2026)

- **Mesa 27.0 / RDNA 4 플래그:** `TRANSFER_QUEUE=1`(RDNA 3/4 중복 제거 `RADV_PERFTEST=sam,transfer_queue`), `NATIVE_ANTILAG=1`(네이티브 `VK_AMD_anti_lag`), `REFLEX_LAYER=1`(`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`, 안티치트/MLFG 차단), `VK_VIDEO_DECODE=1`(`RADV_EXPERIMENTAL=video_decode`).
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** 비안티치트 타이틀용 실험 스택(`VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`, `VKD3D_FEATURE_LEVEL=12_2`, `VKD3D_SHADER_MODEL=6_8`, `PROTON_FSR4_UPGRADE=1`, `PROTON_NATIVE_AGS=1`, `PROTON_USE_WOW64=1`, `PROTON_MEDIA_FORCE_GST=1`, Gamescope 외 네이티브 Wayland 전용 `WAYLANDDRV_RAWINPUT=1`).
- **Hunt: Showdown 1896 (`AppID 594650`) 호환성 가드:** `competitive-anticheat`, `USE_XWAYLAND=1`, `USE_SAFEDX12=1`, `PROTON_NATIVE_AGS=0`, `LOW_LATENCY_LAYER=0`, `USE_MLFG=0`, `USE_BLEEDING_EDGE=0`, `USE_NET_OPT=1`을 강제하며 `--doctor`와 `steam-auto-ui`에서 `config.vdf`(`Proton 11.0-2` / `Proton Hotfix`)를 점검합니다.
- **Steam Controller 2026 / Wireless Steam Puck (`28de:{1302,1304,1005,1007}`):** 4가지 모드(`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`): `wayland-hdr`는 네이티브 Wayland + HDR10(`PROTON_ENABLE_WAYLAND=1`, `DXVK_HDR=1`, `PROTON_USE_SDL=0`, `PROTON_NO_STEAMINPUT=0`, `sdlinput` 제외)을 유지하고 `steam://forceinputappid/<APPID>` 및 `udevadm` 재연결 감시자를 실행하며 종료 시 `steam://forceinputappid/0`으로 복원합니다. 수동 재적용: `steam-auto-run --reapply-input <APPID|0>`; udev 규칙: `./install.sh --with-steam-controller`.

---

내부 설계는 [ARCHITECTURE.md](../../ARCHITECTURE.md), 공식 영문 가이드는 [English User Guide](../../USER_GUIDE.md), 27개 언어 가이드 목록은 [i18n Index](../README.md)를 참고하세요.
