# Steam Auto-Profiler 用户指南

本文概述安装、Steam 自动化、启动配置和故障排查。完整技术说明请参阅[英文指南](../../USER_GUIDE.md)。

## 安装

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` 安装可选的网络 QoS 辅助程序。`--compat-cachy-run` 将现有 `/usr/local/bin/cachy-run` 保留为 `.bak`，并安装兼容 shim。`--with-auto-sync` 安装 systemd 用户 watcher。`--uninstall` 删除已安装组件。

## 工作原理

`steam-auto-detect` 在 Steam 清单和库中查找 AppID，向下扫描游戏目录最多十层，并按优先级分类：(1) `competitive-anticheat`，(2) 原生 FSR/FidelityFX（`native-fsr4`/`native-fsr`），(3) `legacy-upscaler`，(4) `standard`。

`steam-auto-run` 按 `SteamAppId`、`STEAM_COMPAT_APP_ID`、`GAMEID` 的顺序解析 AppID，并移除 `umu-` 前缀。它可显示 `kdialog` 或 `zenity` 对话框，并将设置保存到 `~/.config/steam-auto-profiler/profiles/<APPID>.env`。配置格式为 `KEY=VALUE`，未知键和 shell 语法会被忽略。

兼容设置会写入 `PROTON_ADD_CONFIG` 和 `STEAM_COMPAT_CONFIG`，并保留已有值。常用 token 包括 `wayland`、`fsr4`、`mlfg`、`dxvklowlatency`、`vkd3dlowlatency`、`sdlinput`、`nativeags`、`noopwr`、`vkd3dbindlesstb`、`localshadercache`、`pipewire`、`vkreflex`。

## Steam 自动化

在 Steam 启动选项中填写：

```text
steam-auto-run %command%
```

UMU 示例：`GAMEID=umu-2357570 steam-auto-run %command%`。

修改 `localconfig.vdf` 前请完全退出 Steam：

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` 是 `--sanitize` 的别名；`--remove` 删除 wrapper；`--print-library-paths` 显示库；`--keep-backups N` 保留 N 个备份（`0` 保留全部）。

watcher 会执行 `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`。可运行 `steam-auto-sync --install-systemd` 安装单元。

## 命令与环境变量

`steam-auto-run --doctor`、`--inspect APPID`、`--configure APPID`、`--dry-run APPID`、`--reset APPID`、`--list-profiles`、`--last-log [APPID]`。JSON：`steam-auto-detect --inspect --json APPID`。

常用变量：`NO_GUI=1`、`FORCE_GUI=1`、`XWAYLAND=1`、`MLFG=1`、`VRR_CAP=<fps>`、`KEEP_OVERLAY=1`、`GAMEID=umu-<appid>`、`NETOPT=1`、`OPTISCALER=1`、`SDL=1`、`SAFEDX12=1`、`NO_NTSYNC=1`。

`VRR_CAP` 优先级最高；未指定时使用 `kscreen-doctor`、`wlr-randr` 或 `xrandr` 查询刷新率，超过 60 Hz 时使用刷新率的 94% 上限。Gamescope 中只有明确设置 `VRR_CAP` 才导出 DXVK/VKD3D 帧率限制。

## 网络与故障排查

设置 `NETOPT=1` 或选择 `netopt` 后，`steam-net-boost` 会启用 CAKE 或 `fq_codel`，临时调整 EEE 和 tx queue length；最后一个游戏会话退出时恢复原状态。

状态：`sudo steam-net-boost status [IFACE]`。同步前完全退出 Steam。配置异常时使用 `FORCE_GUI=1` 或 `--reset APPID`。反作弊游戏优先使用 `proton-cachyos-slr`，并用 `--doctor`检查系统。
