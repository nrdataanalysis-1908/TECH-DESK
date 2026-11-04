# TECH DESK

**NR TECH | IT MANAGEMENT & SUPPORT CENTER**

Plataforma modular de suporte e gestão de TI para diagnóstico, manutenção, monitoramento, automação e segurança de endpoints Windows.

<p align="center">
  <strong>DIAGNÓSTICO · MONITORAMENTO · MANUTENÇÃO · AUTOMAÇÃO · SEGURANÇA</strong>
</p>

## Visão do produto

O TECH DESK reúne três interfaces sobre um núcleo compartilhado:

- **Terminal:** operações administrativas por CLI.
- **Desktop:** aplicação local para técnicos e administradores.
- **Web:** painel central de monitoramento e gestão, integrado a agentes locais autenticados.

O objetivo é transformar rotinas dispersas de suporte em operações padronizadas, rastreáveis, seguras e extensíveis.

## Capacidades planejadas

| Domínio | Recursos |
|---|---|
| Diagnóstico | Sistema operacional, hardware, processos, serviços e eventos |
| Manutenção | Temporários, integridade do Windows, disco e Windows Update |
| Rede | Interfaces, IP, DNS, conectividade e diagnóstico |
| Segurança | Estado de proteção, políticas, auditoria e verificações |
| Gestão | Inventário, histórico de operações e relatórios |
| Automação | Catálogo de tarefas administrativas com validações |
| Inteligência | Assistência contextual para análise e recomendação |

> As capacidades acima representam o escopo do produto. Cada módulo será identificado como disponível somente após implementação e testes.

## Arquitetura

- **Core:** Python — configuração, contratos, validação, políticas e logging.
- **Windows adapters:** PowerShell — integração com recursos nativos do sistema.
- **Desktop:** Tauri — interface local.
- **Web:** Next.js — painel de gestão.
- **Agent/API:** comunicação autenticada entre painel e endpoints.
- **Storage:** SQLite para execução local; PostgreSQL para cenários centralizados.

Consulte [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Estrutura atual

```text
TECH-DESK/
├── docs/
│   ├── ARCHITECTURE.md
│   └── SECURITY.md
├── scripts/
│   └── powershell/
│       └── README.md
├── src/
│   └── techdesk/
│       ├── core/
│       │   ├── config.py
│       │   └── logging_config.py
│       ├── __init__.py
│       └── cli.py
├── tests/
│   └── test_config.py
├── .gitignore
├── LICENSE
└── pyproject.toml
```

## Requisitos

- Python 3.11+
- Windows 10/11 para os módulos de administração do sistema
- PowerShell 5.1+ (módulos Windows) ou PowerShell 7+, conforme o adaptador

## Instalação — desenvolvimento

No PowerShell:

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
techdesk
```

Ou, sem instalar o entry point:

```powershell
$env:PYTHONPATH = "src"
python -m techdesk.cli
```

## Testes e qualidade

```powershell
pytest
ruff check .
```

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

- [x] Criar repositório e fundação inicial
- [x] Configuração e logging do núcleo
- [x] CLI inicial
- [ ] Catálogo de operações e contratos
- [ ] Inventário de hardware e software
- [ ] Diagnóstico de rede e sistema
- [ ] Rotinas de manutenção Windows
- [ ] Auditoria persistente e histórico
- [ ] Desktop Tauri
- [ ] API e agente local autenticado
- [ ] Painel Web Next.js
- [ ] Assistente inteligente
- [ ] CI, empacotamento e releases

## Licença

Distribuído sob a licença MIT. Consulte [LICENSE](LICENSE).
