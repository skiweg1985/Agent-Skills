---
name: remote-agent-orchestrator
description: Explicitly requested orchestrator for a bounded delivery wave across remote coding agents reached over SSH. Use only when a user or trusted coordinator says WAVE SETUP, WAVE INIT, WAVE START, WAVE STATUS, WAVE STOP, or WAVE CLOSE; never activate it because it is installed, because a schedule fired, or because work appears to be waiting.
---

# Remote-Agent Orchestrator

Coordinate remote coding agents for one bounded delivery wave. This skill
dispatches and supervises; it never implements.

## What this skill does not decide

It owns execution and supervision only. Three questions belong elsewhere, and
answering them here would put two skills in disagreement:

| Question | Owner |
| --- | --- |
| How much autonomy applies | `linear-coordinate-agents` — read the level it resolves; carry no ladder here |
| Who owns an issue | The tracker. A lock is a local execution mutex, never an ownership claim. Never assign |
| Which agent gets which issue | `cost-aware-agent-routing`, given the issue, its write set, and the registry |

Both skills are **hard preconditions**. If either is absent, `WAVE SETUP` reports
it and `WAVE INIT` and `WAVE START` refuse. Never fall back to your own routing or
autonomy judgement — that is exactly the decision this skill does not make.

## Commands

```text
WAVE SETUP [--role ROLE=AGENT …]
WAVE INIT [project]
WAVE START <project> <milestone|issue …>
WAVE STATUS [project]
WAVE STOP <project>
WAVE CLOSE <project>
```

`SETUP`, `INIT` and `STATUS` write nothing externally and need no ceremony.
**`START` and cron creation require an explicit human go-ahead**: that is where
foreign code runs on other machines and where a recurring job is created. A
schedule, a webhook, a tracker event, or a session waking up is never that
go-ahead.

The go-ahead authorizes a **goal**, not a single dispatch. Within that scope the
supervisor may dispatch on its own. The scope is a tracker milestone or an
explicit issue list — never free text, which would be re-interpreted at every
refresh and could drift while nobody changed anything.

Read `references/commands.md` for the lifecycle and `references/agent-registry.md`
for reachability and roles.

## Boundaries

This skill belongs on the orchestrator host only; workers receive a bounded issue
prompt and nothing else. The coordinator is a **pure dispatcher** and never
implements — if it also held a worker's lock, the separation that lets it release
locks would collapse into one identity.

It may coordinate bounded non-production work up to the autonomy level the tracker
skill resolves. It never permits deployment, production writes, credential
exposure, destructive operations, or scope expansion.

## Local state

Nothing project-specific is ever written into this repository.

```text
$XDG_CONFIG_HOME/agent-orchestrator/
├── coordinator.json     # this installation's identity
├── team-profile.json    # role -> agent id
└── agents.json          # agent id -> reachability and invocation; never credentials

$XDG_STATE_HOME/agent-orchestrator/
├── worker-readiness.json
└── projects/<key>/
    ├── profile.json     # repository, tracker, target branch, worker cap
    ├── team.json        # project-scoped role bindings
    ├── wave.json        # scope, enabled state, cron job id
    ├── snapshot.json    # secrets-free comparison state
    ├── wave.lock        # one active wave per project
    └── locks/<issue>.json
```

Override the roots with `ORCHESTRATOR_CONFIG_ROOT` and `ORCHESTRATOR_STATE_ROOT`.

`<key>` is **derived** from the canonical repository URL and the tracker identity,
not chosen. The same repository and tracker therefore cannot be initialized twice
under two names, each believing it was alone.

Coordinator identity belongs to the **installation**, not the session. A later
session is the same coordinator and continues; the session is recorded for audit
only. That one active wave runs per project is enforced by a `flock` with
liveness, so a dead session's hold is released by the operating system.

## Locks and liveness

The coordinator holds every lock **on behalf of** its workers, because workers do
not have these scripts. Release is authorized by **coordinator identity**, not by
session equality — closing your own wave is normal operation, not an override.
`--force` exists for a genuinely foreign lock and always records who superseded
whom.

The lease is a liveness signal, not a timeout:

- **Liveness** is the process or session state on the worker host, checked over
  SSH. Nothing else.
- **Progress** is commits, pull requests and tracker comments. They say something
  happened, not that anyone is working now.
A finished process has three possible states, and treating them as two loses work:

- **Done** — a pull request is open and the process ended. Proceed to review.
- **Stalled** — the process ended with no pull request, but commits exist on its
  branch. The work was done and only publishing failed, usually because the worker
  could not reach the network. Keep the lock, report it, and re-dispatch the same
  agent with the bounded task of publishing what it already committed. Never treat
  this as dead: the commits are real and nobody else will find them.
- **Dead** — the process ended with no pull request and no commits. Nothing was
  produced. **Release the lock at once** rather than waiting out the lease, record
  why, and let the issue become eligible again. Waiting hours for a lease you know
  is worthless blocks the issue for no reason.

Renew only what you confirmed independently. An unrenewed lease expires, and the
next acquisition records the holder it superseded.

## Dispatch

Reach each worker through its registry entry: transport, host, user, working
directory, and an **explicit invocation template**. Agent CLIs differ in how they
take a one-shot prompt, so a template is required and never inferred from a name.
No credentials live there; public-key authentication is provisioned on the hosts
and only verified. See `references/agent-registry.md`.

**Run the template verbatim.** Substitute `{prompt}` and change nothing else: do
not shorten a path to a bare command name, do not add flags, do not reorder
arguments. The template carries absolute paths because a non-interactive shell has
a minimal `PATH` and will not find an agent installed under a home directory. It
omits sandbox and approval flags deliberately, because such a flag can silently
restrict where the worker may write and cut its network — turning a working setup
into a run that hangs or cannot push. A command assembled at dispatch time looks
equivalent and is not; if the template is wrong, correct the registry so the fix
holds for every later dispatch.

**Reachability is not capability.** An agent CLI that answers is not yet an agent
that can work. Before dispatch, confirm on the execution host, from the same kind
of shell the work will run in, that the worker can **write inside its worktree**
and **reach the network**:

```bash
touch <worktree>/.probe && rm <worktree>/.probe
git -C <worktree> ls-remote origin >/dev/null
```

A sandbox whose writable area is derived from the repository rather than the
worktree does not fail loudly: a start-up write blocks, and the run hangs at zero
CPU looking like a deadlock in the code. Without network, work can be committed
but never pushed, which from outside looks like an agent that stopped for no
reason. Both checks are two commands; skipping them costs an hour of a worker
repeating something that cannot succeed. A worktree the worker cannot write in is
a hard stop for that issue — report it, do not substitute another agent.

## Work, review, merge

A **write set is declared on the issue** before it is dispatchable; an issue
without one is not dispatched. Check the diff against that declaration at pull
request time. Exceeding it is a hard merge stop: leave the pull request open, keep
the lock, report the issue as blocked. Never trim the diff or widen the
declaration afterwards.

Run **as many workers as there are issues with disjoint write sets**, under the
project's `maxWorkers` cap. The cap is an emergency brake, not the steering.

**Review is mandatory and performed by an agent other than the implementer.**
**It must leave a record the coordinator did not write.** The reviewer posts its
own findings under its own identity — a pull request review, or a tracker comment
with its session identifier, as the implementer does for its claim. Verify that
record independently before merging, exactly as you verify the start comment. A
review you only heard about is a worker's claim, and this skill does not treat a
claim as evidence; relaying it in your own summary launders it into a fact.
Findings that do not block go into the tracker as their own record with an owner,
not into a closing paragraph where they are read once and lost.
A review is work: it occupies a slot and its own lock. **The coordinator merges** —
it is the only party that sees every write set in the wave and can tell whether
two finished pull requests break together. When two collide, the first to finish
merges and the second rebases; a rebase that is not trivially clean becomes a
blocked issue back to a worker, because resolving it is implementation work.

## Local helpers

The scripts sit next to this file. A session's working directory is not the skill
directory, so resolve `scripts/` against **this skill's own location** rather than
the current directory. Where the shared sync delivers it, that is:

```bash
ORCH=~/.agents/skills/remote-agent-orchestrator/scripts/orchestratorctl.py
```

If you cannot resolve the skill directory, find it once and use the absolute path
for the rest of the session:

```bash
find ~/.agents/skills ~/.hermes/skills ~/.claude/skills -name orchestratorctl.py 2>/dev/null | head -1
```

```bash
python3 "$ORCH" setup
python3 "$ORCH" setup --role backendSecurity=worker-2
python3 "$ORCH" setup --agent worker-1 --host build-1.example \
  --user agent --workdir /srv/work --invocation 'codex exec {prompt}'
python3 "$ORCH" project init --repo <url> --tracker <project>
python3 "$ORCH" status
python3 "$ORCH" status --project <key>
python3 "$ORCH" wave enable --project <key> \
  --scope <milestone> --scope-kind milestone --cron-job-id <id>
python3 "$ORCH" lock acquire --project <key> --issue <issue> \
  --agent <agent> --session <session> --revision <revision>
python3 "$ORCH" lock renew --project <key> --issue <issue>
python3 "$ORCH" lock release --project <key> --issue <issue>
python3 "$ORCH" snapshot --project <key> --input <file>
```

Every command prints JSON and never contacts a worker; remote actions are yours.
`status` with no project lists every known project, wave state, registered agent
and open lock — that is how a new session finds existing work, on request rather
than automatically.

## Supervision

Only an explicit `WAVE START` may create one temporary supervisor cron job for the
project, attaching this skill with the project as working directory, and persist
its id through `wave enable`. Use a cron job rather than a background session: a
background task dies with the host process while remote workers keep running for
hours, and nobody notices.

**A recorded supervisor is not a running one.** `wave.json` holds the scheduler's
job id; that the job still exists, is enabled and is due is a separate fact. A wave
whose supervisor was paused, disabled or deleted keeps its locks and believes it is
watched while nobody renews a lease, evaluates a review or notices a finished
worker. `WAVE STATUS` therefore checks the recorded job against the scheduler and
reports a missing or paused supervisor as a blocker, not as a detail. Storing the
id is bookkeeping; verifying it is supervision.

`WAVE STOP` stops future scheduling and preserves workers, worktrees and locks. It
**keeps the scheduler job id** and reports any lock still held: the scheduler entry
outlives the wave record, so discarding the id leaves a supervisor that still runs
and that nobody can name, and a held lock without a supervisor is a lease nothing
renews and a finished worker nobody notices. Removing the scheduler job is a
separate, deliberate act.
`WAVE CLOSE` removes the job after live verification that no worker, queued action
or open review remains. A wave's scope is exhausted only when every issue in it is **merged or blocked**.
An open pull request awaiting review is unfinished work, and an implementer that
has stopped is not a finished issue. Closing on "the worker is done" ends the
supervision before the review it was supposed to arrange.

Every supervising run stores the refreshed state as a snapshot. "Report only
material changes" is not a matter of judgement — it is a comparison against that
stored state, and a run that stores none has nothing to compare against and
restates everything it sees. The snapshot holds a digest and a summary, never
secrets.

Before any dispatch or merge, refresh the tracker, repository, pull request and CI
state, worktrees and locks. A repeated wake must attach to an existing run rather
than dispatch the same issue twice. Never treat a worker's claim as evidence:
stdout is diagnostics, and only the pull request and the tracker comment count.

## Reporting

Two audiences, two different messages. Sending the same paragraph to both is noise
that trains everyone to ignore one of them.

**The tracker gets the record.** Write material findings onto the issue whose wave
is being supervised: work finished, a review requested or returned, a lease
expired, a supervisor found missing, a blocker, a wave closed. That is where the
next agent, the next session and the reviewer look, and it outlives every chat.
Post as the coordinator in its own voice, and never phrase a worker's action as
your own — say that the coordinator verified, renewed or blocked something.
Follow the tracker skill's comment conventions: natural sentences, no key-value
scaffolding, the session identifier as the single trailing line.

**The delivery channel gets what needs a person — and what that means is
configured, not judged.** Ask the tool before writing to the channel:

```bash
python3 "$ORCH" notify decide --class blocker|milestone|progress --project <key>
```

It answers `deliver`, `hold`, and why. Three subscription levels, each including
the ones above it: `blocker` for what forces a decision, `milestone` for finished
issues, requested reviews and closed waves, `progress` for every material change.
A wave's setting beats the project's, which beats the host default.

During quiet hours only a blocker passes. Everything else is **held, never
dropped** — `notify hold` parks it, and the first run after the window ends calls
`notify flush` and sends one summary. Waking up to silence and no idea what
happened is the failure this avoids.

**Silence is spelled `[SILENT]`.** The scheduler recognises that exact answer and
skips delivery; an empty response is not the documented way and an explanatory
"nothing to report" is the noise you were avoiding.

**Never be silent about your own supervision.** A run that pauses, disables or
removes the supervisor, or closes the wave, reports that and why — whatever the
level says, and even inside quiet hours. Those are not findings, they are changes
to who is watching, and a wave that stops being watched without saying so cannot
be noticed by anyone. The policy governs findings; it never governs a change to
the supervision itself.

None of this touches the tracker. The record is written either way; the policy
only decides who gets woken. A decision, an approval, a
blocker nobody else can clear, a finished wave. Not progress a human cannot act
on: "the worker is still running" belongs in the tracker at most, and usually
nowhere. If a message would tell the reader nothing they must do, it does not
belong in the channel.

A tick that found nothing material writes nothing anywhere. The scheduler's own
run log is not a report and needs no consideration; the local secrets-free ledger
stays the orchestrator's memory for snapshot comparison, not a third audience.
