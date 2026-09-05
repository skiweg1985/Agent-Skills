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
5. Report safe candidates, issues whose write set is missing or is a description
   rather than paths, and overlaps between exclusive paths. Name the issues a
   `START` would first have to send to a coding agent for derivation.

`INIT` must not create a scheduler job, dispatch a worker, change issue ownership,
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
4. When issues in the scope lack a write set, or declare one in words instead of
   paths, dispatch one coding agent for all of them together to derive exclusive
   paths, shared files and an owner per shared file, as **Write sets** in the
   skill describes. The scope go-ahead covers that read-only run. Check its
   proposal against the repository, decide the shared-file owners, and record the
   result on each issue before continuing. Do not derive a write set yourself.
5. Select issues that are unblocked, have an accountable owner, declare a write
   set in paths, and whose exclusive paths do not overlap another running
   issue's. Declared shared files may overlap. Stay within `maxWorkers`.
6. Take a lock for each issue before dispatching. An existing live lock means
   attach to that run and inspect it; never start a second.
7. Dispatch using the agent's registered invocation template. Require one worktree
   per issue, created by the worker, and an agent-authored tracker start comment.
   Verify both independently — the worker saying so is not evidence.
8. Give the wave a supervisor. **Read the job id already in the wave state first**
   and ask the scheduler whether that job still exists. If it does, reuse it —
   re-enable and re-schedule it rather than creating a second one; stopping a wave
   keeps its job on purpose, so a later start finds it waiting. Create a new job
   only when the recorded id names nothing. Persist the id with `wave enable`
   either way.

   The job's prompt holds the facts of this wave — project key, repository, worker
   host, each dispatched agent's session and worktree, the authorized scope, the
   coordinator identity, the finding that authorizes the merge — and one
   instruction: run the supervisor tick from `remote-agent-orchestrator`. Do not
   paraphrase the tick, the write-set rule or the reporting policy into it. The
   skill states them, and the next sync corrects them there; a copy in the prompt
   outlives every correction.

   Two supervisors for one project is a blocker, not something to tidy up: they
   tick against the same wave, both believe they are in charge, and the second one
   is evidence that a stop or close left something behind. Report it with both job
   ids and let a human decide which survives.

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

Read the job's prompt back too. If it restates rules instead of naming the wave,
report that: those rules were frozen when the job was created and will not follow
the skill. Replacing the prompt is the fix, and it needs no new job.

## Supervisor tick

The tick lives in `SKILL.md`, not here. It runs unattended every few minutes, and
a rule the supervisor must follow on every run has to be in the file that is
loaded with the skill — reference files are read on request, and an unattended run
has no reason to ask.

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
**release completed locks first, then remove the scheduler job**, keep the local
profile and ledger, and report the final evidence. In that order — a lock left
behind after the supervisor is gone has nobody to clean it up.
