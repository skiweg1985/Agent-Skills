# Agent registry and roles

Two files, two different questions. Keeping them apart is what lets a wave survive
a new session: intent and reachability are durable, observation is not.

| File | Question | Lifetime |
| --- | --- | --- |
| `team-profile.json` | Which role should which agent have? | durable, hand-editable |
| `agents.json` | How is that agent reached and started? | durable, hand-editable |
| `worker-readiness.json` | Did it answer last time? | transient, never proof |

All three live under the local roots, never in this repository.

## Reachability

```json
{
  "schemaVersion": 1,
  "agents": {
    "worker-1": {
      "transport": "ssh",
      "host": "build-1.example",
      "user": "agent",
      "workdir": "/srv/work",
      "branchPrefix": "wave/",
      "invocation": "codex exec {prompt}"
    }
  }
}
```

Record it with:

```bash
python3 scripts/orchestratorctl.py setup --agent worker-1 \
  --host build-1.example --user agent --workdir /srv/work \
  --invocation 'codex exec {prompt}'
```

**Never store credentials here.** No key, no passphrase, no token. Public-key
authentication is provisioned on the hosts themselves; the orchestrator verifies
that it works and never creates or transports it. A field whose name suggests a
secret is rejected outright. The registry says where an agent lives, not how to
break in.

**The invocation template is required and never inferred.** Coding agents differ
in how they take a one-shot prompt, and guessing one from an agent's name is the
kind of inference this skill forbids everywhere else.

Everything else about reaching a host — a jump host, a port policy, an SSH config
alias — belongs in the host's own SSH configuration, referenced by name, not
copied here.

## Roles

```json
{
  "schemaVersion": 1,
  "roles": {
    "coordinator": null,
    "support": null,
    "frontend": null,
    "backendSecurity": null,
    "review": null
  }
}
```

- Set a role deliberately with `setup --role frontend=worker-1`.
- Agent identifiers are local, non-secret labels.
- A role bound to an agent with no registry entry is reported by `setup`; it is
  not dispatchable.
- Query live availability before assigning work. A binding is a hint, never
  evidence that a worker is free.
- Keep one accountable owner per issue. A role entry does not authorize that
  worker to start a wave of its own.
- If nothing resolves a role, leave it `null` and ask. Never guess from a display
  name.

## Readiness evidence

`worker-readiness.json` may hold only secrets-free observations: a worker label, a
tool version, a successful readiness check, a timestamp. It is never proof for
later — `WAVE START` performs a fresh preflight on the actual execution host every
time. It exists to make drift visible and to report from, not to skip a check.
