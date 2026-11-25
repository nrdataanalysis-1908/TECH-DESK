# TECH DESK Architecture

## 1. Objective

Build a modular IT support and management platform with distinct interfaces, a shared core, and traceable operational execution.

## 2. Componentes

### Core (Python)

Responsável por:
- configuração e parâmetros de execução;
- contratos e catálogo de operações;
- validação de entrada e preconditions;
- políticas de autorização;
- logging, auditoria e tratamento uniforme de erros.

### Windows Adapters (PowerShell)

Integrate with native Windows capabilities: inventory, services, processes, networking, events, storage, and maintenance. Adapters must not contain interface logic.

### Interfaces

- CLI: primeira interface funcional.
- Desktop: Tauri, para operação local.
- Web: Next.js, para gestão e visualização centralizadas.

Interfaces consume shared contracts; they do not duplicate business logic.

### Agente local e API

O agente local recebe solicitações autenticadas e executa exclusivamente operações previamente cadastradas. The web dashboard must never send free-form shell commands to the endpoint.

### Persistência

- SQLite: modo individual/local.
- PostgreSQL: modo centralizado e multiusuário.
- Logs operacionais: trilha de auditoria com retenção configurável.

## 3. Operation Workflow

1. The interface requests an operation identified by a key.
2. The core validates parameters, policy, and preconditions.
3. The user confirms when required by the risk level.
4. The authorized adapter executes the routine with a timeout.
5. The result is normalized and recorded.
6. The interface presents the status, evidence, and any corrective action.

## 4. Minimum Operation Contract

Each operation must declare:
- stable identifier;
- name and description;
- category;
- typed parameters;
- required privilege;
- risk classification;
- whether confirmation is required;
- preconditions;
- timeout;
- reversibility;
- structured result.

## 5. Principles

- low coupling and high cohesion;
- replaceable interfaces;
- idempotent operations whenever possible;
- explicit failures, never silent failures;
- telemetry without sensitive data;
- unit tests and adapter-level integration tests;
- compatibility documented by Windows version.

## 6. Technical Roadmap

1. Fundação Python e CLI.
2. Catálogo e contratos de operação.
3. Inventário e diagnóstico read-only.
4. Adaptadores de manutenção com confirmação.
5. Persistência e auditoria.
6. Desktop.
7. API, agente e painel web.
8. Assistência inteligente com explicabilidade e aprovação humana.
