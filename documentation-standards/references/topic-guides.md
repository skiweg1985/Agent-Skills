# Topic Guides and Sources of Truth

Human-maintained documentation should explain tasks, boundaries, tradeoffs, and
recovery. Exact lookup data should stay with the machine-readable source that
owns it.

## Source-of-truth matrix

| Information | Authoritative source | Human documentation should... |
|---|---|---|
| CLI flags and defaults | The tool's `--help` output or generated CLI reference | Explain common workflows and link to the exact reference. |
| API methods, fields, and schemas | OpenAPI or another generated contract | Explain authentication, task-level examples, compatibility, and important failure behavior. |
| Configuration fields and defaults | A validated schema and maintained example configuration | Explain intent, safe choices, precedence, and operational consequences. |
| Internal classes, files, and functions | Code, types, names, and tests | Explain only non-obvious boundaries or extension contracts. |
| Development history | Git, pull requests, releases, or a maintained changelog | Describe current behavior rather than retelling implementation history. |

Put generated lookup material in the repository's established reference
location; for a new project, prefer `docs/reference/`. Avoid copying generated
facts into prose unless the copy is necessary to complete a task and has a
clear maintenance owner.

## Configuration

Describe how an operator selects and verifies a configuration, including
precedence, security implications, restart or rollout effects, and a minimal
working example. Link to the schema for the complete field list.

## APIs and CLIs

Organize examples around reader goals rather than endpoint or flag catalogs.
Show authentication, a representative request or command, the expected result,
and important failure behavior when those details are not already obvious from
the generated reference.

## Operations and observability

Document the lifecycle actions that actually exist: installation, update,
backup, restore, rollback, recovery, and diagnosis. For each supported action,
state prerequisites, the command or procedure, how to recognize success, and a
safe recovery path when failure is realistic.

Connect observability to decisions. Describe what healthy looks like, which
signal identifies a meaningful failure, and what the operator should do next.
Avoid inventories of every metric, log field, or dashboard when the monitoring
system already provides that reference.

## Security

Explain trust boundaries and operator obligations: authentication,
authorization, credential and certificate custody, network exposure, least
privilege, rotation, and auditability. Include only controls and threats that
apply to the system; link to generated configuration reference for exact
fields.

## Troubleshooting

Write entries for failures that are realistic, costly, or recurring. Each entry
should identify the symptom, the quickest discriminating check, the likely
cause, the recovery action, and when to escalate. Prefer evidence-producing
commands over speculative lists of possible causes.

## UI guidance and screenshots

Document stable user tasks and decision points. Use screenshots only when
spatial context materially helps and there is a realistic process for keeping
them current. A stable label, route, or short procedure is usually cheaper to
maintain than a screenshot of routine UI detail.
