# TECH DESK

**NR TECH | IT MANAGEMENT & SUPPORT CENTER**

Central de execução e manutenção de endpoints Windows, com operações locais controladas, confirmação explícita, verificação de privilégios, timeout e trilha de auditoria.

## Foco operacional

O menu principal prioriza execução: são 18 operações administrativas e de manutenção contra 12 consultas rápidas. O catálogo de diagnósticos adicionais permanece acessível pela linha de comando.

### Operações implementadas

| Área | Operações |
|---|---|
| Manutenção | Limpeza de DNS, temporários antigos e cache de miniaturas; esvaziamento da Lixeira |
| Shell e dispositivos | Reinício do Explorer, Spooler e serviço de áudio; limpeza da fila de impressão |
| Rede | Renovação DHCP, limpeza de cache ARP e redefinição Winsock |
| Segurança | Atualização das assinaturas e verificação rápida do Microsoft Defender |
| Integridade | Criação de ponto de restauração, CHKDSK online, SFC e DISM |
| Atualizações | Reinício controlado do serviço Windows Update |

Ações com potencial de perda ou interrupção são identificadas por nível de risco e descrição antes da confirmação. Esvaziar a Lixeira e a fila de impressão são ações irreversíveis para os respectivos itens removidos. A redefinição Winsock pode exigir reinicialização do Windows.

### Consultas do menu

Resumo do sistema, CPU/memória, armazenamento, uptime, processos, serviços, configuração IP, DNS, adaptadores, conectividade, Firewall e Microsoft Defender.

O catálogo estendido de consultas Windows continua disponível com `--diagnostic`, por exemplo:

```powershell
python -m techdesk.cli --diagnostic usb
python -m techdesk.cli --diagnostic events
python -m techdesk.cli --diagnostic software
```

## Segurança e execução

- Catálogo fechado de operações: não há execução de comandos arbitrários fornecidos pelo usuário.
- Confirmação textual explícita antes de qualquer alteração.
- Verificação de elevação para operações administrativas.
- Execução sem shell intermediário (`shell=False`), com timeout e captura do código de saída.
- Prévia não destrutiva para a limpeza seletiva de temporários.
- Auditoria JSONL local com operação, horário, host e resultado, sem registrar a saída dos comandos.
- Saídas de utilitários nativos do Windows decodificadas pela página OEM do sistema.
- Testes automatizados para catálogo, dispatch, cancelamento e bloqueio por privilégio.

## Instalação — desenvolvimento

PowerShell:

```powershell
git clone https://github.com/nrdataanalysis-1908/TECH-DESK.git
cd TECH-DESK
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Execução

```powershell
python -m techdesk.cli
python -m techdesk.cli --diagnostics
python -m techdesk.cli --diagnostic dns
```

Abra o terminal como Administrador somente quando for executar operações que exigem elevação. O TECH DESK não tenta elevar privilégios silenciosamente.

## Qualidade

```powershell
pytest
ruff check .
```

O GitHub Actions executa os testes e o lint em Linux e Windows. A aprovação da CI não substitui a validação funcional das operações em uma máquina Windows real.

## Arquitetura

- Core: Python — catálogo, políticas, validações, execução e auditoria.
- Adaptadores Windows: utilitários nativos e PowerShell com comandos fixos.
- CLI: interface operacional atual.
- Desktop: Tauri — planejado.
- Web/API e agente local autenticado: planejados.
- Persistência centralizada: PostgreSQL — planejada; auditoria atual é local.

## Situação do produto

A CLI e o primeiro conjunto de operações locais estão implementados. Desktop, painel web, agente remoto, gestão centralizada, empacotamento e releases ainda não fazem parte da versão funcional atual.

O projeto só deve ser apresentado como validado em produção após CI verde e testes funcionais documentados em Windows 11, incluindo cenários de sucesso, cancelamento, falta de privilégio, timeout e falha do comando.

## Licença

MIT. Consulte [LICENSE](LICENSE).
