# Local team configuration

`A3 SETUP` creates an editable, user-owned local team profile at:

```text
$XDG_CONFIG_HOME/a3-coordinator/team-profile.json
```

It is separate from project state. `A3 INIT` copies its desired role bindings into the selected project's local `team.json`; a coordinator must still check live worker availability before dispatching.

Initial scaffold:

```json
{
  "schemaVersion": 1,
  "configuredAt": "2026-01-01T00:00:00+00:00",
  "roles": {
    "coordinator": null,
    "support": null,
    "frontend": null,
    "backendSecurity": null,
    "review": null
  }
}
```

## Guided setup and overrides

- Run `a3ctl.py setup` to create the scaffold without replacing existing choices.
- Supply an intentional override with `--role ROLE=AGENT`, for example `--role frontend=frontend-agent`.
- Agent identifiers are local, non-secret labels. Keep hostnames, account names, tokens, emails, models, ports, connection paths, and credentials in private local policy rather than in this file.
- `A3 SETUP` discovers safe facts first. If a required access, approval, changed host key, or role decision cannot be inferred safely, it must tell the user what was checked, why the gap matters, and the smallest next action.

## Readiness evidence

`A3 SETUP` also creates this state file when absent:

```text
$XDG_STATE_HOME/a3-coordinator/worker-readiness.json
```

It may contain only secrets-free observations such as a worker label, tool version, successful authentication/readiness state, and timestamp. It is never proof forever: `A3 START` must perform a fresh preflight on the actual worker execution environment. A local coordinator's CLI output is not evidence about a remote worker.

## Binding roles safely

- Query live availability before assigning work. A prior role binding is a hint, not evidence that a worker is free.
- Preserve one accountable owner per issue. A role entry does not authorize that worker to start its own A3 wave.
- If no local policy or current metadata resolves a role, leave it `null` and ask the coordinator/user. Never guess from a display name.
- A local coordinator may use a private policy to resolve remote execution details. That policy is not copied into this public skill.
