# Security Policy

## Core Principle

TECH DESK manages endpoints. An authorization or validation failure can cause downtime or data loss. Security is an architectural requirement, not an ancillary feature.

## Mandatory Rules

- Never execute arbitrary commands received from remote interfaces.
- Use an operation allowlist and typed parameters.
- Enforce least privilege.
- Require confirmation before deleting data, changing settings, restarting services, or interrupting connectivity.
- Validate the operating system, privileges, paths, and resource state before execution.
- Set timeouts and handle exit codes.
- Never store passwords, tokens, or keys in code, logs, or version-controlled files.
- Sanitize parameters and output before logging.
- Record the actor, operation, timestamp, result, and correlation identifier.
- Provide a simulation/preview mode whenever technically feasible.

## Suggested Classification

| Level | Nature | Policy |
|---|---|---|
| L0 | Read-only query | May run without elevation |
| L1 | Low-impact reversible change | Confirm as appropriate |
| L2 | Significant system change | Explicit confirmation and validated privileges |
| L3 | Destructive or disruptive action | Strong confirmation, audit trail, and rollback plan |

## Remote Communication

- TLS is mandatory.
- Strong authentication between the dashboard and agent.
- Scoped tokens with expiration.
- Replay protection and origin validation.
- Rate limiting and an audit trail.
- No execution endpoint may be publicly exposed without authentication.

## Vulnerability Reporting

Do not publish exploitable vulnerability details before coordinating a fix. Open a private issue or use the security channel configured by the maintainer.


## HTTPS download boundary

The support downloader accepts only absolute HTTPS URLs on the default port, without embedded credentials, surrounding whitespace or control characters. The same policy is enforced for every redirect and the final response URL.

If the server supplies Content-Length, it must be a decimal byte count within the 100 MiB limit and must match the number of bytes actually received. Incomplete or malformed responses are discarded; the tool never executes downloaded files.

Windows device basenames (for example CON, NUL, COM1 and LPT1) are prefixed before the file is saved, preventing reserved-name failures on Windows.
