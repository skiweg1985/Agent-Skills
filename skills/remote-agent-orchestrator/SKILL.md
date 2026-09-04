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
- **Done** is a pull request open *and* the process ended. **Dead** is the process
  gone with no pull request.

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

`WAVE STOP` removes future scheduling and preserves workers, worktrees and locks.
`WAVE CLOSE` removes the job after live verification that no worker, queued action
or open review remains. A wave whose scope is exhausted closes itself.

Before any dispatch or merge, refresh the tracker, repository, pull request and CI
state, worktrees and locks. A repeated wake must attach to an existing run rather
than dispatch the same issue twice. Never treat a worker's claim as evidence:
stdout is diagnostics, and only the pull request and the tracker comment count.
