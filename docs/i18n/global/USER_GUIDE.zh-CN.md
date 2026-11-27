# Steam Auto-Profiler 用户指南

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

本指南涵盖 **Steam Auto-Profiler v2.1** 的完整安装、平面屏幕与 VR 启动编排、`steam-auto-ui` 控制中心、游戏库同步、基准测试以及故障排查流程。

Steam Auto-Profiler 是一款面向 Linux 的轻量级 Bash/Python 启动器与控制中心：它会检测 Steam AppID（或非 Steam 快捷方式），应用带有严格驱动/超分辨率/反作弊保护护栏的上下文配置文件，然后启动原有游戏命令。它绝不捆绑或注入第三方 Proton 运行时。

---

## 系统要求

- Linux 桌面会话（KDE Plasma 6 / Wayland、GNOME、wlroots 或 X11）、Bash 5+、Python 3.10+、Steam 及标准核心工具。
- 可选原生控制中心 GUI：`PyQt6` 或 `PySide6`（未安装时自动回退至零依赖的 Python 标准库 `curses` TUI）。
- 可选启动前检查清单弹窗：`kdialog` 或 `zenity`。
- 可选静默帧时间（frametime）基准测试：`mangohud`。
- 可选会话级网络助手：`tc`、`ip` 与 `ethtool`（仅在执行 `--with-net-boost` 安装时需要 `sudo`）。

---

## 安装与更新

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` 会将全部六个可执行文件（`steam-auto-run`、`steam-auto-detect`、`steam-auto-sync`、`steam-net-boost`、`vr-run` 与 `steam-auto-ui`）复制到 `~/.local/bin`，安装桌面入口（`~/.local/share/applications/steam-auto-profiler.desktop`），创建 `~/.config/steam-auto-profiler/profiles`，并添加默认 vkBasalt 预设（`competitive`、`standard`、`vivid`、`shooter`、`oled-clean`）。请确保 `~/.local/bin` 已加入 `PATH`。

安装脚本的可选参数可以组合使用：

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`：安装 `/usr/local/bin/steam-net-boost`（以及其他脚本的系统级副本），并为 `steam-net-boost` 配置最小权限免密 `sudoers` 规则。
- `--compat-cachy-run`：将已有的 `/usr/local/bin/cachy-run` 备份为 `/usr/local/bin/cachy-run.bak`（若它尚非 Steam Auto-Profiler 垫片），并安装转发至 `steam-auto-run` 的兼容垫片。
- `--with-auto-sync`（`--enable-auto-sync`）：为所有已发现的 Steam 游戏库安装并启用 systemd 用户监视器 `steam-auto-profiler-sync.path` 及对应的 oneshot 服务。
- `--uninstall`：移除已安装的二进制文件、桌面入口、可选网络助手/sudoers 规则、兼容垫片以及自动同步 systemd 用户单元。

更新现有本地仓库：

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

在同步游戏前检查主机就绪状态：

```bash
steam-auto-run --doctor
```

---

## 端到端启动流水线

1. **AppID 解析：** 依次检查 `SteamAppId`、`STEAM_COMPAT_APP_ID`，随后检查 `GAMEID`（为 Lutris/Heroic/UMU 去除 `umu-` 前缀）。
2. **游戏库与快捷方式发现：** `steam-auto-detect` 搜索 Steam 根目录及 `libraryfolders.vdf` 中的辅助库，读取 `appmanifest_<APPID>.acf`，或以只读方式回退解析二进制 `userdata/*/config/shortcuts.vdf`，随后执行单次 `find` 扫描，最深 10 层（跳过 `screenshots`、`saves`、`logs`、`shadercache`、`workshop`、`movies`、`videos`、`localization`）。
3. **五级分类优先级：**
   - **1. `competitive-anticheat`：** 已知竞技游戏 AppID 或检测到反作弊运行时（EAC、BattlEye、Ricochet、ACE、GameGuard、XIGNCODE 等）。禁用 OptiScaler、MLFG、vkBasalt 与异步 DXVK；启用低延迟与会话网络 QoS。
   - **2. `vr`：** 检测到 `openvr_api.dll`/`openvr_api.so`、`openxr_loader.dll`/`libopenxr_loader.so*`、`*.vrmanifest`，或快捷方式中的 `vr-run`/`-vr` 标志。导出 `AUTO_IS_VR=1`。
   - **3. `native-fsr4` / `native-fsr`：** 模块化 FidelityFX SDK 3.1+（`amd_fidelityfx_upscaler_*.dll`、`amd_fidelityfx_framegeneration_dx12.dll`、`amdxcffx64.dll`）。启用驱动级 FSR4 升级（`PROTON_FSR4_UPGRADE=1`，在 AMD RDNA 3 上为 `PROTON_FSR4_RDNA3_UPGRADE=1`）。
   - **4. `legacy-upscaler`：** 旧版 DLSS（`nvngx_dlss*.dll`）、XeSS（`libxess*.dll`）、Streamline（`sl.interposer.dll`）或 FSR 2/3.0 DLL。标记 `AUTO_OPTISCALER=1` 并设置 `AUTO_UPSCALER_INFO` 指引。
   - **5. `standard`：** 安全的原生 Wine Wayland + 低延迟 VRR 配置。
4. **VRR 刷新率上限：** 显式指定的 `VRR_CAP=<fps>` 始终优先（`VRR_CAP=0` 禁用限帧）。否则通过 `kscreen-doctor`（KDE Plasma 6 活动 `*` 模式或传统 `Hz`）、`wlr-randr` 或 `xrandr` 探测当前显示器刷新率，默认 1:1 应用（240 Hz 下为 `240 FPS`）。启用 `VRR_MINUS_MARGIN=1` 可应用可选的 `-6%` VRR 安全余量（`hz * 94 / 100`，例如 240 Hz 下为 `225 FPS`）。在 Gamescope 会话中，除非显式设置了 `VRR_CAP`，否则不会导出 DXVK/VKD3D 帧率上限。
5. **互斥保护护栏：**
   - **FSR 4 / OptiScaler + vkBasalt：** 每当 `PROTON_FSR4_UPGRADE=1`、`PROTON_FSR4_RDNA3_UPGRADE=1` 或 `USE_OPTISCALER=1` 启用时，强制设置 `ENABLE_VKBASALT=0`（防止双重锐化与 HDR10 裁切）。
   - **MLFG + 低延迟 / VRR 限帧：** `MLFG=1`（`USE_MLFG=1`）会导出 `ENABLE_LAYER_MESA_ANTI_LAG=0`、`PROTON_DXVK_LOWLATENCY=0`、`PROTON_VKD3D_LOWLATENCY=0`，取消设置 `DXVK_FRAME_RATE`、`VKD3D_FRAME_RATE` 与 `DXVK_FRAME_PACE`，并在 AMD RDNA 3 上导出 `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround`。当 `USE_MLFG=0` 且启用 VRR 限帧时，导出 `DXVK_FRAME_PACE=low-latency-vrr`。
   - **现代 DX12 + Safe DX12：** 当 `USE_SAFEDX12=0` 时，在 AMD 上导出 `PROTON_NATIVE_AGS=1` 以及 `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`（当 `SAFEDX12=1` 时干净省略）。
6. **兼容令牌（Compat Token）映射：** 受管特性会追加到 `PROTON_ADD_CONFIG` 与 `STEAM_COMPAT_CONFIG` 中而不覆盖现有用户配置：`wayland`、`sdlinput`、`nativeags`、`noopwr`、`vkd3dbindlesstb`、`dxvklowlatency`、`vkd3dlowlatency`、`localshadercache`、`pipewire`、`fsr4`、`mlfg`、`vkreflex`、`nontsync`、`nowmdecoration`。
7. **KDE Plasma 6 自动 HDR（`AUTO_HDR_SWITCH=1`）：** 在 Gamescope 之外与 `DXVK_HDR=1`（或 `USE_HDR=1`）同时启用时，通过 `kscreen-doctor -o` 探测主启用输出；若当前未开启 HDR，则在启动前开启，并在 `EXIT`/`INT`/`TERM` trap 中恢复 SDR。
8. **静默帧时间基准测试（`BENCH=1`）：** 以隐藏 CSV 模式运行 MangoHud（`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`），退出时解析帧时间，将 `Avg FPS`、`1% Low FPS` 与 `P99 (ms)` 追加写入 `~/.config/steam-auto-profiler/benchmarks/<APPID>.json`，并清理临时 CSV 文件。
9. **快速崩溃安全模式自动恢复：** 若 Proton/Windows 游戏在启用实验性 Wayland 或 DX12 标志（`USE_XWAYLAND=0` 或 `USE_SAFEDX12=0`）时，在 `20s` 内（可通过 `SAP_CRASH_THRESHOLD_SEC` 调整）以非零状态退出，系统会在 `last-<APPID>.log` 与 `last-launch.log` 中记录 `crash_hint`，并在 GUI 活跃时提示为下次启动保存 `USE_XWAYLAND=1` + `USE_SAFEDX12=1`。
10. **调度器与网络生命周期：** 依次通过 `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun`（仅当 `ananicy-cpp.service` 未运行时）-> 直接执行，并支持可选的 `PRIME=1`（`prime-run`）。当 `USE_NET_OPT=1` 时，`steam-net-boost` 使用带 `flock` 的引用计数执行 `on`/`off`，同时保留静态 root CAKE 与 HTB + leaf CAKE 队列层次结构。

---

## 统一控制中心（`steam-auto-ui`）

可通过桌面应用菜单、`steam-auto-run --ui` 或直接命令启动 `steam-auto-ui`：

```bash
steam-auto-ui                 # 自动检测 Qt6 GUI (PyQt6/PySide6) 或 curses TUI
steam-auto-ui --gui           # 强制启动原生 Qt6 GUI 窗口
steam-auto-ui --tui           # 强制启动标准库 curses TUI（支持 SSH）
steam-auto-ui --lang fi       # 指定界面语言启动（支持 27 种语言）
steam-auto-ui --check         # 运行无头自检（输出 JSON 诊断信息）
```

`steam-auto-ui` 会从 `LC_ALL` / `LC_MESSAGES` / `LANG` 自动检测系统区域设置，并在 Qt6 GUI 中提供实时语言下拉框（在 `curses` TUI 中按 `L` 快捷键），无需重启即可在全部 27 种语言间即时切换。

### 五个同步视图

1. **游戏与配置：** 可筛选的 Steam 游戏与只读非 Steam `shortcuts.vdf` 条目列表（`AppID`、`Game Name`、`Source`、`Auto Class`、`Synced`、`Profile`）、超分辨率 SDK 徽章（`AUTO_UPSCALER_INFO`）、全部 10 个配置开关 + `VRR_CAP` 的实时互斥校验、`Dry-Run Preview`、快速跳转 `Benchmarks` 按钮以及 `Reset Profile`。
2. **系统与遥测：** 非阻塞实时读取 `steam-auto-run --doctor`、`scxctl get` / `sched_ext` 状态、已安装组件栈版本（`mesa-git`/`mesa`、`proton-cachyos-slr`、`wivrn-server`、`xrizer-git`/`xrizer`、`mangohud`）、着色器缓存占用（`~/.cache/mesa_shader_cache*`、`radv_builtin_shaders*`）、`/var/log/pacman.log` 中的 git/AUR 降级告警、GPU 显存/利用率/温度、`tc -s qdisc` 的 LAN（`10:`）与 WAN（`20:`/root）吞吐及 `av_delay`，以及 `vr-mode status`。
3. **游戏库同步：** 实时 Steam 运行状态保护横幅，以及一键执行 `--report`、`--sanitize --dry-run`、`--sanitize`（Steam 运行时拒绝执行）与 `--migrate-cachy-run`。
4. **日志与恢复：** 浏览 `last-launch.log` 与 `last-<APPID>.log`，查看 `crash_hint` 告警，并一键应用安全模式（`USE_XWAYLAND=1`、`USE_SAFEDX12=1`）。
5. **基准测试：** 可筛选的 `BENCH=1` 帧时间测试并排对比表（`Avg FPS`、`1% Low FPS`、`P99 (ms)`、`Samples`、`FSR4`、`MLFG`、`XWayland`、`SafeDX12`、`VRR Cap`）。

---

## VR 编排（`vr-run`）

在 Steam 中将 VR 游戏的 **属性 > 通用 > 启动选项** 设为：

```text
vr-run %command%
```

- 清理继承自平面屏幕的环境变量覆盖（`DXVK_FRAME_RATE`、`VKD3D_FRAME_RATE`、`DXVK_FRAME_PACE`、`PROTON_ENABLE_WAYLAND`、`PROTON_USE_WAYLAND`、`ENABLE_LAYER_MESA_ANTI_LAG`、`ENABLE_VKBASALT`、`PROTON_MLFG_UPGRADE`、`MLFG_UPGRADE`）。
- 通过 `MESA_VK_DEVICE_SELECT` 自动选择显存最大的独立 GPU，并在 AMD GPU 上设置 `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam`。
- 动态探测 WiVRn 与 xrizer 的 OpenXR/OpenVR 路径（`~/.local/share/wivrn-slr/openxr_wivrn.json`、`/usr/share/openxr/1/openxr_wivrn.json`、`/opt/xrizer`、`~/.local/share/xrizer`、`~/.config/openvr`、`$XDG_RUNTIME_DIR/wivrn`），在不覆盖用户显式配置的前提下设置 `XR_RUNTIME_JSON`、`VR_OVERRIDE`、`PRESSURE_VESSEL_FILESYSTEMS_RO`、`PRESSURE_VESSEL_FILESYSTEMS_RW` 与 `LD_LIBRARY_PATH`。
- 当安装了 `vr-mode` 时，在 `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` 中通过引用计数（配 `flock`）管理 `vr-mode on` / `vr-mode off`（设置 `VR_AUTO_MODE=0` 可禁用）。
- 沿用相同的 `ananicy-cpp` 感知调度器链（`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> 直接 `exec`）。
- 随时运行 `vr-run --dry-run` 预览解析后的环境变量。

`steam-auto-run` 会自动绕过 SteamVR（`250820`）和 `-vr`/`--vr` 启动，`steam-auto-sync` 也会自动为 VR 游戏分配并保留 `vr-run %command%`。

---

## Steam 游戏库同步（`steam-auto-sync`）

写入 `localconfig.vdf` 前请彻底关闭 Steam：

```bash
steam-auto-sync --report              # 只读审计游戏库 + shortcuts.vdf
steam-auto-sync --print-library-paths # 显示所有已发现的 Steam 游戏库路径
steam-auto-sync --dry-run             # 预览修改内容
steam-auto-sync                       # 注入 steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # 预览旧版参数清理
steam-auto-sync --sanitize            # 清理杂乱/孤立参数（别名：--clean）
steam-auto-sync --migrate-cachy-run   # 迁移旧版 cachy-run 配置
steam-auto-sync --remove              # 移除 steam-auto-run 包装器
```

- 带时间戳的备份 `localconfig.vdf.bak.*` 会根据 `--keep-backups N` 自动清理（默认保留 `10` 份；`0` 表示全部保留）。
- 如需排除特定 AppID，请将其按行写入 `~/.config/steam-auto-profiler/ignore_appids.txt`（支持 `#` 注释）。
- systemd 自动同步监视器（`./install.sh --with-auto-sync` 或 `steam-auto-sync --install-systemd`）会在 Steam 清单变动时执行 `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`。

---

## CLI 与配置参考

### 命令列表

| 用途 | 命令 |
| --- | --- |
| 系统就绪度检查 | `steam-auto-run --doctor`（别名 `--check-system`） |
| 启动控制中心（GUI/TUI） | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` 或 `steam-auto-run --ui` |
| 检查游戏信息（人类可读） | `steam-auto-run --inspect APPID` |
| 检查游戏信息（JSON） | `steam-auto-detect --inspect --json APPID` |
| 交互式重新配置游戏 | `steam-auto-run --configure APPID` |
| 预览解析后的启动环境 | `steam-auto-run --dry-run APPID` |
| 重置已保存的配置 | `steam-auto-run --reset APPID` |
| 列出已保存的配置 | `steam-auto-run --list-profiles` |
| 查看最近一次启动日志 | `steam-auto-run --last-log [APPID]` |
| 预览 VR 启动环境 | `vr-run --dry-run` |
| 检查网络助手状态（只读） | `steam-net-boost status [IFACE]` |

### 已保存的 `.env` 配置键与环境变量覆盖

配置文件位于 `~/.config/steam-auto-profiler/profiles/<APPID>.env`，仅接受白名单内的 `KEY=VALUE` 格式（Shell 命令替换与未知键会被安全忽略）：

| `.env` 键 | 环境变量覆盖 | 作用 |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | 强制使用 XWayland 而非原生 Wine Wayland |
| `USE_FSR4=0` | `FSR4=0` | 禁用驱动级 FSR 4 升级（默认 `1`） |
| `USE_MLFG=1` | `MLFG=1` | 启用帧生成（会禁用 Anti-Lag、低延迟和 VRR 帧率上限） |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | 启用 OptiScaler 桥接（在 `competitive-anticheat` 中受护栏禁止） |
| `USE_SHARPEN=1` | `SHARPEN=1`（`RCAS=1`） | 启用 vkBasalt 锐化（当 FSR 4 或 OptiScaler 启用时自动禁用） |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | 省略实验性 `VKD3D_CONFIG` 标志与 `vkd3dbindlesstb` 令牌 |
| `USE_NET_OPT=1` | `NETOPT=1` | 通过 `steam-net-boost` 启用会话级网络 QoS |
| `USE_SDL=1` | `SDL=1` | 优先使用原生 SDL / Steam Input 模拟 |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | 保留 Steam 叠加层的 `LD_PRELOAD` |
| `USE_CEF_FIX=1` | `CEF=1` | 为 CEF 启动器追加 `--in-process-gpu` |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | 为老旧游戏禁用 NTSync |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | 禁用窗口管理器边框装饰 |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | 自定义 DXVK/VKD3D 帧率上限（`0` 禁用限帧） |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | 在显示器刷新率基础上保留 `-6%` 余量（如 240 Hz 下为 `225 FPS`） |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | 允许在 Wine Wayland 下抑制系统快捷键（默认 `0`） |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | 启动时自动开启 KDE Plasma 6 HDR，退出时恢复 SDR |
| — | `BENCH=1`, `BENCH_DURATION=60` | 运行静默 MangoHud CSV 基准测试并保存 JSON 摘要 |
| — | `NO_GUI=1` / `FORCE_GUI=1` | 抑制或强制重新弹出启动前 `kdialog`/`zenity` 检查清单 |
| — | `FSR_HUD=1` | 导出 FSR/DLSS/MLFG HUD 指示器变量 |
| — | `VULKAN=1` / `PRIME=1` | 追加 `-vulkan` / 使用 `prime-run` 包装启动 |
| — | `GAMEID=umu-<appid>` | 解析 UMU / Lutris / Heroic 的 AppID |

---

## Lutris、Heroic、Faugus 与 UMU

- **Lutris：** 开启高级选项，选择 `proton-cachyos-slr`（或你使用的 Proton 版本），关闭 Lutris 运行时，勾选优先使用系统库，并将命令前缀设为 `steam-auto-run`。
- **Heroic / Faugus：** 选择 `proton-cachyos-slr`，并将 `steam-auto-run` 添加为包装器/命令前缀。
- **UMU / Protonfixes：** 按需导出 `PROTON_VERB=waitforexitandrun` 与 `GAMEID=umu-<appid>`。

---

## 故障排查

- **在 Wayland 或 DX12 下快速崩溃：** 打开 `steam-auto-ui` 中的 **日志与恢复**（或运行 `steam-auto-run --last-log APPID`）并一键应用安全模式（`USE_XWAYLAND=1`、`USE_SAFEDX12=1`），或使用 `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%` 启动。
- **反作弊游戏无法启动：** 请使用 `proton-cachyos-slr`（Steam Linux Runtime），并运行 `steam-auto-run --doctor` 检查 EAC v2、`/dev/ntsync` 与 `vm.max_map_count`。
- **Steam 还原了启动选项：** 在运行 `steam-auto-sync` 或 `steam-auto-sync --sanitize` 之前，务必彻底关闭 Steam。
- **VRR 限帧不正确或缺失：** 显式设置 `VRR_CAP=<fps>`、设为 `VRR_CAP=0` 禁用，或使用 `VRR_MINUS_MARGIN=1` 保留 `-6%` 余量。在 Gamescope 中，仅显式设置的 `VRR_CAP` 会导出 DXVK/VKD3D 上限。
- **检查网络 QoS：** 运行 `steam-net-boost status`（无需权限，只读）。如需自动会话级 QoS，请运行 `./install.sh --with-net-boost` 安装 root 助手。

---

## v2.1 新特性（Mesa 27.0 / RDNA 4、Ultra Bleeding-Edge、Hunt 594650 与 Steam Controller 2026）

- **Mesa 27.0 / RDNA 4 选项：** `TRANSFER_QUEUE=1`（RDNA 3/4 去重后的 `RADV_PERFTEST=sam,transfer_queue`）、`NATIVE_ANTILAG=1`（原生 `VK_AMD_anti_lag`）、`REFLEX_LAYER=1`（`LOW_LATENCY_LAYER=1` + `LOW_LATENCY_LAYER_REFLEX=1`，反作弊与 MLFG 中禁用）以及 `VK_VIDEO_DECODE=1`（`RADV_EXPERIMENTAL=video_decode`）。
- **Ultra Bleeding-Edge（`BLEEDING_EDGE=1` / `USE_BLEEDING_EDGE=1`）：** 面向非反作弊游戏的实验栈（`VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer`、`VKD3D_FEATURE_LEVEL=12_2`、`VKD3D_SHADER_MODEL=6_8`、`PROTON_FSR4_UPGRADE=1`、`PROTON_NATIVE_AGS=1`、`PROTON_USE_WOW64=1`、`PROTON_MEDIA_FORCE_GST=1`，仅在 Gamescope 外的原生 Wayland 导出 `WAYLANDDRV_RAWINPUT=1`）。
- **Hunt: Showdown 1896（`AppID 594650`）兼容保护：** 强制 `competitive-anticheat`、`USE_XWAYLAND=1`、`USE_SAFEDX12=1`、`PROTON_NATIVE_AGS=0`、`LOW_LATENCY_LAYER=0`、`USE_MLFG=0`、`USE_BLEEDING_EDGE=0`、`USE_NET_OPT=1`；`--doctor` 与 `steam-auto-ui` 会检查 `config.vdf` 并建议使用 Valve 的 `Proton 11.0-2` 或 `Proton Hotfix`。
- **Steam Controller 2026 / Wireless Steam Puck（`28de:{1302,1304,1005,1007}`）：** 4 种路由模式（`USE_STEAM_CONTROLLER=auto|wayland-hdr|xwayland|off`）：`wayland-hdr` 保持原生 Wayland + HDR10（`PROTON_ENABLE_WAYLAND=1`、`DXVK_HDR=1`、`PROTON_USE_SDL=0`、`PROTON_NO_STEAMINPUT=0`，省略 `sdlinput`），自动调用 `steam://forceinputappid/<APPID>` 并通过 `udevadm` 监听游戏中休眠重连，退出时重置为 `steam://forceinputappid/0`。手动触发：`steam-auto-run --reapply-input <APPID|0>`；udev 规则：`./install.sh --with-steam-controller`。

---

内部架构详情请参阅 [ARCHITECTURE.md](../../ARCHITECTURE.md)，英文原版请查阅 [English User Guide](../../USER_GUIDE.md)，全部 27 种语言指南请参阅 [i18n Index](../README.md)。
