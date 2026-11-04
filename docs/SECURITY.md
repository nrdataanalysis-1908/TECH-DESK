# Política de segurança

## Princípio fundamental

O TECH DESK administra endpoints. Uma falha de autorização ou validação pode causar indisponibilidade ou perda de dados. Segurança é requisito arquitetural, não funcionalidade acessória.

## Regras obrigatórias

- Não executar comandos arbitrários recebidos de interfaces remotas.
- Usar allowlist de operações e parâmetros tipados.
- Aplicar privilégio mínimo.
- Solicitar confirmação antes de excluir dados, alterar configurações, reiniciar serviços ou interromper conectividade.
- Validar sistema operacional, privilégios, caminhos e estado do recurso antes da execução.
- Definir timeout e tratar códigos de saída.
- Não armazenar senhas, tokens ou chaves em código, logs ou arquivos versionados.
- Sanitizar parâmetros e saídas antes de registrar.
- Registrar autor, operação, instante, resultado e identificador de correlação.
- Disponibilizar modo de simulação/preview sempre que tecnicamente possível.

## Classificação sugerida

| Nível | Natureza | Política |
|---|---|---|
| L0 | Consulta/read-only | Pode executar sem elevação |
| L1 | Alteração reversível de baixo impacto | Confirmar conforme contexto |
| L2 | Alteração relevante de sistema | Confirmação explícita e privilégio validado |
| L3 | Ação destrutiva ou disruptiva | Confirmação reforçada, auditoria e plano de reversão |

## Comunicação remota

- TLS obrigatório.
- Autenticação forte entre painel e agente.
- Tokens com escopo e expiração.
- Proteção contra replay e validação de origem.
- Rate limiting e trilha de auditoria.
- Nenhum endpoint de execução exposto publicamente sem autenticação.

## Reporte de vulnerabilidades

Não publique detalhes exploráveis de uma vulnerabilidade antes de coordenar sua correção. Abra uma issue privada ou utilize o canal de segurança configurado pelo mantenedor.
