# TECH DESK

**NR TECH | IT MANAGEMENT & SUPPORT CENTER**

Plataforma modular de suporte e gestão de TI para diagnóstico, manutenção, monitoramento, automação e segurança de endpoints Windows.

## Visão do produto

O TECH DESK reúne três interfaces sobre um núcleo compartilhado:

- Terminal: operações administrativas por CLI.
- Desktop: aplicação local para técnicos e administradores.
- Web: painel central de monitoramento e gestão, integrado a agentes locais autenticados.

O objetivo é transformar rotinas dispersas de suporte em operações padronizadas, rastreáveis, seguras e extensíveis.

## Implementado

- CLI interativa com menu de navegação.
- Diagnóstico local somente para leitura.
- Identificação do sistema operacional, arquitetura, processador, núcleos lógicos e hostname.
- Coleta de memória em Windows e Linux quando suportada pelo sistema.
- Inventário de armazenamento da unidade do diretório do usuário.
- Identificação de endereços IP associados ao hostname local.
- Catálogo com 26 opções de diagnóstico no Windows: rede, adaptadores, DNS, rotas, conexões, processos, serviços, inicialização, tarefas, firewall, Defender, atualizações, eventos, USB, bateria, impressoras, softwares e contas locais.
- Consultas PowerShell predefinidas, somente leitura, com timeout e sem aceitar comandos arbitrários.
- Opção `techdesk --diagnostics` para execução direta do relatório.
- Operações administrativas locais: limpeza do cache DNS, limpeza seletiva de arquivos temporários antigos, reinício do Spooler, SFC e DISM.
- Confirmação explícita, allowlist, verificação de elevação para tarefas administrativas, timeout e auditoria JSONL local.
- Testes automatizados para diagnósticos e guardrails de execução.

## Capacidades planejadas

| Domínio | Recursos |
|---|---|
| Diagnóstico | Resumo do endpoint, hardware básico, processos, serviços e eventos |
| Manutenção | Limpeza seletiva de temporários, SFC e DISM (primeiras operações implementadas) |
| Rede | Interfaces, IP, DNS, rotas, conexões e conectividade |
| Segurança | Firewall, Microsoft Defender, políticas e auditoria |
| Gestão | Inventário, histórico de operações e relatórios |
| Automação | Catálogo de tarefas administrativas com validações |
| Inteligência | Assistência contextual para análise e recomendação |

> Os recursos planejados só serão considerados disponíveis após implementação e testes.

## Arquitetura

- Core: Python — configuração, contratos, validação, políticas e logging.
- Windows adapters: PowerShell — integração com recursos nativos do sistema.
- Desktop: Tauri — interface local.
- Web: Next.js — painel de gestão.
- Agent/API: comunicação autenticada entre painel e endpoints.
- Storage: SQLite local e PostgreSQL para cenários centralizados.

Consulte [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) e [docs/SECURITY.md](docs/SECURITY.md).

## Instalação — desenvolvimento

No PowerShell:

`git clone https://github.com/nrdataanalysis-1908/TECH-DESK.git`

`cd TECH-DESK`

`py -3.11 -m venv .venv`

`.\.venv\Scripts\Activate.ps1`

`python -m pip install --upgrade pip`

`pip install -e ".[dev]"`

## Execução

- Menu interativo: `techdesk`
- Relatório direto: `techdesk --diagnostics`

## Testes e qualidade

- `pytest`
- `ruff check .`

## Segurança por concepção

1. Allowlist de operações: nada de execução arbitrária de comandos recebidos do painel.
2. Privilégio mínimo: elevação somente quando indispensável.
3. Confirmação explícita para ações destrutivas ou disruptivas.
4. Validação de pré-condições, timeout e tratamento de falhas.
5. Logs estruturados sem credenciais, tokens ou segredos.
6. Auditoria de ator, operação, horário e resultado.
7. Separação entre interface, regras de negócio e adaptadores do sistema.

Leia [docs/SECURITY.md](docs/SECURITY.md) antes de implementar novos módulos.

## Roadmap

- [x] Repositório e fundação inicial
- [x] Configuração e logging do núcleo
- [x] CLI interativa
- [x] Diagnóstico básico do endpoint
- [x] Catálogo inicial de operações administrativas com confirmação e auditoria
- [ ] Inventário avançado de hardware e software
- [x] Catálogo inicial com 26 diagnósticos somente para leitura
- [ ] Diagnóstico aprofundado de rede e sistema
- [ ] Ampliar rotinas de manutenção Windows
- [ ] Auditoria persistente e histórico
- [ ] Desktop Tauri
- [ ] API e agente local autenticado
- [ ] Painel Web Next.js
- [ ] Assistente inteligente
- [ ] CI, empacotamento e releases

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
