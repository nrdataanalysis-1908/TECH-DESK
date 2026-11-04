# Arquitetura do TECH DESK

## 1. Objetivo

Construir uma plataforma modular de suporte e gestão de TI com interfaces distintas, núcleo compartilhado e execução operacional rastreável.

## 2. Componentes

### Core (Python)

Responsável por:
- configuração e parâmetros de execução;
- contratos e catálogo de operações;
- validação de entrada e pré-condições;
- políticas de autorização;
- logging, auditoria e tratamento uniforme de erros.

### Adaptadores Windows (PowerShell)

Integram-se aos recursos nativos do Windows: inventário, serviços, processos, rede, eventos, armazenamento e manutenção. Os adaptadores não devem conter regras de interface.

### Interfaces

- CLI: primeira interface funcional.
- Desktop: Tauri, para operação local.
- Web: Next.js, para gestão e visualização centralizadas.

As interfaces consomem contratos comuns; não duplicam regras de negócio.

### Agente local e API

O agente local recebe solicitações autenticadas e executa exclusivamente operações previamente cadastradas. O painel web nunca deve enviar comandos shell livres ao endpoint.

### Persistência

- SQLite: modo individual/local.
- PostgreSQL: modo centralizado e multiusuário.
- Logs operacionais: trilha de auditoria com retenção configurável.

## 3. Fluxo de uma operação

1. Interface solicita uma operação identificada por código.
2. Core valida parâmetros, política e pré-condições.
3. O usuário confirma quando o nível de risco exigir.
4. Adaptador autorizado executa a rotina com timeout.
5. Resultado é normalizado e registrado.
6. Interface apresenta estado, evidências e eventual ação corretiva.

## 4. Contrato mínimo de operação

Cada operação deverá declarar:
- identificador estável;
- nome e descrição;
- categoria;
- parâmetros tipados;
- privilégio requerido;
- classificação de risco;
- confirmação obrigatória ou não;
- pré-condições;
- timeout;
- possibilidade de reversão;
- resultado estruturado.

## 5. Princípios

- baixo acoplamento e alta coesão;
- interfaces substituíveis;
- operações idempotentes quando possível;
- falhas explícitas, nunca silenciosas;
- telemetria sem dados sensíveis;
- testes unitários e testes de integração por adaptador;
- compatibilidade documentada por versão do Windows.

## 6. Roadmap técnico

1. Fundação Python e CLI.
2. Catálogo e contratos de operação.
3. Inventário e diagnóstico read-only.
4. Adaptadores de manutenção com confirmação.
5. Persistência e auditoria.
6. Desktop.
7. API, agente e painel web.
8. Assistência inteligente com explicabilidade e aprovação humana.
