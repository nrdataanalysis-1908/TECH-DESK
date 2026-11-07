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


## HTTPS download boundary

The support downloader accepts only absolute HTTPS URLs on the default port, without embedded credentials, surrounding whitespace or control characters. The same policy is enforced for every redirect and the final response URL.

If the server supplies Content-Length, it must be a decimal byte count within the 100 MiB limit and must match the number of bytes actually received. Incomplete or malformed responses are discarded; the tool never executes downloaded files.

Windows device basenames (for example CON, NUL, COM1 and LPT1) are prefixed before the file is saved, preventing reserved-name failures on Windows.
