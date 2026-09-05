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
      "invocation": "codex exec {prompt}",
      "trackerIdentity": {"provider": "linear", "displayName": "worker1"}
    }
  }
}
```

Record it with:

```bash
python3 scripts/orchestratorctl.py setup --agent worker-1 \
  --host build-1.example --user agent --workdir /srv/work \
  --invocation 'codex exec {prompt}' \
  --tracker-identity linear:worker1
```

**The tracker identity says who this agent is when somebody addresses it.**
Workers talk to each other on the issues, and a supervisor routing a question to
the agent whose *name resembles* the one addressed is guessing — the same guess
the invocation template exists to prevent. Record `provider` and the display name
exactly as the tracker spells it, optionally the stable user id for audit. Two
agents may not claim one identity, and a name no entry claims is reported rather
than routed. The field is optional: an agent without one is dispatchable for work
and unreachable for questions, which is worth knowing before a wave starts. It
carries no secret, and `setup` keeps it when a later run corrects a host or a
port, because who an agent is in the tracker does not change with how it is
reached.

**Never store credentials here.** No key, no passphrase, no token. Public-key
authentication is provisioned on the hosts themselves; the orchestrator verifies
that it works and never creates or transports it. A field whose name suggests a
secret is rejected outright. The registry says where an agent lives, not how to
break in.

**The invocation template is required and never inferred.** Coding agents differ
in how they take a one-shot prompt, and guessing one from an agent's name is the
kind of inference this skill forbids everywhere else.

**Use it verbatim at dispatch: substitute `{prompt}`, change nothing else.** Two
failures follow from editing it, and both are quiet. A bare command name instead
of the absolute path fails because a non-interactive shell carries a minimal
`PATH` and will not find an agent installed under a home directory. An added
sandbox or approval flag can restrict the writable area to the repository rather
than the worktree and unshare the network, so start-up writes block, tests hang at
zero CPU, and finished work cannot be pushed. Record the working command in the
registry and let every dispatch read it from there.

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
