# TECH DESK Architecture

## 1. Objective

Build a modular IT support and management platform with distinct interfaces, a shared core, and traceable operational execution.

## 2. Components

### Core (Python)

Responsible for:
- configuration and runtime parameters;
- operation contracts and catalog;
- input validation and preconditions;
- authorization policies;
- logging, auditing, and consistent error handling.

### Windows Adapters (PowerShell)

Integrate with native Windows capabilities: inventory, services, processes, networking, events, storage, and maintenance. Adapters must not contain interface logic.

### Interfaces

- CLI: primeira interface funcional.
- Desktop: Tauri for local operations.
- Web: Next.js for centralized management and visualization.

Interfaces consume shared contracts; they do not duplicate business logic.

### Local Agent and API

The local agent receives authenticated requests and executes only pre-registered operations. The web dashboard must never send free-form shell commands to the endpoint.

### Persistence

- SQLite: single-user/local mode.
- PostgreSQL: centralized, multi-user mode.
- Operational logs: audit trail with configurable retention.

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

1. Python and CLI foundation.
2. Operation catalog and contracts.
3. Inventory and read-only diagnostics.
4. Maintenance adapters with confirmation.
5. Persistence and auditing.
6. Desktop.
7. API, agente e painel web.
8. Intelligent assistance with explainability and human approval.
