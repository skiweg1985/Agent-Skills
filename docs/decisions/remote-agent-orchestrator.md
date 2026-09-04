# Remote-agent orchestrator

The design the `a3-cron-coordinator` skill is being rebuilt to. It is recorded
here because the reasoning is expensive to reconstruct and several of its rules
only make sense together.

## Context

The existing skill coordinates a delivery wave but was written for a coordinator
and workers sharing one machine. Running real remote agents exposed seven defects,
each reproduced rather than suspected: the documented lock command writes to
`runtime/projects/<slug>/locks` instead of the documented path; the snapshot
mechanism `A3 STATUS` depends on is unreachable through the documented flow;
`a3_state.py` has no tests; an expired lease is taken over with no trace of the
previous holder; a corrupt lock file surfaces a raw Python error; `A3 CLOSE`
can only release a worker's lock with `--force`; and deduplication only compares
within one slug, so two sessions can run parallel waves on one repository.

The goal is Hermes orchestrating remote coding agents over SSH, in combination
with `linear-coordinate-agents`.

## Roles and boundaries

The skill is installed **only on the orchestrator host**. Workers never have it,
so "a worker never starts a wave itself" is structurally true rather than a rule
to obey. The coordinator is a **pure dispatcher** and never implements: if it
also held a worker's lock, the separation that authorizes it to release locks
would collapse into one identity.

The threat model is **honest mistakes**, not a hostile agent. Anyone with SSH
access to the workers bypasses any marker the skill could carry; that is a
question of SSH authorization, not skill logic.

## Identity and mutual exclusion

Coordinator identity belongs to the **Hermes installation**, not to a session — an
ID generated at first setup. Any later session of that installation is the same
coordinator and simply continues, which is what makes the wave findable in a new
session without a takeover ritual. The running session is recorded for audit only.

At most **one active wave per project**, enforced by a `flock` with liveness
rather than by comparing identities: a dead session's lock is released by the
operating system.

**Project identity is derived** from the canonical repository URL plus the tracker
identity; the chosen name survives only as a label. A duplicate then cannot be
created rather than merely being detected.

## Authorization and scope

`SETUP`, `INIT` and `STATUS` write nothing externally and need no ceremony.
`START` and cron creation require an explicit human go-ahead — that is where
foreign code runs on other machines and where a job is created that repeats a
mistake.

The go-ahead authorizes a **goal**, not a single action: a tracker milestone or an
explicit issue list, never free text. Within that scope the supervisor may
dispatch autonomously. Free text would be re-interpreted at every refresh, so the
scope could drift while nobody changed anything.

A wave **ends itself** once its scope is exhausted. A cron still running after the
goal is met is the forgotten background process that surprises someone weeks later.

## Supervision

The supervisor is a **cron job with the skill attached**, not a background session.
A background task dies with the host process while remote workers keep running for
hours — and nobody notices. Cron and an interactive session cannot both dispatch,
because of the project `flock`.

## Locks and liveness

The coordinator **holds every lock on behalf of its workers**, because workers do
not have the scripts. A lock records the `agent`, the `coordinator` installation,
and the session for audit. **Release is authorized by coordinator identity**, not
by session equality, which removes `--force` from normal operation; it remains for
emergencies and always leaves a record of who superseded whom.

The lease is a **liveness signal**. The supervisor renews only what it has
independently confirmed is still running; an unrenewed lease expires with an
explicit note.

- **Liveness** is the process or session state on the worker host, checked over SSH — nothing else.
- **Progress** is commits, pull requests and tracker comments. They say something
  happened, not that someone is working.
- **Done** is a pull request open *and* the process ended. **Dead** is the process
  gone with no pull request.

Measuring only progress lets a hung worker with an old commit pass as alive forever.

## Dispatch contract

The agent registry holds, per agent, the transport, host, user, working directory,
a role hint, and an **explicit invocation template** — the one-shot forms of the
available coding agents differ, and guessing one from an agent's name is exactly
the inference this skill forbids elsewhere. The orchestrator asks for these
details on first use and stores them.

**No credentials anywhere.** Public-key authentication is assumed and only
verified; worker credentials are provisioned on the worker host and never
transported. The registry says where an agent lives, not how to break in.

**Only externally observable facts count as results:** the pull request and the
tracker comment. Worker stdout is diagnostics, never evidence — otherwise "never
treat a worker's claim as evidence" is defeated through the back door.

A missing registry entry or an unreachable host is a **hard stop for that issue**:
do not dispatch, release the lock, report. Never guess, never substitute another
agent. Ask a human only when one is present; otherwise the question goes into the
report.

The **worker creates its own worktree** from a convention in the registry; the
coordinator verifies it exists and sits on the expected branch before counting the
dispatch as successful. The coordinator does not perform git surgery on several
remote machines.

## Work, review, merge

A **write set is declared on the issue** before it is dispatchable. The diff is
checked against that declaration at pull-request time; exceeding it is a hard
merge stop with the pull request left open, the lock held and the issue reported
as blocked. No trimming, no retroactive widening.

**Concurrency is bounded by disjoint write sets**, not by a number — as many
workers as there are issues with non-overlapping write sets, under a configurable
cap as an emergency brake. With agents reviewing each other, the real bottleneck
is repository conflict, which is measurable.

**Review is mandatory and performed by an agent other than the implementer.**
The **coordinator merges**: it is the only party with a view of every write set in
the wave and can see whether two finished pull requests break together, which
neither author can. A review is work — it occupies a slot and a lock. When two
pull requests collide, the first to finish merges and the second rebases; a rebase
that is not trivially clean becomes a blocked issue back to a worker, because
conflict resolution is implementation work.

## What the orchestrator does not decide

| Question | Owner |
| --- | --- |
| Autonomy level | `linear-coordinate-agents` — the orchestrator reads the resolved level and carries no ladder of its own |
| Ownership of an issue | The tracker. The lock is a local execution mutex, never an ownership claim; the orchestrator does not assign |
| Which agent gets which issue | `cost-aware-agent-routing`, given the issue, its write set, and the available agents |

Both are **hard preconditions**. If either is missing on the host, setup reports it
and `INIT` and `START` refuse. An orchestrator that quietly falls back to its own
heuristics would make exactly the decisions it was designed not to make.

Reporting goes to the tracker as the shared record, plus a local secrets-free
ledger for the orchestrator's own snapshot comparison — no third destination.
A new session finds existing work through `STATUS` with no argument, which lists
known projects, wave states, configured agents and open locks. Nothing activates
on its own.

## Consequences

The dispatcher boundary, the single-wave guarantee and the duplicate-project
guarantee all become properties of the system rather than instructions. The cost
is that the orchestrator is useless alone: it depends on two other skills and on a
registry a human fills in once.

Liveness over SSH means the orchestrator needs shell access to every worker host
for supervision, not only for dispatch. A worker host that permits dispatch but
not process inspection cannot be supervised, and the design has no fallback that
would be honest — progress signals are explicitly not liveness.

## Revisit when

- Workers gain the ability to run the state scripts themselves. Locks could then be
  held by their actual holder, and the coordinator-identity release rule would
  become unnecessary indirection.
- A supervisor needs to dispatch beyond an authorized goal — continuous throughput
  rather than bounded waves. That is a deliberate extension needing its own
  authorization, not a parameter change.
- Hermes sessions gain durable supervision that survives process exit, which would
  make the cron dependency optional.
