# Local team configuration

`A3 INIT` creates `team.json` locally for the selected project. It prevents private role mappings, host names, model choices, and availability details from entering the public skill repository.

Initial scaffold:

```json
{
  "schemaVersion": 1,
  "project": "example-project",
  "resolvedAt": null,
  "roles": {
    "coordinator": null,
    "support": null,
    "frontend": null,
    "backendSecurity": null,
    "review": null
  }
}
```

## Binding roles safely

- Query live availability before assigning work. A prior role binding is a hint, not evidence that a worker is free.
- Bind only a non-secret agent identifier and intended responsibility. Do not store hostnames, tokens, email addresses, model credentials, or internal URLs.
- Preserve one accountable owner per issue. A role entry does not authorize that worker to start its own A3 wave.
- If no local policy or current metadata resolves a role, leave it `null` and ask the coordinator/user. Never guess from a display name.
- A local coordinator may use a private policy to populate this file; that private policy is not copied into this public skill.
