# Steam Auto-Profiler ユーザーガイド

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

このガイドでは、**Steam Auto-Profiler v2.1** の完全なインストール手順、フラットスクリーンおよび VR の起動オーケストレーション、`steam-auto-ui` コントロールセンター、ライブラリ同期、ベンチマーク、トラブルシューティングについて解説します。

Steam Auto-Profiler は Linux 向けの軽量な Bash/Python 製ランチャー兼コントロールセンターです。Steam AppID（または非 Steam ショートカット）を解析し、ドライバー・アップスケーラー・アンチチートに対する厳格なガードレールを備えたコンテキスト対応プロファイルを適用したうえで、既存のゲームコマンドを起動します。サードパーティ製 Proton ランタイムを同梱・注入することはありません。

---

## 動作要件

- Linux デスクトップセッション（KDE Plasma 6 / Wayland、GNOME、wlroots、または X11）、Bash 5+、Python 3.10+、Steam、および標準コアユーティリティ。
- コントロールセンター用ネイティブ GUI（任意）：`PyQt6` または `PySide6`（未導入時は依存関係ゼロの標準ライブラリ `curses` TUI に自動フォールバック）。
- 起動前チェックリストダイアログ（任意）：`kdialog` または `zenity`。
- サイレント・フレームタイムベンチマーク（任意）：`mangohud`。
- セッションネットワークヘルパー（任意）：`tc`、`ip`、`ethtool`（`sudo` は `--with-net-boost` のインストール時のみ必要）。

---

## インストールとアップデート

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` は 6 つの実行ファイル（`steam-auto-run`、`steam-auto-detect`、`steam-auto-sync`、`steam-net-boost`、`vr-run`、`steam-auto-ui`）を `~/.local/bin` にコピーし、デスクトップエントリ（`~/.local/share/applications/steam-auto-profiler.desktop`）をインストールし、`~/.config/steam-auto-profiler/profiles` を作成し、デフォルトの vkBasalt プリセット（`competitive`、`standard`、`vivid`、`shooter`、`oled-clean`）を追加します。`~/.local/bin` が `PATH` に含まれていることを確認してください。

インストーラーのオプションフラグは組み合わせ可能です：

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`：`/usr/local/bin/steam-net-boost`（および他スクリプトのシステムコピー）と、`steam-net-boost` 専用の最小権限パスワードなし `sudoers` ルールをインストールします。
- `--compat-cachy-run`：既存の `/usr/local/bin/cachy-run`（すでに Steam Auto-Profiler のシムである場合を除く）を `/usr/local/bin/cachy-run.bak` として退避し、`steam-auto-run` への転送シムをインストールします。
- `--with-auto-sync`（`--enable-auto-sync`）：検出されたすべての Steam ライブラリを監視する systemd ユーザーウォッチャー `steam-auto-profiler-sync.path` と対応する oneshot サービスをインストール・有効化します。
- `--uninstall`：インストール済みのバイナリ、デスクトップエントリ、任意のネットワークヘルパー/sudoers ルール、互換シム、自動同期用 systemd ユーザーユニットを削除します。

既存のチェックアウトを更新するには：

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

ゲームを同期する前にホストの準備状態を確認します：

```bash
steam-auto-run --doctor
```

---

## エンドツーエンド起動パイプライン

1. **AppID 解決：** `SteamAppId`、`STEAM_COMPAT_APP_ID`、次に `GAMEID`（Lutris/Heroic/UMU 向けの `umu-` プレフィックスを除去）を確認します。
2. **ライブラリおよびショートカット検出：** `steam-auto-detect` は Steam ルートと `libraryfolders.vdf` 内のセカンダリライブラリを検索し、`appmanifest_<APPID>.acf` を読み取るか、バイナリ形式の `userdata/*/config/shortcuts.vdf` に読み取り専用でフォールバックしたのち、最大 10 階層までの単一パス `find` を実行します（`screenshots`、`saves`、`logs`、`shadercache`、`workshop`、`movies`、`videos`、`localization` は除外）。
3. **5 段階の分類優先順位：**
   - **1. `competitive-anticheat`：** 既知の競技向け AppID、またはアンチチートランタイム（EAC、BattlEye、Ricochet、ACE、GameGuard、XIGNCODE など）を検出。OptiScaler、MLFG、vkBasalt、非同期 DXVK を無効化し、低遅延とセッションネットワーク QoS を有効化します。
   - **2. `vr`：** `openvr_api.dll`/`openvr_api.so`、`openxr_loader.dll`/`libopenxr_loader.so*`、`*.vrmanifest`、またはショートカットの `vr-run`/`-vr` フラグを検出。`AUTO_IS_VR=1` をエクスポートします。
   - **3. `native-fsr4` / `native-fsr`：** モジュール型 FidelityFX SDK 3.1+（`amd_fidelityfx_upscaler_*.dll`、`amd_fidelityfx_framegeneration_dx12.dll`、`amdxcffx64.dll`）。ドライバーレベルの FSR4 アップグレードを有効化します（`PROTON_FSR4_UPGRADE=1`、AMD RDNA 3 では `PROTON_FSR4_RDNA3_UPGRADE=1`）。
   - **4. `legacy-upscaler`：** レガシー DLSS（`nvngx_dlss*.dll`）、XeSS（`libxess*.dll`）、Streamline（`sl.interposer.dll`）、または FSR 2/3.0 の DLL を検出。`AUTO_OPTISCALER=1` をマークし、`AUTO_UPSCALER_INFO` にガイダンスを設定します。
   - **5. `standard`：** 安全なネイティブ Wine Wayland + 低遅延 VRR プロファイル。
4. **VRR リフレッシュレート上限：** 明示的な `VRR_CAP=<fps>` が常に優先されます（`VRR_CAP=0` で上限無効）。未指定時は `kscreen-doctor`（KDE Plasma 6 のアクティブ `*` モードまたは従来の `Hz`）、`wlr-randr`、または `xrandr` でアクティブな表示リフレッシュレートを取得し、デフォルトで 1:1 適用します（240 Hz なら `240 FPS`）。任意の `-6%` VRR 安全マージン（`hz * 94 / 100`、例：240 Hz で `225 FPS`）を使うには `VRR_MINUS_MARGIN=1` を有効にします。Gamescope セッションでは、`VRR_CAP` を明示しない限り DXVK/VKD3D の上限は省略されます。
5. **相互排他ガードレール：**
   - **FSR 4 / OptiScaler + vkBasalt：** `PROTON_FSR4_UPGRADE=1`、`PROTON_FSR4_RDNA3_UPGRADE=1`、または `USE_OPTISCALER=1` が有効な場合は常に `ENABLE_VKBASALT=0` を強制します（二重シャープニングと HDR10 クリッピングを防止）。
   - **MLFG + 低遅延 / VRR 上限：** `MLFG=1`（`USE_MLFG=1`）は `ENABLE_LAYER_MESA_ANTI_LAG=0`、`PROTON_DXVK_LOWLATENCY=0`、`PROTON_VKD3D_LOWLATENCY=0` をエクスポートし、`DXVK_FRAME_RATE`、`VKD3D_FRAME_RATE`、`DXVK_FRAME_PACE` を解除し、AMD RDNA 3 では `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` をエクスポートします。`USE_MLFG=0` かつ VRR 上限が有効な場合は `DXVK_FRAME_PACE=low-latency-vrr` をエクスポートします。
   - **モダン DX12 + Safe DX12：** `USE_SAFEDX12=0` のとき AMD で `PROTON_NATIVE_AGS=1` および `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` をエクスポートします（`SAFEDX12=1` ではきれいに省略）。
6. **Compat トークンのマッピング：** 管理対象機能は既存のユーザー設定を上書きせず、`PROTON_ADD_CONFIG` と `STEAM_COMPAT_CONFIG` の両方に追記されます：`wayland`、`sdlinput`、`nativeags`、`noopwr`、`vkd3dbindlesstb`、`dxvklowlatency`、`vkd3dlowlatency`、`localshadercache`、`pipewire`、`fsr4`、`mlfg`、`vkreflex`、`nontsync`、`nowmdecoration`。
7. **KDE Plasma 6 自動 HDR（`AUTO_HDR_SWITCH=1`）：** Gamescope 外で `DXVK_HDR=1`（または `USE_HDR=1`）とともに有効化すると、`kscreen-doctor -o` でプライマリ有効出力を調べます。HDR がオフなら起動前にオンへ切り替え、`EXIT`/`INT`/`TERM` トラップで終了時に SDR へ復元します。
8. **サイレント・フレームタイムベンチマーク（`BENCH=1`）：** MangoHud を非表示 CSV モード（`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`）で実行し、終了時にフレームタイムを解析して `Avg FPS`、`1% Low FPS`、`P99 (ms)` を `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` に追記し、一時 CSV を削除します。
9. **高速クラッシュ時のセーフモード自動復旧：** 実験的な Wayland または DX12 フラグが有効な状態（`USE_XWAYLAND=0` または `USE_SAFEDX12=0`）で Proton/Windows タイトルが `20s` 未満（`SAP_CRASH_THRESHOLD_SEC` で変更可能）に非ゼロ終了した場合、`last-<APPID>.log` と `last-launch.log` に `crash_hint` を記録し、GUI が有効な場合は次回起動用に `USE_XWAYLAND=1` + `USE_SAFEDX12=1` を保存するか確認します。
10. **スケジューラーとネットワークのライフサイクル：** `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun`（`ananicy-cpp.service` が非アクティブな場合のみ）-> 直接実行の順で起動し、任意で `PRIME=1`（`prime-run`）にも対応します。`USE_NET_OPT=1` の場合、`steam-net-boost` は静的 root CAKE および HTB + leaf CAKE 階層を保持しながら、`flock` 付き参照カウント方式で `on`/`off` を実行します。

---

## 統合コントロールセンター（`steam-auto-ui`）

デスクトップのアプリケーションメニュー、`steam-auto-run --ui`、またはコマンドラインから `steam-auto-ui` を起動します：

```bash
steam-auto-ui                 # Qt6 GUI (PyQt6/PySide6) または curses TUI を自動検出
steam-auto-ui --gui           # ネイティブ Qt6 GUI ウィンドウを強制起動
steam-auto-ui --tui           # 標準ライブラリ curses TUI を強制起動（SSH 経由でも動作）
steam-auto-ui --lang fi       # UI 言語を明示指定して起動（27 言語対応）
steam-auto-ui --check         # ヘッドレス自己診断を実行（JSON 診断情報を出力）
```

`steam-auto-ui` は `LC_ALL` / `LC_MESSAGES` / `LANG` からシステムロケールを自動検出し、Qt6 GUI のライブ言語ドロップダウン（`curses` TUI では `L` ホットキー）から再起動なしで 27 言語すべてをリアルタイムに切り替えられます。

### 5 つの同期ビュー

1. **ゲームとプロファイル：** Steam タイトルおよび読み取り専用非 Steam `shortcuts.vdf` エントリのフィルター可能な一覧（`AppID`、`Game Name`、`Source`、`Auto Class`、`Synced`、`Profile`）、アップスケーラー SDK バッジ（`AUTO_UPSCALER_INFO`）、全 10 個のプロファイルトグル + `VRR_CAP` に対するリアルタイム相互排他検証、`Dry-Run Preview`、`Benchmarks` へのジャンプボタン、`Reset Profile`。
2. **システムとテレメトリ：** `steam-auto-run --doctor` のノンブロッキングライブ表示、`scxctl get` / `sched_ext` 状態、インストール済みスタックバージョン（`mesa-git`/`mesa`、`proton-cachyos-slr`、`wivrn-server`、`xrizer-git`/`xrizer`、`mangohud`）、シェーダーキャッシュ使用量（`~/.cache/mesa_shader_cache*`、`radv_builtin_shaders*`）、`/var/log/pacman.log` の git/AUR ダウングレード警告、GPU VRAM・使用率・温度、`tc -s qdisc` の LAN（`10:`）対 WAN（`20:`/root）スループットおよび `av_delay`、`vr-mode status`。
3. **ライブラリ同期：** Steam の稼働状態を監視するライブ保護バナーと、`--report`、`--sanitize --dry-run`、`--sanitize`（Steam 稼働中はブロック）、`--migrate-cachy-run` のワンクリック操作。
4. **ログと復旧：** `last-launch.log` および `last-<APPID>.log` の閲覧、`crash_hint` 警告の確認、ワンクリックでのセーフモード適用（`USE_XWAYLAND=1`、`USE_SAFEDX12=1`）。
5. **ベンチマーク：** `BENCH=1` フレームタイム計測結果のフィルター可能な並列比較表（`Avg FPS`、`1% Low FPS`、`P99 (ms)`、`Samples`、`FSR4`、`MLFG`、`XWayland`、`SafeDX12`、`VRR Cap`）。

---

## VR オーケストレーション（`vr-run`）

VR タイトルの Steam **プロパティ > 一般 > 起動オプション** に以下を設定します：

```text
vr-run %command%
```

- 引き継がれたフラットスクリーン向け上書き設定を除去します（`DXVK_FRAME_RATE`、`VKD3D_FRAME_RATE`、`DXVK_FRAME_PACE`、`PROTON_ENABLE_WAYLAND`、`PROTON_USE_WAYLAND`、`ENABLE_LAYER_MESA_ANTI_LAG`、`ENABLE_VKBASALT`、`PROTON_MLFG_UPGRADE`、`MLFG_UPGRADE`）。
- `MESA_VK_DEVICE_SELECT` により最大 VRAM の専用 GPU を自動選択し、AMD GPU では `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` を設定します。
- WiVRn および xrizer の OpenXR/OpenVR パス（`~/.local/share/wivrn-slr/openxr_wivrn.json`、`/usr/share/openxr/1/openxr_wivrn.json`、`/opt/xrizer`、`~/.local/share/xrizer`、`~/.config/openvr`、`$XDG_RUNTIME_DIR/wivrn`）を動的に検出し、明示的なユーザー上書きを壊さずに `XR_RUNTIME_JSON`、`VR_OVERRIDE`、`PRESSURE_VESSEL_FILESYSTEMS_RO`、`PRESSURE_VESSEL_FILESYSTEMS_RW`、`LD_LIBRARY_PATH` を構成します。
- `vr-mode` がインストールされている場合、`${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` で（`flock` を用いて）`vr-mode on` / `vr-mode off` を参照カウント管理します（`VR_AUTO_MODE=0` で無効化）。
- `ananicy-cpp` 対応の同一スケジューラーチェーン（`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> 直接 `exec`）で起動します。
- 解決後の環境変数はいつでも `vr-run --dry-run` で確認できます。

`steam-auto-run` は SteamVR（`250820`）および `-vr`/`--vr` 起動を自動的にバイパスし、`steam-auto-sync` は VR タイトルへ自動的に `vr-run %command%` を割り当てて保持します。

---

## Steam ライブラリ同期（`steam-auto-sync`）

`localconfig.vdf` へ書き込む前に Steam を完全に終了してください：

```bash
steam-auto-sync --report              # ライブラリ + shortcuts.vdf の読み取り専用監査
steam-auto-sync --print-library-paths # 検出されたすべての Steam ライブラリを表示
steam-auto-sync --dry-run             # 編集内容をプレビュー
steam-auto-sync                       # steam-auto-run / vr-run を注入
steam-auto-sync --sanitize --dry-run  # レガシーフラグ整理のプレビュー
steam-auto-sync --sanitize            # 煩雑・孤立フラグを整理（エイリアス：--clean）
steam-auto-sync --migrate-cachy-run   # 旧 cachy-run プロファイルを移行
steam-auto-sync --remove              # steam-auto-run ラッパーを削除
```

- タイムスタンプ付きバックアップ `localconfig.vdf.bak.*` は `--keep-backups N` で自動整理されます（デフォルト `10`、`0` ですべて保持）。
- 特定の AppID を除外するには、`~/.config/steam-auto-profiler/ignore_appids.txt` に 1 行 1 件で記載します（`#` コメント可）。
- systemd 自動同期ウォッチャー（`./install.sh --with-auto-sync` または `steam-auto-sync --install-systemd`）は、Steam マニフェスト変更時に `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` を実行します。

---

## CLI およびプロファイルリファレンス

### コマンド一覧

| 用途 | コマンド |
| --- | --- |
| システム準備状態の監査 | `steam-auto-run --doctor`（エイリアス `--check-system`） |
| コントロールセンター起動（GUI/TUI） | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` または `steam-auto-run --ui` |
| ゲームの解析（人間向け表示） | `steam-auto-run --inspect APPID` |
| ゲームの解析（JSON） | `steam-auto-detect --inspect --json APPID` |
| プロファイルの対話的再設定 | `steam-auto-run --configure APPID` |
| 解決済み起動環境のプレビュー | `steam-auto-run --dry-run APPID` |
| 保存済みプロファイルのリセット | `steam-auto-run --reset APPID` |
| 保存済みプロファイルの一覧表示 | `steam-auto-run --list-profiles` |
| 最新の起動ログを表示 | `steam-auto-run --last-log [APPID]` |
| VR 起動環境のプレビュー | `vr-run --dry-run` |
| ネットワークヘルパー確認（読み取り専用） | `steam-net-boost status [IFACE]` |

### 保存済み `.env` プロファイルキーと環境変数上書き

プロファイルファイルは `~/.config/steam-auto-profiler/profiles/<APPID>.env` に保存され、許可リスト方式の `KEY=VALUE` 形式のみを受け付けます（シェルコマンド置換や未知のキーは安全に無視されます）：

| `.env` キー | 環境変数上書き | 効果 |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | ネイティブ Wine Wayland ではなく XWayland を強制 |
| `USE_FSR4=0` | `FSR4=0` | ドライバーレベルの FSR 4 アップグレードを無効化（デフォルト `1`） |
| `USE_MLFG=1` | `MLFG=1` | フレーム生成を有効化（Anti-Lag、低遅延、VRR フレーム上限を無効化） |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | OptiScaler ブリッジを有効化（`competitive-anticheat` では強制無効） |
| `USE_SHARPEN=1` | `SHARPEN=1`（`RCAS=1`） | vkBasalt シャープニングを有効化（FSR 4 または OptiScaler 有効時は無効） |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | 実験的な `VKD3D_CONFIG` フラグと `vkd3dbindlesstb` トークンを省略 |
| `USE_NET_OPT=1` | `NETOPT=1` | `steam-net-boost` によるセッションネットワーク QoS を有効化 |
| `USE_SDL=1` | `SDL=1` | ネイティブ SDL / Steam Input エミュレーションを優先 |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Steam オーバーレイの `LD_PRELOAD` を保持 |
| `USE_CEF_FIX=1` | `CEF=1` | CEF ランチャー向けに `--in-process-gpu` を追加 |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | レガシータイトル向けに NTSync を無効化 |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | ウィンドウマネージャーの装飾を無効化 |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | カスタム DXVK/VKD3D フレーム上限（`0` で上限無効） |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | モニターリフレッシュレートに `-6%` の余裕を適用（例：240 Hz で `225 FPS`） |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Wine Wayland 下でのショートカット抑止を許可（デフォルト `0`） |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | 起動時に KDE Plasma 6 HDR を自動有効化し、終了時に SDR へ復元 |
| — | `BENCH=1`, `BENCH_DURATION=60` | サイレント MangoHud CSV ベンチマークを実行し JSON サマリーを保存 |
| — | `NO_GUI=1` / `FORCE_GUI=1` | 起動前の `kdialog`/`zenity` チェックリストを非表示または強制表示 |
| — | `FSR_HUD=1` | FSR/DLSS/MLFG の HUD インジケーター変数をエクスポート |
| — | `VULKAN=1` / `PRIME=1` | `-vulkan` を追加 / `prime-run` でラップ |
| — | `GAMEID=umu-<appid>` | UMU / Lutris / Heroic の AppID を解決 |

---

## Lutris、Heroic、Faugus、UMU

- **Lutris：** 詳細オプションを有効にし、`proton-cachyos-slr`（または使用中の Proton ビルド）を選択、Lutris ランタイムを無効化、システムライブラリを優先し、コマンドプレフィックスに `steam-auto-run` を設定します。
- **Heroic / Faugus：** `proton-cachyos-slr` を選択し、ラッパー／コマンドプレフィックスとして `steam-auto-run` を追加します。
- **UMU / Protonfixes：** 必要に応じて `PROTON_VERB=waitforexitandrun` と `GAMEID=umu-<appid>` をエクスポートします。

---

## トラブルシューティング

- **Wayland または DX12 での高速クラッシュ：** `steam-auto-ui` の **ログと復旧** を開く（または `steam-auto-run --last-log APPID` を実行）してセーフモード（`USE_XWAYLAND=1`、`USE_SAFEDX12=1`）を適用するか、`XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%` で起動してください。
- **アンチチート対応タイトルが起動しない：** `proton-cachyos-slr`（Steam Linux Runtime）を使用し、`steam-auto-run --doctor` で EAC v2、`/dev/ntsync`、`vm.max_map_count` を確認してください。
- **Steam が起動オプションを元に戻してしまう：** `steam-auto-sync` または `steam-auto-sync --sanitize` を実行する前に Steam を完全に終了してください。
- **VRR 上限が誤っている・適用されない：** `VRR_CAP=<fps>` を明示設定するか、`VRR_CAP=0` で無効化、または `-6%` の余裕を設ける場合は `VRR_MINUS_MARGIN=1` を使用します。Gamescope では、明示的な `VRR_CAP` を指定した場合のみ DXVK/VKD3D の上限がエクスポートされます。
- **ネットワーク QoS の確認：** `steam-net-boost status`（権限不要の読み取り専用）を実行します。自動セッション QoS を使う場合は `./install.sh --with-net-boost` で root ヘルパーをインストールしてください。

---

## v2.1 の新機能（Mesa 27.0 / RDNA 4・Ultra Bleeding-Edge・Hunt 594650・Steam Controller 2026）

- **Mesa 27.0 / RDNA 4 フラグ:** `TRANSFER_QUEUE=1`（RDNA 3/4 向け重複除去済み `RADV_PERFTEST=sam,transfer_queue`）、`NATIVE_ANTILAG=1`（ネイティブ `VK_AMD_anti_lag`）、`REFLEX_LAYER=1`（`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`、アンチチート/MLFG では無効）、`VK_VIDEO_DECODE=1`（`RADV_EXPERIMENTAL=video_decode`）。
- **Ultra Bleeding-Edge (`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`):** 非アンチチート向けの実験的スタック（`VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`、`VKD3D_FEATURE_LEVEL=12_2`、`VKD3D_SHADER_MODEL=6_8`、`PROTON_FSR4_UPGRADE=1`、`PROTON_NATIVE_AGS=1`、`PROTON_USE_WOW64=1`、`PROTON_MEDIA_FORCE_GST=1`、Gamescope 外のネイティブ Wayland のみ `WAYLANDDRV_RAWINPUT=1`）。
- **Hunt: Showdown 1896 (`AppID 594650`) 互換ガード:** `competitive-anticheat`、`USE_XWAYLAND=1`、`USE_SAFEDX12=1`、`PROTON_NATIVE_AGS=0`、`LOW_LATENCY_LAYER=0`、`USE_MLFG=0`、`USE_BLEEDING_EDGE=0`、`USE_NET_OPT=1` を強制し、`--doctor` と `steam-auto-ui` で `config.vdf` の `Proton 11.0-2` / `Proton Hotfix` 設定を確認します。
- **Steam Controller 2026 / Wireless Steam Puck (`28de:{1302,1304,1005,1007}`):** 4 モード（`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`）。`wayland-hdr` はネイティブ Wayland + HDR10（`PROTON_ENABLE_WAYLAND=1`、`DXVK_HDR=1`、`PROTON_USE_SDL=0`、`PROTON_NO_STEAMINPUT=0`、`sdlinput` 除外）を維持しつつ、`steam://forceinputappid/<APPID>` と `udevadm` 自動再接続監視を実行し、終了時に `steam://forceinputappid/0` へ戻します。手動再適用は `steam-auto-run --reapply-input <APPID|0>`、udev ルールは `./install.sh --with-steam-controller`。

---

内部設計については [ARCHITECTURE.md](../../ARCHITECTURE.md)、英語の正規ガイドは [English User Guide](../../USER_GUIDE.md)、全 27 言語ガイドの一覧は [i18n Index](../README.md) を参照してください。
