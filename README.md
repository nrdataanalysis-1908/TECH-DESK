<div align="center">

# TECH DESK

### NR TECH | IT MANAGEMENT & SUPPORT CENTER

Central inteligente de suporte, diagnóstico e manutenção de endpoints Windows.

![Python](https://img.shields.io/badge/Python-3.11+-2563EB?style=for-the-badge&logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Platform-Windows-2563EB?style=for-the-badge&logo=windows&logoColor=white)
![CI](https://img.shields.io/badge/CI-Windows%20%7C%20Linux-0EA5E9?style=for-the-badge&logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-2563EB?style=for-the-badge)

</div>

<p align="center">
  <img src="docs/assets/techdesk-menu.svg" alt="Prévia visual do menu TECH DESK em azul e ciano" width="100%">
</p>

## Visão geral

O TECH DESK reúne rotinas de suporte técnico em uma CLI modular, com catálogo fechado de operações, confirmações explícitas, verificação de privilégios, timeout, captura de resultados e trilha de auditoria.

A interface utiliza exclusivamente a paleta azul e ciano da NR TECH. Ações de manutenção, consultas e ferramentas auxiliares são organizadas em grupos próprios.

## Recursos incorporados

### Operações de manutenção

| Área | Recursos |
|---|---|
| Sistema | Limpeza seletiva de temporários, SFC, DISM e CHKDSK online |
| Rede | Limpeza DNS/ARP, renovação DHCP, redefinição Winsock e conectividade |
| Impressão e periféricos | Reinício do Spooler, limpeza da fila e inventário USB |
| Segurança | Microsoft Defender, atualização de assinaturas, verificação rápida e Firewall |
| Windows | Reinício de Explorer/áudio/Windows Update, ponto de restauração e atualização GPO |
| Logs | Backup EVTX de Application, System, Setup e Security; limpeza de Application/Setup somente após backup |
| Aplicativos | Consulta de atualizações e atualização geral via Winget, mediante confirmação |
| Memória | Inventário dos processos de maior consumo e solicitação de fechamento gracioso por PID |

### Ferramentas e consultas

- Informações avançadas do sistema (msinfo32).
- Gerenciador de Dispositivos e Limpeza de Disco.
- PowerShell aberto como ferramenta local, sem execução de comandos arbitrários pelo TECH DESK.
- Teste de velocidade no navegador padrão.
- Diagnóstico de CPU, memória, armazenamento, uptime, processos e serviços.
- Inventário de software, USB, eventos e políticas de grupo.
- Submenu de otimização de memória com ações individuais e sequência guiada, sempre com confirmação.
- Download HTTPS limitado a 100 MiB, com redirecionamentos exclusivamente HTTPS e cálculo SHA-256. O arquivo é salvo, nunca executado pelo TECH DESK.

## Fluxo operacional

<p align="center">
  <img src="docs/assets/techdesk-flow.svg" alt="Fluxo operacional seguro do TECH DESK" width="100%">
</p>

1. O técnico seleciona uma operação do catálogo ou uma consulta somente leitura.
2. O TECH DESK apresenta escopo, risco e exigência de privilégio.
3. Operações de alteração exigem confirmação textual explícita.
4. O núcleo valida ambiente, privilégios e pré-condições.
5. O executor chama somente comandos previamente definidos, sem shell intermediário e com timeout.
6. O resultado é apresentado e os metadados da execução são gravados na auditoria local.

## Controles de segurança

- Allowlist: não há execução de comandos arbitrários fornecidos pelo usuário.
- Confirmação explícita antes de qualquer alteração.
- Privilégio mínimo e bloqueio quando a elevação é necessária.
- subprocess com shell=False, timeout e captura do código de saída.
- Limpeza de temporários limitada a arquivos regulares com mais de sete dias, preservando diretórios e links simbólicos.
- Limpeza de eventos exporta Application e Setup antes da exclusão; o log Security é preservado.
- Fechamento de processos solicita encerramento gracioso; não utiliza encerramento forçado.
- Download HTTPS sem execução automática, com limite de tamanho, validação de redirecionamento e SHA-256.
- Auditoria JSONL local sem registrar a saída potencialmente sensível dos comandos.

## Instalação

PowerShell:

~~~powershell
git clone https://github.com/nrdataanalysis-1908/TECH-DESK.git
cd TECH-DESK
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
~~~

## Execução

~~~powershell
python -m techdesk.cli
python -m techdesk.cli --diagnostics
python -m techdesk.cli --diagnostic usb
python -m techdesk.cli --diagnostic gpresult
python -m techdesk.cli --diagnostic performance
~~~

Abra o terminal como Administrador somente quando uma operação exigir elevação. O TECH DESK não tenta elevar privilégios silenciosamente.

## Qualidade

~~~powershell
pytest
ruff check .
~~~

O GitHub Actions executa testes e lint em Windows e Linux. CI verde não substitui validação funcional de cada rotina em uma máquina Windows real.

## Arquitetura atual

- Core Python: catálogo, políticas, validações, execução e auditoria.
- Adaptadores Windows: comandos nativos e PowerShell com argumentos fixos.
- Interface atual: CLI.
- Persistência: auditoria local JSONL.
- Desktop Tauri, API web, agente local autenticado e PostgreSQL centralizado: evolução planejada, ainda não implementada.

## Estado de validação

As rotinas possuem testes automatizados de catálogo, dispatch, cancelamento, privilégios e guardrails. A execução funcional em Windows real deve ser validada individualmente, especialmente operações que alteram serviços, logs, rede, aplicativos e arquivos.

## Licença

MIT. Consulte LICENSE.
