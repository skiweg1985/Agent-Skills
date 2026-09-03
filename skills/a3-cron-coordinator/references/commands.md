# A3 command lifecycle

These commands are explicit coordinator requests. They are not shell aliases and do not run automatically when the skill is installed.

## `A3 INIT [project]`

Initialize exactly one project without launching coding work. With no argument, derive the project from the current Git worktree and canonical `origin` URL. Ask only if that repository maps to multiple tracker projects or the current directory is not a Git worktree.

1. Read the selected repository's current working agreements and resolve its canonical repository URL, target branch, worktree convention, and whether it is non-production.
2. Read the tracker project, candidate issues, dependencies, active assignments/comments, open GitHub PRs, CI, worktrees, and existing workers.
3. Discover currently available agent identities from the local environment or configured tracker integrations. Do not infer a role from a display name. Create the local `team.json` scaffold and bind a role only from explicit user direction, current agent metadata, or an approved local policy.
4. Run `a3ctl.py init`. If repository+tracker identity already exists, report `DEDUPED`; do not create a second profile.
5. Save a secrets-free project profile and local team bindings. End with a report of safe candidates and write-set conflicts.

`INIT` must not create a Cron, dispatch a worker, change issue ownership, commit, push, merge, deploy, or write externally.

## `A3 START [project] [next N|ISSUE-KEY …]`

Only a trusted coordinator may perform this command.

1. Refresh all sources again; INIT data is not proof.
2. Select only unblocked issues with an accountable owner and non-overlapping write sets. `next N` means the safest dependency-respecting N, not simply the oldest N.
3. Acquire a durable lock before dispatching each worker. A duplicate lock means attach to/inspect the existing run; never start another.
4. Require one worktree per issue and an agent-authored tracker start comment; verify it independently.
5. Create one temporary 15-minute project supervisor Cron and persist its job ID locally with `a3ctl.py enable`.

## `A3 STATUS <project>`

Read-only. Refresh the tracker, GitHub PR/CI status, workers, and locks; compare a secrets-free snapshot. Report only material deltas, blockers, and the next safe action.

## `A3 STOP <project>`

Remove/pause only the project's future supervisor scheduling and call `a3ctl.py disable`. Preserve workers, worktrees, locks, and evidence. Never kill a worker or delete a worktree without a separate explicit instruction.

## `A3 CLOSE <project>`

After live verification that no worker, queued safe action, or review PR remains: remove the temporary Cron, release completed locks, retain the local profile/ledger, and report final evidence.
