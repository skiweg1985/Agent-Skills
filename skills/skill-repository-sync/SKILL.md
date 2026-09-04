---
name: skill-repository-sync
description: Safely check for and install updates from the shared skiweg1985/Agent-Skills GitHub repository on an agent host, and diagnose a host whose skills are missing or stale. Use when asked to update, refresh, pull, or synchronize the shared skills, when a skill that should exist cannot be found, or when a host's role assignment is in question.
---

# Sync the Shared Skill Repository

Use the host-installed updater rather than running Git commands against the clone
yourself:

```bash
$HOME/.local/bin/update-agent-skills
```

The updater:

1. locks against concurrent updates;
2. resolves this host's roles from `~/.config/agent-skills/host.conf`, or `AGENT_SKILLS_ROLES` if set;
3. verifies the clone uses the expected GitHub remote and is not dirty;
4. fetches and permits only a fast-forward update;
5. rebuilds the delivery directory from the skills whose groups match this host's roles;
6. validates every skill in the clone and everything delivered;
7. rolls back and records the failure if installation or validation fails.

Report whether the repository was already current or name the old and new commit
IDs. On a dirty clone, remote mismatch, failed install, or validation failure,
stop and report the blocker. Do not repair it with `git reset --hard`, change the
remote, reinstall the updater, edit the clone, or modify cron unless the user
explicitly authorizes that maintenance.

## Clone and delivery directory are not the same thing

The clone at `~/.local/share/agent-skills` holds every skill. The delivery
directory at `~/.agents/skills` is **generated** and holds only what this host's
roles selected. Never add a skill by copying it into the delivery directory: the
next sync rebuilds that directory and the copy disappears. Change what a host
receives by changing its roles, or the skill's groups in the manifest.

A skill present in the clone but absent from the manifest aborts the sync. That
is deliberate — assign it a group rather than working around the error.

## When a skill is missing, read the status record first

Under cron a failing sync is silent, so a missing skill and a stale host look
identical from the outside. **Whenever you are asked about installed skills, or a
skill that should exist cannot be found, read this before concluding anything:**

```bash
cat "${XDG_STATE_HOME:-$HOME/.local/state}/agent-skills/sync-status.json"
```

- `outcome` is `ok` or `failed`, with `failureReason` when it failed.
- `lastSuccessAt` is the last time the delivery directory was rebuilt
  successfully. Older than roughly twice the cron interval means the sync has
  been failing for a while, whatever the last run reported.
- `roles` and `skills` say what this host was supposed to receive. A skill absent
  from that list is not missing — it was never selected for this host.

Distinguish the three cases in your report: the sync is failing, the host's roles
do not include the skill, or the skill does not exist in the repository at all.

## Where each agent looks

The delivery directory serves all four agents. Codex and OpenCode read
`~/.agents/skills` natively, Claude Code through the `~/.claude/skills` symlink,
and Hermes through `skills.external_dirs` in `~/.hermes/config.yaml`. Updating
the delivery directory therefore updates every agent on the host at once.

For installation, roles, cron, and failure-handling details, read
[the automatic-update reference](references/automatic-updates.md).
