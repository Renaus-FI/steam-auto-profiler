# Steam Auto-Profiler ユーザーガイド

このガイドは、インストール、Steam連携、起動、診断の基本をまとめたものです。詳細は[英語ガイド](../../USER_GUIDE.md)を参照してください。

## インストール

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` は任意のネットワークQoSヘルパーを導入します。`--compat-cachy-run` は既存の `/usr/local/bin/cachy-run` を `.bak` として保持し互換shimを導入します。`--with-auto-sync` はsystemdユーザーwatcherを導入します。`--uninstall` は導入内容を削除します。

## 動作の概要

`steam-auto-detect` はSteamのAppIDマニフェストとライブラリを調べ、ゲームフォルダーを最大10階層スキャンし、優先順位に従って分類します。(1) `competitive-anticheat`、(2) ネイティブFSR/FidelityFX (`native-fsr4` / `native-fsr`)、(3) `legacy-upscaler`、(4) `standard`です。

`steam-auto-run` は `SteamAppId`、`STEAM_COMPAT_APP_ID`、`GAMEID` の順でAppIDを解決し、`umu-` 接頭辞を除去します。`kdialog` または `zenity` を表示し、選択を `~/.config/steam-auto-profiler/profiles/<APPID>.env` に保存できます。保存形式は `KEY=VALUE` で、未知のキーやシェル構文は無視されます。

互換設定は既存値を保持したまま `PROTON_ADD_CONFIG` と `STEAM_COMPAT_CONFIG` に反映されます。主要トークンは `wayland`、`fsr4`、`mlfg`、`dxvklowlatency`、`vkd3dlowlatency`、`sdlinput`、`nativeags`、`noopwr`、`vkd3dbindlesstb`、`localshadercache`、`pipewire`、`vkreflex`です。

## Steamの自動化

Steamのゲーム起動オプション:

```text
steam-auto-run %command%
```

UMUでは `GAMEID=umu-2357570 steam-auto-run %command%` とします。

`localconfig.vdf` を変更する前にSteamを完全終了してください。

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` は `--sanitize` の別名、`--remove` はwrapper削除、`--print-library-paths` はライブラリ一覧、`--keep-backups N` はバックアップ保存数です（`0`ですべて保持）。

watcherは `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` を実行します。`steam-auto-sync --install-systemd` でunitを導入できます。

## コマンドと環境変数

`steam-auto-run --doctor`、`--inspect APPID`、`--configure APPID`、`--dry-run APPID`、`--reset APPID`、`--list-profiles`、`--last-log [APPID]`。JSON: `steam-auto-detect --inspect --json APPID`。

主な変数: `NO_GUI=1`、`FORCE_GUI=1`、`XWAYLAND=1`、`MLFG=1`、`VRR_CAP=<fps>`、`KEEP_OVERLAY=1`、`GAMEID=umu-<appid>`、`NETOPT=1`、`OPTISCALER=1`、`SDL=1`、`SAFEDX12=1`、`NO_NTSYNC=1`。

`VRR_CAP` が優先されます。未指定時は `kscreen-doctor`、`wlr-randr`、`xrandr` からリフレッシュレートを取得し、60 Hzを超える場合は94%を上限にします。Gamescopeでは `VRR_CAP` が明示されない限りDXVK/VKD3Dフレームレートを追加しません。

## ネットワークとトラブルシューティング

`NETOPT=1` または `netopt` を選ぶと、`steam-net-boost` がCAKEまたは`fq_codel`を有効化し、EEEとtx queue lengthをセッション中だけ調整します。最後のゲームセッション終了時に元の状態へ戻します。

状態確認: `sudo steam-net-boost status [IFACE]`。Steam変更時は完全終了してください。誤ったプロフィールには `FORCE_GUI=1` または `--reset APPID` を使います。アンチチートタイトルでは `proton-cachyos-slr` を優先し、`--doctor`で確認してください。
