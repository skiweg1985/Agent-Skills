# Wave lifecycle

These are explicit coordinator requests. They are not shell aliases and none of
them runs because the skill is installed.

## `WAVE SETUP [--role ROLE=AGENT …]`

Create or review the local foundation without touching any project.

1. Confirm `linear-coordinate-agents` and `cost-aware-agent-routing` are present.
   If either is missing, report it and stop — the orchestrator delegates autonomy
   and routing to them and must not substitute its own judgement.
2. Run `orchestratorctl.py setup` (resolve its path as the skill file describes). It creates this installation's coordinator
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
3. Run a fresh preflight on each candidate's **actual execution host**, from the
   same kind of shell the work will run in. Confirm three things, not one: the
   agent CLI answers, the worker can write inside its worktree, and it can reach
   the network. A sandbox derived from the repository rather than the worktree
   makes writes block silently and removes the network, so an agent that passes a
   reachability check can still be unable to test or push. Record only
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

A human exception for a specific breach is granted as a comment on the issue,
where the coordinator verifies it independently and the next agent can still find
it. It covers that one merge only.

A missing registry entry, an unreachable host, or a worktree the worker cannot
write in is a hard stop for that issue:
do not dispatch, release its lock, report it. Never substitute another agent.

## `WAVE NOTIFY [project] <level>`

Change what reaches the delivery channel without touching the tracker record.

```bash
python3 "$ORCH" notify show --project <key>          # effective level and its source
python3 "$ORCH" notify set --level blocker           # host default
python3 "$ORCH" notify set --project <key> --level progress
python3 "$ORCH" notify set --project <key> --wave --level progress   # this wave only
python3 "$ORCH" notify set --quiet-hours 22:00-07:00 # host-wide; "none" removes it
```

Levels are a subscription, not a volume dial: `blocker` ⊂ `milestone` ⊂ `progress`.
No level silences a change to the supervision itself — a paused, disabled or
removed supervisor, or a closed wave, is always reported.
Quiet hours are a host setting and let only blockers through; the rest is held and
summarised afterwards. Report the effective level and where it came from, so the
user can see whether a wave override is still in force.

## `WAVE STATUS [project]`

Read-only. With no argument, list every known project, its wave state, registered
agents and open locks — this is how a new session finds existing work.

With a project, refresh the tracker, pull request and CI state, real worker
liveness and locks, then compare against the stored snapshot and report only
material deltas, blockers and the next safe action. Store the refreshed state as
the new snapshot afterwards, so the next reader compares against what you saw and
not against something older.

Check the supervisor itself, not merely its recorded id: ask the scheduler whether
that job exists, is enabled and has a next run due. An active wave without a live
supervisor is a blocker — locks stop being renewed, a finished worker goes
unnoticed, and the wave never closes. Report it and name the job id.

## Supervisor tick

Each scheduled run supervises; it does not widen the wave.

1. Refresh state and check liveness on each worker host over SSH. **Store the
   refreshed state as a snapshot before deciding anything** — the delta rule below
   compares against it, and a tick that stores none has nothing to compare against
   and will restate the whole world every time:
   ```bash
   python3 "$ORCH" snapshot --project <key> --input <refreshed-state.json> --summary "<what changed>"
   ```
   Its `changed` field answers, in one word, whether this tick has anything to say.
2. Renew the lease of every worker confirmed to be still running. Leave the rest
   to expire, and record that they did. A live process is not progress: when a
   worker has run far longer than the work should take with no new commit, report
   that as a diagnosis instead of renewing forever.
3. Decide what a finished process left behind before doing anything else. A pull
   request means done; commits without one mean stalled, so re-dispatch that agent
   to publish and keep its lock; neither means dead, so release the lock now
   instead of waiting out the lease, and say why.
4. For work that is done, request review from an agent other than the implementer,
   and require it to publish its own findings: a pull request review, or a tracker
   comment under its own identity carrying its session identifier. If no other
   agent is available or preflight-ready, the issue is **blocked** — report it and
   move on to the next candidate. Never review your own dispatch to keep the wave
   moving; a coordinator that reviews is no longer an independent check.
5. For reviewed work, **first read that record back**. No published review means
   the work is not reviewed, whatever the reviewer reported to you; do not merge,
   and say what is missing. Then check the diff against the declared write set.
   Files beyond it that overlap another active worker are a hard stop; files that
   overlap nobody and are covered by the review are recorded as a deviation on the
   issue and merged. Say which of the two you found, and name the files. Record non-blocking findings as their own tracker items with an owner
   before closing, rather than listing them in the closing report.
   Two finished pull requests that collide merge in completion order; the later
   one rebases, and a non-trivial rebase becomes a blocked issue back to a worker.
6. Dispatch the next issue **inside the authorized scope** when a slot frees.
7. Re-examine every standing blocker against the rules of *this* run before
   treating it as still blocking. A blocker recorded under an earlier rule is a
   decision, not a fact, and decisions are re-made when the rule changes.
8. Close the wave only when every issue in scope is merged or blocked. An open
   pull request, a review not yet published, or a stalled worker all count as
   unfinished. Then remove the cron job, release completed locks, and write the
   final report — and report the closure itself, because it ends the supervision.

Work through the steps above before consulting the snapshot. `changed: false`
says the world looks as it did, not that there is nothing left to do — the rules
you are running under may have changed since the last tick, which turns a standing
blocker into an available merge. Only a tick that both found nothing new **and**
performed no action stays silent.

A tick whose snapshot reports `changed: false` and that took no action has nothing
to report: answer exactly `[SILENT]`, which the scheduler recognises and does not
deliver. Do not answer "nothing to report" — that is a message, and it is the
noise silence exists to avoid.

The one thing never made silent is a change to the supervision itself. Pausing,
disabling or removing the supervisor, or closing the wave, is reported with its
reason regardless of the notification level and regardless of quiet hours. A wave
that stops being watched without saying so cannot be noticed by anyone.

Post each material finding to the issue in the tracker as the coordinator. Before
writing anything to the delivery channel, ask `notify decide --class …` and follow
its answer: deliver, or hold it with `notify hold` and say nothing. On the first
run after quiet hours end, call `notify flush` and send the held notices as one
message. Send to the delivery channel only what a person must act on — a decision, an approval,
an unclearable blocker, a finished wave. Never the same paragraph to both. A tick
that found nothing material posts nothing anywhere.

## `WAVE STOP <project>`

Stop future scheduling and call `wave disable`. Preserve workers, worktrees, locks
and evidence. Never kill a worker or delete a worktree without a separate explicit
instruction.

`wave disable` keeps the scheduler job id and names it back to you, because
disabling the wave does not stop the job — remove it deliberately, or it keeps
ticking against a wave that no longer exists. It also reports every lock still
held. Stopping with locks open is legitimate, but from that moment nothing renews
their leases and nothing notices when the work finishes; say so in the report
rather than leaving it to be discovered. Say which of those locks belong to a
worker that already stalled — its commits exist and someone has to publish them,
and after a stop nobody is watching for that.

## `WAVE CLOSE <project>`

After verifying live that no worker, queued action or open review remains, and
that every merged issue carries a published review record and its non-blocking
findings have somewhere to live:
**release completed locks first, then remove the cron job**, keep the local
profile and ledger, and report the final evidence. In that order — a lock left
behind after the supervisor is gone has nobody to clean it up.
