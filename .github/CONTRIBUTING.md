# Contribuindo com o TECH DESK

O TECH DESK prioriza segurança operacional, previsibilidade e rastreabilidade.

## Fluxo de contribuição

1. Crie uma branch a partir de `main` usando um prefixo como `feat/`, `fix/`, `docs/` ou `chore/`.
2. Mantenha cada alteração focada e documente impactos operacionais.
3. Execute `pytest` e `ruff check .`.
4. Abra um Pull Request para `main`, preenchendo o modelo disponibilizado.
5. Aguarde a execução do CI em Windows e Ubuntu e resolva eventuais falhas antes do merge.

## Requisitos de segurança

- Não introduza execução arbitrária de comandos.
- Não utilize `shell=True` em subprocessos.
- Preserve allowlists, confirmações explícitas, timeouts e validações de privilégio.
- Não registre tokens, credenciais, dados pessoais ou saídas potencialmente sensíveis.
- Toda operação que altere o sistema deve documentar pré-condições, efeitos e estratégia de falha.

## Releases

Versões são publicadas por tags SemVer no formato `vMAJOR.MINOR.PATCH`. A automação de release executa testes, lint, empacota a distribuição Python e anexa os artefatos à GitHub Release. Não publique uma versão estável sem validação funcional compatível com o escopo da versão.
