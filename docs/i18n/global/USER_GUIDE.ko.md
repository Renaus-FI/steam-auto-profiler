# Steam Auto-Profiler 사용자 안내서

이 문서는 설치와 일상적인 사용 흐름을 요약합니다. 자세한 기술 설명은 [영문 안내서](../../USER_GUIDE.md)를 참고하세요.

## 설치

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost`는 선택형 네트워크 QoS 도우미를 설치합니다. `--compat-cachy-run`은 기존 `/usr/local/bin/cachy-run`을 `.bak`으로 보존하고 호환 shim을 설치합니다. `--with-auto-sync`는 systemd 사용자 watcher를 설치합니다. `--uninstall`은 설치 항목을 제거합니다.

## 동작 방식

`steam-auto-detect`는 Steam 라이브러리와 매니페스트에서 AppID를 찾고 게임 폴더를 최대 10단계까지 검사한 뒤 우선순위대로 분류합니다: (1) `competitive-anticheat`, (2) 네이티브 FSR/FidelityFX (`native-fsr4`/`native-fsr`), (3) `legacy-upscaler`, (4) `standard`.

`steam-auto-run`은 `SteamAppId`, `STEAM_COMPAT_APP_ID`, `GAMEID` 순으로 AppID를 해석하고 `umu-` 접두사를 제거합니다. `kdialog` 또는 `zenity`로 설정창을 표시하고 선택 항목을 `~/.config/steam-auto-profiler/profiles/<APPID>.env`에 저장합니다. 형식은 `KEY=VALUE`이며 알 수 없는 키와 셸 문법은 무시됩니다.

호환 설정은 기존 값을 보존하면서 `PROTON_ADD_CONFIG`와 `STEAM_COMPAT_CONFIG`에 추가됩니다. 주요 토큰은 `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire`, `vkreflex`입니다.

## Steam 자동화

Steam 실행 옵션:

```text
steam-auto-run %command%
```

UMU: `GAMEID=umu-2357570 steam-auto-run %command%`.

`localconfig.vdf`를 수정하기 전에 Steam을 완전히 종료하세요.

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean`은 `--sanitize` 별칭이고, `--remove`는 wrapper를 제거하며, `--print-library-paths`는 라이브러리를 표시하고, `--keep-backups N`은 백업 개수입니다(`0`은 모두 보존).

watcher는 `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`을 실행합니다. `steam-auto-sync --install-systemd`로 unit를 설치할 수 있습니다.

## 명령과 환경 변수

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles`, `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

주요 변수: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1`, `NO_NTSYNC=1`.

`VRR_CAP`이 우선합니다. 지정하지 않으면 `kscreen-doctor`, `wlr-randr`, `xrandr`로 주사율을 확인하고 60 Hz 초과 시 94% 상한을 사용합니다. Gamescope에서는 `VRR_CAP`이 없으면 DXVK/VKD3D 프레임 제한을 추가하지 않습니다.

## 네트워크 및 문제 해결

`NETOPT=1` 또는 `netopt`를 선택하면 `steam-net-boost`가 CAKE 또는 `fq_codel`을 적용하고, 세션 중 EEE와 tx queue length를 조정합니다. 마지막 세션 종료 시 원래 상태로 복원합니다.

상태 확인: `sudo steam-net-boost status [IFACE]`. 동기화 전 Steam을 완전히 종료하세요. 잘못된 프로필은 `FORCE_GUI=1` 또는 `--reset APPID`로 다시 설정합니다. 안티치트 게임은 `proton-cachyos-slr`을 우선하고 `--doctor`로 점검하세요.
