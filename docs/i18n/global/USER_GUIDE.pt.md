# Guia do Usuário do Steam Auto-Profiler

> [English User Guide](../../USER_GUIDE.md) | [i18n Index](../README.md)

Este guia cobre a instalação completa, a orquestração de inicialização para tela plana e VR, o Centro de Controle `steam-auto-ui`, a sincronização da biblioteca, benchmarking e solução de problemas do **Steam Auto-Profiler v2.0**.

O Steam Auto-Profiler é um lançador e centro de controle leve em Bash/Python para Linux que inspeciona um AppID do Steam (ou atalho de jogo Não-Steam), aplica um perfil sensível ao contexto com proteções rigorosas de driver/upscaler/anti-cheat e inicia o comando existente do jogo. Ele nunca empacota nem injeta um runtime Proton de terceiros.

---

## Requisitos

- Sessão de desktop Linux (KDE Plasma 6 / Wayland, GNOME, wlroots ou X11), Bash 5+, Python 3.10+, Steam e utilitários padrão do sistema.
- GUI nativa opcional para o Centro de Controle: `PyQt6` ou `PySide6` (recorre automaticamente à TUI `curses` da biblioteca padrão, sem dependências externas).
- Diálogos opcionais de lista de verificação pré-lançamento: `kdialog` ou `zenity`.
- Benchmarking silencioso opcional de frametime: `mangohud`.
- Auxiliar opcional de rede por sessão: `tc`, `ip` e `ethtool` (`sudo` é necessário apenas durante a instalação com `--with-net-boost`).

---

## Instalação e Atualizações

```bash
git clone https://github.com/Renaus-FI/steam-auto-profiler.git
cd steam-auto-profiler
./install.sh
```

`./install.sh` copia todos os seis executáveis (`steam-auto-run`, `steam-auto-detect`, `steam-auto-sync`, `steam-net-boost`, `vr-run` e `steam-auto-ui`) para `~/.local/bin`, instala o atalho de desktop (`~/.local/share/applications/steam-auto-profiler.desktop`), cria `~/.config/steam-auto-profiler/profiles` e adiciona os presets padrão do vkBasalt (`competitive`, `standard`, `vivid`, `shooter`, `oled-clean`). Certifique-se de que `~/.local/bin` esteja no `PATH`.

As opções do instalador podem ser combinadas:

```bash
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

- `--with-net-boost`: instala `/usr/local/bin/steam-net-boost` (além de cópias no sistema dos outros scripts) e uma regra `sudoers` estritamente limitada sem senha para `steam-net-boost`.
- `--compat-cachy-run`: preserva um `/usr/local/bin/cachy-run` existente como `/usr/local/bin/cachy-run.bak` (a menos que já seja o shim do Steam Auto-Profiler) e instala um shim de redirecionamento para `steam-auto-run`.
- `--with-auto-sync` (`--enable-auto-sync`): instala e habilita o monitor systemd de usuário `steam-auto-profiler-sync.path` e seu serviço `oneshot` correspondente em todas as bibliotecas Steam descobertas.
- `--uninstall`: remove os binários instalados, o atalho de desktop, o auxiliar de rede/regra sudoers opcionais, o shim de compatibilidade e as unidades systemd de usuário de sincronização automática.

Para atualizar um repositório já clonado:

```bash
git pull --ff-only
./install.sh --with-net-boost --compat-cachy-run --with-auto-sync
```

Verifique se o sistema está pronto antes de sincronizar os jogos:

```bash
steam-auto-run --doctor
```

---

## Pipeline de Lançamento Ponta a Ponta

1. **Resolução de AppID:** Verifica `SteamAppId`, `STEAM_COMPAT_APP_ID` e depois `GAMEID` (removendo qualquer prefixo `umu-` para Lutris/Heroic/UMU).
2. **Descoberta de Bibliotecas e Atalhos:** `steam-auto-detect` pesquisa raízes do Steam e bibliotecas secundárias em `libraryfolders.vdf`, lê `appmanifest_<APPID>.acf` ou recorre em modo somente leitura ao arquivo binário `userdata/*/config/shortcuts.vdf`, executando então um `find` de passagem única de até 10 níveis de profundidade (ignorando `screenshots`, `saves`, `logs`, `shadercache`, `workshop`, `movies`, `videos`, `localization`).
3. **Precedência de Classificação em Cinco Níveis:**
   - **1. `competitive-anticheat`:** AppID competitivo conhecido ou runtime anti-cheat detectado (EAC, BattlEye, Ricochet, ACE, GameGuard, XIGNCODE, etc.). Desativa OptiScaler, MLFG, vkBasalt e DXVK assíncrono; ativa baixa latência e QoS de rede da sessão.
   - **2. `vr`:** Detecta `openvr_api.dll`/`openvr_api.so`, `openxr_loader.dll`/`libopenxr_loader.so*`, `*.vrmanifest` ou flags de atalho `vr-run`/`-vr`. Exporta `AUTO_IS_VR=1`.
   - **3. `native-fsr4` / `native-fsr`:** FidelityFX SDK 3.1+ modular (`amd_fidelityfx_upscaler_*.dll`, `amd_fidelityfx_framegeneration_dx12.dll`, `amdxcffx64.dll`). Ativa o upgrade FSR4 em nível de driver (`PROTON_FSR4_UPGRADE=1` ou `PROTON_FSR4_RDNA3_UPGRADE=1` em AMD RDNA 3).
   - **4. `legacy-upscaler`:** DLLs legadas de DLSS (`nvngx_dlss*.dll`), XeSS (`libxess*.dll`), Streamline (`sl.interposer.dll`) ou FSR 2/3.0. Marca `AUTO_OPTISCALER=1` e define orientações em `AUTO_UPSCALER_INFO`.
   - **5. `standard`:** Perfil seguro de Wine Wayland nativo + VRR de baixa latência.
4. **Limitação de Taxa de Atualização VRR:** Um `VRR_CAP=<fps>` explícito sempre prevalece (`VRR_CAP=0` desativa o limite). Caso contrário, a taxa de atualização ativa da tela é consultada via `kscreen-doctor` (modo ativo `*` do KDE Plasma 6 ou `Hz` legado), `wlr-randr` ou `xrandr` e aplicada 1:1 por padrão (`240 FPS` em 240 Hz). Ative `VRR_MINUS_MARGIN=1` para a margem de segurança VRR opcional de `-6%` (`hz * 94 / 100`, ex.: `225 FPS` em 240 Hz). Em sessões Gamescope, os limites DXVK/VKD3D são omitidos salvo quando `VRR_CAP` for explícito.
5. **Proteções de Exclusão Mútua:**
   - **FSR 4 / OptiScaler + vkBasalt:** `ENABLE_VKBASALT=0` é imposto sempre que `PROTON_FSR4_UPGRADE=1`, `PROTON_FSR4_RDNA3_UPGRADE=1` ou `USE_OPTISCALER=1` estiver ativo (evita nitidez dupla e clipping HDR10).
   - **MLFG + Baixa Latência / Limites VRR:** `MLFG=1` (`USE_MLFG=1`) exporta `ENABLE_LAYER_MESA_ANTI_LAG=0`, `PROTON_DXVK_LOWLATENCY=0`, `PROTON_VKD3D_LOWLATENCY=0`, remove `DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE` e `DXVK_FRAME_PACE`, e exporta `DXIL_SPIRV_CONFIG=wmma_rdna3_workaround` em AMD RDNA 3. Quando `USE_MLFG=0` e o limite VRR está ativo, `DXVK_FRAME_PACE=low-latency-vrr` é exportado.
   - **DX12 Moderno + Safe DX12:** Exporta `PROTON_NATIVE_AGS=1` em AMD e `VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer` quando `USE_SAFEDX12=0` (omitido de forma limpa quando `SAFEDX12=1`).
6. **Mapeamento de Tokens de Compatibilidade:** Recursos gerenciados são anexados sem sobrescrever os valores do usuário tanto em `PROTON_ADD_CONFIG` quanto em `STEAM_COMPAT_CONFIG`: `wayland`, `sdlinput`, `nativeags`, `noopwr`, `vkd3dbindlesstb`, `dxvklowlatency`, `vkd3dlowlatency`, `localshadercache`, `pipewire`, `fsr4`, `mlfg`, `vkreflex`, `nontsync`, `nowmdecoration`.
7. **HDR Automático no KDE Plasma 6 (`AUTO_HDR_SWITCH=1`):** Quando ativado fora do Gamescope com `DXVK_HDR=1` (ou `USE_HDR=1`), consulta a saída principal habilitada via `kscreen-doctor -o`; se o HDR estiver desativado, ativa-o antes do lançamento e restaura SDR em um trap `EXIT`/`INT`/`TERM`.
8. **Benchmarking Silencioso de Frametime (`BENCH=1`):** Executa o MangoHud em modo CSV oculto (`no_display,autostart_log=1,log_duration=${BENCH_DURATION:-60}`), analisa os frametimes ao encerrar, anexa `Avg FPS`, `1% Low FPS` e `P99 (ms)` em `~/.config/steam-auto-profiler/benchmarks/<APPID>.json` e remove os CSVs temporários.
9. **Autorrecuperação em Modo Seguro para Travamento Rápido:** Se um título Proton/Windows encerrar com código diferente de zero em menos de `20s` (configurável via `SAP_CRASH_THRESHOLD_SEC`) enquanto flags experimentais de Wayland ou DX12 estiverem ativas (`USE_XWAYLAND=0` ou `USE_SAFEDX12=0`), registra um `crash_hint` em `last-<APPID>.log` e `last-launch.log` e oferece (com GUI ativa) salvar `USE_XWAYLAND=1` + `USE_SAFEDX12=1` para o próximo lançamento.
10. **Ciclo de Vida do Agendador e Rede:** Executa via `game-performance` -> `powerprofilesctl launch -p performance --` -> `gamemoderun` (somente quando `ananicy-cpp.service` está inativo) -> execução direta, com `PRIME=1` (`prime-run`) opcional. Se `USE_NET_OPT=1`, `steam-net-boost` executa `on`/`off` com contagem de referências e `flock`, preservando hierarquias estáticas root CAKE e HTB + leaf CAKE.

---

## Centro de Controle Unificado (`steam-auto-ui`)

Abra o `steam-auto-ui` pelo menu de aplicativos, via `steam-auto-run --ui` ou diretamente:

```bash
steam-auto-ui                 # Detecta automaticamente a GUI Qt6 (PyQt6/PySide6) ou TUI curses
steam-auto-ui --gui           # Força a janela gráfica nativa Qt6
steam-auto-ui --tui           # Força a TUI curses da stdlib (funciona via SSH)
steam-auto-ui --lang fi       # Inicia com idioma de interface explícito (27 idiomas suportados)
steam-auto-ui --check         # Executa autoverificação headless (imprime diagnóstico em JSON)
```

O `steam-auto-ui` detecta automaticamente a localidade do sistema via `LC_ALL` / `LC_MESSAGES` / `LANG` e disponibiliza um seletor de idioma ao vivo na GUI Qt6 (e o atalho `L` na TUI `curses`) para alternar entre todos os 27 idiomas em tempo de execução sem reiniciar.

### Cinco Visualizações Sincronizadas

1. **Jogos e Perfis:** Tabela filtrável de títulos Steam e entradas Não-Steam somente leitura de `shortcuts.vdf` (`AppID`, `Game Name`, `Source`, `Auto Class`, `Synced`, `Profile`), selo de SDK de upscaling (`AUTO_UPSCALER_INFO`), validação em tempo real de exclusão mútua nos 10 alternadores de perfil + `VRR_CAP`, `Dry-Run Preview`, botão de acesso direto a `Benchmarks` e `Reset Profile`.
2. **Sistema e Telemetria:** Leitura ao vivo não bloqueante de `steam-auto-run --doctor`, estado de `scxctl get` / `sched_ext`, versões instaladas da pilha (`mesa-git`/`mesa`, `proton-cachyos-slr`, `wivrn-server`, `xrizer-git`/`xrizer`, `mangohud`), uso de cache de shaders (`~/.cache/mesa_shader_cache*`, `radv_builtin_shaders*`), alertas de downgrade git/AUR em `/var/log/pacman.log`, VRAM/uso/temperatura da GPU, vazão LAN (`10:`) vs WAN (`20:`/root) e `av_delay` via `tc -s qdisc`, e `vr-mode status`.
3. **Sincronização da Biblioteca:** Banner ao vivo de proteção contra o Steam em execução mais ações de um clique para `--report`, `--sanitize --dry-run`, `--sanitize` (recusado enquanto o Steam estiver aberto) e `--migrate-cachy-run`.
4. **Logs e Recuperação:** Navegue por `last-launch.log` e `last-<APPID>.log`, inspecione alertas `crash_hint` e aplique o Modo Seguro com um clique (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`).
5. **Benchmarks:** Tabela comparativa filtrável lado a lado das execuções de frametime com `BENCH=1` (`Avg FPS`, `1% Low FPS`, `P99 (ms)`, `Samples`, `FSR4`, `MLFG`, `XWayland`, `SafeDX12`, `VRR Cap`).

---

## Orquestração de VR (`vr-run`)

No Steam, defina **Propriedades > Geral > Opções de inicialização** para títulos VR como:

```text
vr-run %command%
```

- Remove sobreposições herdadas de tela plana (`DXVK_FRAME_RATE`, `VKD3D_FRAME_RATE`, `DXVK_FRAME_PACE`, `PROTON_ENABLE_WAYLAND`, `PROTON_USE_WAYLAND`, `ENABLE_LAYER_MESA_ANTI_LAG`, `ENABLE_VKBASALT`, `PROTON_MLFG_UPGRADE`, `MLFG_UPGRADE`).
- Seleciona automaticamente a GPU dedicada com maior VRAM via `MESA_VK_DEVICE_SELECT` e define `AMD_VULKAN_ICD=RADV` / `RADV_PERFTEST=sam` em GPUs AMD.
- Sondagem dinâmica de caminhos OpenXR/OpenVR do WiVRn e xrizer (`~/.local/share/wivrn-slr/openxr_wivrn.json`, `/usr/share/openxr/1/openxr_wivrn.json`, `/opt/xrizer`, `~/.local/share/xrizer`, `~/.config/openvr`, `$XDG_RUNTIME_DIR/wivrn`) e configuração de `XR_RUNTIME_JSON`, `VR_OVERRIDE`, `PRESSURE_VESSEL_FILESYSTEMS_RO`, `PRESSURE_VESSEL_FILESYSTEMS_RW` e `LD_LIBRARY_PATH` sem sobrescrever configurações explícitas do usuário.
- Controla `vr-mode on` / `vr-mode off` com contagem de referências em `${XDG_RUNTIME_DIR:-/tmp}/vr-run.sessions` (com `flock`) quando `vr-mode` está instalado (`VR_AUTO_MODE=0` desativa).
- Executa pela mesma cadeia de agendadores ciente de `ananicy-cpp` (`game-performance` -> `powerprofilesctl` -> `gamemoderun` -> `exec` direto).
- Pré-visualize as variáveis resolvidas a qualquer momento com `vr-run --dry-run`.

`steam-auto-run` ignora automaticamente o SteamVR (`250820`) e lançamentos `-vr`/`--vr`, e `steam-auto-sync` atribui e preserva automaticamente `vr-run %command%` para títulos VR.

---

## Sincronização da Biblioteca Steam (`steam-auto-sync`)

Feche o Steam completamente antes de gravar em `localconfig.vdf`:

```bash
steam-auto-sync --report              # Auditoria somente leitura da biblioteca + shortcuts.vdf
steam-auto-sync --print-library-paths # Exibe todas as bibliotecas Steam descobertas
steam-auto-sync --dry-run             # Pré-visualiza alterações
steam-auto-sync                       # Injeta steam-auto-run / vr-run
steam-auto-sync --sanitize --dry-run  # Pré-visualiza limpeza de flags antigas
steam-auto-sync --sanitize            # Limpa flags desorganizadas/órfãs (alias: --clean)
steam-auto-sync --migrate-cachy-run   # Migra perfis antigos do cachy-run
steam-auto-sync --remove              # Remove o wrapper steam-auto-run
```

- Backups com carimbo de data/hora `localconfig.vdf.bak.*` são limpos automaticamente com `--keep-backups N` (padrão `10`; `0` mantém todos).
- Exclua AppIDs específicos listando-os (um por linha, comentários `#` permitidos) em `~/.config/steam-auto-profiler/ignore_appids.txt`.
- O monitor systemd de auto-sincronização (`./install.sh --with-auto-sync` ou `steam-auto-sync --install-systemd`) executa `steam-auto-sync --sanitize --wait-for-steam-exit --steam-exit-timeout 300` quando os manifestos do Steam mudam.

---

## Referência de CLI e Perfis

### Comandos

| Finalidade | Comando |
| --- | --- |
| Auditoria de prontidão do sistema | `steam-auto-run --doctor` (alias `--check-system`) |
| Abrir Centro de Controle (GUI/TUI) | `steam-auto-ui [--gui\|--tui\|--check] [--lang CODE]` ou `steam-auto-run --ui` |
| Inspecionar um jogo (legível) | `steam-auto-run --inspect APPID` |
| Inspecionar um jogo (JSON) | `steam-auto-detect --inspect --json APPID` |
| Reconfigurar perfil interativamente | `steam-auto-run --configure APPID` |
| Pré-visualizar ambiente de lançamento | `steam-auto-run --dry-run APPID` |
| Redefinir perfil salvo | `steam-auto-run --reset APPID` |
| Listar perfis salvos | `steam-auto-run --list-profiles` |
| Exibir último log de lançamento | `steam-auto-run --last-log [APPID]` |
| Pré-visualizar ambiente VR | `vr-run --dry-run` |
| Inspecionar auxiliar de rede (somente leitura) | `steam-net-boost status [IFACE]` |

### Chaves `.env` de Perfil Salvas e Sobreposições de Ambiente

Os arquivos de perfil ficam em `~/.config/steam-auto-profiler/profiles/<APPID>.env` e aceitam um formato `KEY=VALUE` baseado em lista permitida (substituições de comando de shell e chaves desconhecidas são ignoradas com segurança):

| Chave `.env` | Variável de Ambiente | Efeito |
| --- | --- | --- |
| `USE_XWAYLAND=1` | `XWAYLAND=1` | Força XWayland em vez de Wine Wayland nativo |
| `USE_FSR4=0` | `FSR4=0` | Desativa o upgrade FSR 4 em nível de driver (padrão `1`) |
| `USE_MLFG=1` | `MLFG=1` | Ativa geração de quadros (desativa Anti-Lag, baixa latência e limites VRR) |
| `USE_OPTISCALER=1` | `OPTISCALER=1` | Ativa a ponte OptiScaler (bloqueada em `competitive-anticheat`) |
| `USE_SHARPEN=1` | `SHARPEN=1` (`RCAS=1`) | Ativa nitidez vkBasalt (desativada quando FSR 4 ou OptiScaler está ativo) |
| `USE_SAFEDX12=1` | `SAFEDX12=1` | Omite flags experimentais de `VKD3D_CONFIG` e o token `vkd3dbindlesstb` |
| `USE_NET_OPT=1` | `NETOPT=1` | Ativa QoS de rede por sessão via `steam-net-boost` |
| `USE_SDL=1` | `SDL=1` | Prefere emulação nativa SDL / Steam Input |
| `USE_KEEP_OVERLAY=1` | `KEEP_OVERLAY=1` | Preserva o `LD_PRELOAD` do Steam Overlay |
| `USE_CEF_FIX=1` | `CEF=1` | Anexa `--in-process-gpu` para launchers CEF |
| `USE_NO_NTSYNC=1` / `PROTON_NO_NTSYNC=1` | `NO_NTSYNC=1` | Desativa NTSync para títulos legados |
| `USE_NO_DECORATION=1` | `NO_DECORATION=1` | Desativa decorações do gerenciador de janelas |
| `VRR_CAP=<fps>` | `VRR_CAP=<fps>` | Limite personalizado de quadros DXVK/VKD3D (`0` desativa o limite) |
| `VRR_MINUS_MARGIN=1` | `VRR_MINUS_MARGIN=1` | Aplica margem de `-6%` na taxa de atualização do monitor (ex.: `225 FPS` em 240 Hz) |
| `WAYLANDDRV_SHORTCUT_INHIBIT=1` | `WAYLANDDRV_SHORTCUT_INHIBIT=1` | Permite inibição de atalhos sob Wine Wayland (padrão `0`) |
| `AUTO_HDR_SWITCH=1` | `AUTO_HDR_SWITCH=1` | Ativa HDR do KDE Plasma 6 automaticamente ao iniciar e restaura SDR ao sair |
| — | `BENCH=1`, `BENCH_DURATION=60` | Executa benchmark CSV silencioso do MangoHud e salva resumo JSON |
| — | `NO_GUI=1` / `FORCE_GUI=1` | Suprime ou força a reabertura da lista `kdialog`/`zenity` pré-lançamento |
| — | `FSR_HUD=1` | Exporta variáveis indicadoras de HUD para FSR/DLSS/MLFG |
| — | `VULKAN=1` / `PRIME=1` | Anexa `-vulkan` / encapsula com `prime-run` |
| — | `GAMEID=umu-<appid>` | Resolve AppIDs do UMU / Lutris / Heroic |

---

## Lutris, Heroic, Faugus e UMU

- **Lutris:** Habilite opções avançadas, selecione `proton-cachyos-slr` (ou sua build do Proton), desative o runtime do Lutris, prefira bibliotecas do sistema e defina o prefixo de comando como `steam-auto-run`.
- **Heroic / Faugus:** Escolha `proton-cachyos-slr` e adicione `steam-auto-run` como wrapper/prefixo de comando.
- **UMU / Protonfixes:** Exporte `PROTON_VERB=waitforexitandrun` e `GAMEID=umu-<appid>` quando necessário.

---

## Solução de Problemas

- **Travamento rápido no Wayland ou DX12:** Abra **Logs e Recuperação** no `steam-auto-ui` (ou execute `steam-auto-run --last-log APPID`) e aplique o Modo Seguro (`USE_XWAYLAND=1`, `USE_SAFEDX12=1`), ou inicie com `XWAYLAND=1 SAFEDX12=1 steam-auto-run %command%`.
- **Títulos anti-cheat não iniciam:** Use `proton-cachyos-slr` (Steam Linux Runtime) e execute `steam-auto-run --doctor` para verificar EAC v2, `/dev/ntsync` e `vm.max_map_count`.
- **O Steam reverte opções de inicialização:** Feche o Steam completamente antes de executar `steam-auto-sync` ou `steam-auto-sync --sanitize`.
- **Limite VRR incorreto ou ausente:** Defina `VRR_CAP=<fps>` explicitamente, `VRR_CAP=0` para desativar ou `VRR_MINUS_MARGIN=1` para margem de `-6%`. No Gamescope, apenas um `VRR_CAP` explícito exporta limites DXVK/VKD3D.
- **Verificação de QoS de rede:** Execute `steam-net-boost status` (somente leitura, sem privilégios). Instale o auxiliar root com `./install.sh --with-net-boost` se desejar QoS automático por sessão.

Consulte [ARCHITECTURE.md](../../ARCHITECTURE.md) para detalhes internos de arquitetura, [English User Guide](../../USER_GUIDE.md) para o guia canônico em inglês e [i18n Index](../README.md) para todos os 27 guias localizados.
