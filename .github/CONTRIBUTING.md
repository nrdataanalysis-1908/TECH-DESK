# Contribuindo com o TECH DESK

TECH DESK prioritizes operational security, predictability, and traceability.

## Contribution Workflow

1. Crie uma branch a partir de `main` usando um prefixo como `feat/`, `fix/`, `docs/` ou `chore/`.
2. Keep each change focused and document operational impact.
3. Execute `pytest` e `ruff check .`.
4. Open a Pull Request against `main` and complete the provided template.
5. Wait for CI to run on Windows and Ubuntu, and resolve any failures before merging.

## Security Requirements

- Do not introduce arbitrary command execution.
- Do not use `shell=True` in subprocesses.
- Preserve allowlists, explicit confirmations, timeouts, and privilege checks.
- Never log tokens, credentials, personal data, or potentially sensitive output.
- Every operation that changes the system must document preconditions, effects, and failure strategy.

## Releases

Releases are published through SemVer tags in the `vMAJOR.MINOR.PATCH` format. Release automation runs tests and linting, packages the Python distribution, and attaches artifacts to the GitHub Release. Do not publish a stable version without functional validation appropriate to the release scope.
