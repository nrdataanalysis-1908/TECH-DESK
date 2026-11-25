# PowerShell Adapters

Administrative routines will be implemented here as modular components.

## Script Requirements

- Validate the Windows version and required privileges.
- Accept explicit, strongly typed parameters.
- Use `SupportsShouldProcess` and `-WhatIf` where applicable.
- Return predictable exit codes.
- Apply timeouts and exception handling.
- Log start time, end time, duration, and result.
- Never embed credentials.
- Never execute free-form text as a command.
- Document impact, reversibility, and preconditions.

No destructive routine is enabled at this initial stage.
