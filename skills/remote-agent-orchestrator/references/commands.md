# Wave lifecycle

These are explicit coordinator requests. They are not shell aliases and none of
them runs because the skill is installed.

## `WAVE SETUP [--role ROLE=AGENT …]`

Create or review the local foundation without touching any project.

1. Confirm `linear-coordinate-agents` and `cost-aware-agent-routing` are present.
   If either is missing, report it and stop — the orchestrator delegates autonomy
   and routing to them and must not substitute its own judgement.
2. Run `orchestratorctl.py setup`. It creates this installation's coordinator
   identity on first run and preserves every existing choice afterwards.
3. Ask for the reachability of each agent that is missing one: host, user,
   working directory, and the exact command that starts it. Record it with
   `setup --agent`. Public-key authentication is expected to be provisioned
   already; verify it, never create it.
4. Discover every safe fact yourself. For a remote worker, check the actual
   execution host before concluding that a CLI, an authentication or an MCP is
   missing — a result from the coordinator's own machine says nothing about it.
5. Report the identity, configured roles, registered agents, roles still bound to
   an unregistered agent, and the next safe action.

`SETUP` must not start a worker, create a worktree, take a lock, schedule a job,
write to a tracker or repository, or create any network or credential
configuration.

## `WAVE INIT [project]`

Initialize exactly one project without launching work. With no argument, derive
it from the current worktree and its canonical `origin` URL. Ask only when that
repository maps to several tracker projects or the directory is not a worktree.

1. Read the repository's working agreements: canonical URL, target branch,
   worktree convention, and whether it is non-production.
2. Read the tracker project, candidate issues and their declared write sets,
   dependencies, current assignments, open pull requests, CI, worktrees and any
   running workers.
3. Load role bindings from the local profile and confirm each bound agent has a
   registry entry. A binding is an intention, not evidence that a worker is free.
4. Run `orchestratorctl.py project init`. The project key is derived from
   repository and tracker, so a second run under a different label reports
   `deduped` rather than creating a rival project.
5. Report safe candidates, issues lacking a declared write set, and write-set
   conflicts.

`INIT` must not create a cron job, dispatch a worker, change issue ownership,
commit, push, merge, deploy, or write anything externally.

## `WAVE START <project> <milestone|issue …>`

Only on an explicit human go-ahead, which authorizes the **scope**, not one
dispatch.

1. Refresh every source again. `SETUP` and `INIT` data are not proof.
2. Resolve the scope against the tracker and record it. An issue outside the scope
   is never dispatched, whatever its state.
3. Run a fresh preflight on each candidate's **actual execution host**. Record only
   secrets-free evidence. Ask the user only about a real access, approval or
   assignment gap; when nobody is present, the question goes into the report.
4. Select issues that are unblocked, have an accountable owner, declare a write
   set, and do not overlap another running write set. Stay within `maxWorkers`.
5. Take a lock for each issue before dispatching. An existing live lock means
   attach to that run and inspect it; never start a second.
6. Dispatch using the agent's registered invocation template. Require one worktree
   per issue, created by the worker, and an agent-authored tracker start comment.
   Verify both independently — the worker saying so is not evidence.
7. Create one temporary supervisor cron job and persist its id with `wave enable`.

A missing registry entry or an unreachable host is a hard stop for that issue:
do not dispatch, release its lock, report it. Never substitute another agent.

## `WAVE STATUS [project]`

Read-only. With no argument, list every known project, its wave state, registered
agents and open locks — this is how a new session finds existing work.

With a project, refresh the tracker, pull request and CI state, real worker
liveness and locks, then compare against the stored snapshot and report only
material deltas, blockers and the next safe action.

## Supervisor tick

Each scheduled run supervises; it does not widen the wave.

1. Refresh state and check liveness on each worker host over SSH.
2. Renew the lease of every worker confirmed to be still running. Leave the rest
   to expire, and record that they did.
3. For finished work — pull request open, process ended — request review from an
   agent other than the implementer.
4. For reviewed work, check the diff against the declared write set, then merge.
   Two finished pull requests that collide merge in completion order; the later
   one rebases, and a non-trivial rebase becomes a blocked issue back to a worker.
5. Dispatch the next issue **inside the authorized scope** when a slot frees.
6. When the scope holds no unfinished work, close the wave: remove the cron job,
   release completed locks, write the final report.

## `WAVE STOP <project>`

Stop future scheduling and call `wave disable`. Preserve workers, worktrees, locks
and evidence. Never kill a worker or delete a worktree without a separate explicit
instruction.

## `WAVE CLOSE <project>`

After verifying live that no worker, queued action or open review remains: remove
the cron job, release completed locks, keep the local profile and ledger, and
report the final evidence.
