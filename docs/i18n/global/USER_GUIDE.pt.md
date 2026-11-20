# Guia do usuário Steam Auto-Profiler

Este guia cobre instalação e operação completa. Consulte o [guia em inglês](../../USER_GUIDE.md) para detalhes técnicos.

## Instalação

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

`--with-net-boost` instala o auxiliar opcional de QoS de rede. `--compat-cachy-run` preserva `/usr/local/bin/cachy-run` como `.bak` e instala o shim. `--with-auto-sync` instala o watcher systemd do usuário. `--uninstall` remove os componentes.

## Como funciona

`steam-auto-detect` encontra o AppID nos manifestos e bibliotecas Steam, percorre a pasta do jogo até dez níveis e usa prioridade: (1) `competitive-anticheat`, (2) FSR/FidelityFX nativo (`native-fsr4`/`native-fsr`), (3) `legacy-upscaler`, (4) `standard`.

`steam-auto-run` resolve `SteamAppId`, `STEAM_COMPAT_APP_ID` e `GAMEID`, removendo o prefixo `umu-`. Pode abrir `kdialog` ou `zenity` e salvar opções em `~/.config/steam-auto-profiler/profiles/<APPID>.env`. O perfil usa `KEY=VALUE`; sintaxe de shell e chaves desconhecidas são ignoradas.

As configurações são colocadas em `PROTON_ADD_CONFIG` e `STEAM_COMPAT_CONFIG`, preservando valores existentes. Tokens suportados incluem `wayland`, `fsr4`, `mlfg`, `dxvklowlatency`, `vkd3dlowlatency`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `localshadercache`, `pipewire` e `vkreflex`.

## Automação no Steam

Opções de lançamento do Steam:

```text
steam-auto-run %command%
```

Para UMU: `GAMEID=umu-2357570 steam-auto-run %command%`.

Feche completamente o Steam antes de alterar `localconfig.vdf`:

```bash
steam-auto-sync --report
steam-auto-sync --dry-run
steam-auto-sync --sanitize --dry-run
steam-auto-sync --sanitize
steam-auto-sync --migrate-cachy-run
```

`--clean` é alias de `--sanitize`; `--remove` remove o wrapper; `--print-library-paths` lista bibliotecas; `--keep-backups N` conserva N backups (`0` conserva todos).

O watcher executa `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300`. Use `steam-auto-sync --install-systemd` para instalar as unidades.

## Comandos e variáveis

`steam-auto-run --doctor`, `--inspect APPID`, `--configure APPID`, `--dry-run APPID`, `--reset APPID`, `--list-profiles` e `--last-log [APPID]`. JSON: `steam-auto-detect --inspect --json APPID`.

Variáveis principais: `NO_GUI=1`, `FORCE_GUI=1`, `XWAYLAND=1`, `MLFG=1`, `VRR_CAP=<fps>`, `KEEP_OVERLAY=1`, `GAMEID=umu-<appid>`, `NETOPT=1`, `OPTISCALER=1`, `SDL=1`, `SAFEDX12=1` e `NO_NTSYNC=1`.

`VRR_CAP` tem prioridade. Sem ele, o programa consulta `kscreen-doctor`, `wlr-randr` ou `xrandr`; acima de 60 Hz calcula 94 % como limite. No Gamescope, limites DXVK/VKD3D só são exportados com `VRR_CAP`.

## Rede e solução de problemas

Com `NETOPT=1` ou `netopt`, `steam-net-boost` ativa CAKE ou `fq_codel`, altera temporariamente EEE e ajusta tx queue length. Ao terminar a última sessão, restaura o estado anterior.

Status: `sudo steam-net-boost status [IFACE]`. Feche o Steam antes da sincronização. Use `FORCE_GUI=1` ou `--reset APPID` para corrigir perfis. Para anti-cheat, prefira `proton-cachyos-slr` e execute `--doctor`.
