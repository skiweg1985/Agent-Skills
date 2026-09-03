---
name: a3-cron-coordinator
description: Explicitly opt-in, GitHub-first Cron coordinator for a non-production project delivery wave. Use only when a user or trusted coordinator explicitly says `A3 INIT`, `A3 START`, `A3 STATUS`, `A3 STOP`, or `A3 CLOSE`; never load or activate this skill merely because it is installed on a coding-agent host.
---

# A3 Cron Coordinator

## Opt-in boundary — mandatory

This public skill is **inert by default**. Installation, repository clone, agent startup, task assignment, Linear assignment, a webhook, or a Cron tick must never activate it.

Act only after an explicit command from a user or trusted coordinator beginning with one of:

```text
A3 INIT [project]
A3 START [project] [next N|ISSUE-KEY …]
A3 STATUS [project]
A3 STOP [project]
A3 CLOSE [project]
```

A coding worker must never invoke `A3 INIT` or `A3 START` itself, create a supervisor Cron, change another project's A3 state, or dispatch another worker. A worker receives only its bounded issue prompt from an already active coordinator.

## Local-only project state

The public repository holds reusable logic only. `A3 INIT` creates all project-specific state locally, never in this skill repository:

```text
$XDG_STATE_HOME/a3-coordinator/projects/<project-slug>/
├── profile.json       # repository/tracker metadata; no credentials
├── team.json          # locally resolved agent-role bindings
├── activation.json    # initialized/enabled state and Cron job ID
└── runtime/           # locks and secrets-free snapshots
```

Default `$XDG_STATE_HOME` is `$HOME/.local/state`. Override the root only with `A3_COORDINATION_ROOT`.

Read `references/commands.md` for the lifecycle and `references/local-team-config.md` for the local agent discovery rules.

## GitHub-first default

Use GitHub (`gh`, pull requests, GitHub Actions) unless the selected project is explicitly identified as another SCM. Never infer a host, project URL, or API from this skill.

## A3 safety limits

A3 may coordinate bounded non-production implementation, validation, commit, push, review, and owner merge only where current user direction, repository rules, and project policy allow it. It never permits deployment, production writes, credential exposure, destructive operations, or scope expansion.

Before dispatch or merge, refresh the tracker, repository, PR/CI state, active worktrees, and locks. A repeated wake must return an existing run rather than dispatch the same issue twice.

## Core invariants

- One accountable owner, one worktree, and one durable lock per issue.
- Never overlap active write sets, API contracts, migrations, or shared interface decisions.
- Never treat a worker's claim as evidence; independently read the live tracker, repository, PR, CI, and worktree state.
- `UNKNOWN`, `DIRTY`, `CONFLICTING`, changed PR heads, missing evidence, or stale CI are hard stops for merge.
- Report only material changes. Store snapshots without secrets.

## Local helpers

```bash
python3 scripts/a3ctl.py init --project <slug> --repo <canonical-repository-url> --tracker <tracker-project>
python3 scripts/a3ctl.py status --project <slug>
python3 scripts/a3ctl.py enable --project <slug> --cron-job-id <job-id>
python3 scripts/a3ctl.py disable --project <slug>
python3 scripts/a3_state.py --state-root "$XDG_STATE_HOME/a3-coordinator/projects/<slug>/runtime" acquire \
  --project <slug> --issue <ISSUE> --agent <agent> --session <session> --revision <revision>
```

`a3ctl.py init` is idempotent: it deduplicates on canonical repository URL plus tracker identity. A mismatch stops rather than overwriting another project.

## Cron lifecycle

`A3 INIT` without an argument derives the local project identity from the current Git worktree and canonical `origin` URL. It asks only when multiple tracker projects match that repository. Only an explicit `A3 START` run from the coordinator may create one temporary `a3-supervisor-<slug>` job, usually every 15 minutes. Attach this skill and use the selected project as workdir. Persist its job ID through `a3ctl.py enable`. `A3 STOP` removes future scheduling but does not kill workers; `A3 CLOSE` removes the job only after live verification that no work/review action remains.
