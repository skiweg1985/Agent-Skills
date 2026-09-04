---
name: improve-remote-orchestration
description: Analyse a real orchestration run end to end and turn what it exposes into changes to the orchestrator skill. Use when a dispatched agent hangs, stalls, finishes without publishing, or behaves differently from what the orchestrator recorded; when a wave has completed and is worth reviewing; or when an operational finding should become a durable rule rather than a one-off fix.
---

# Improve Remote Orchestration

The orchestrator was designed against reasoning and is corrected by observation. A
live run exposes in an hour what review would not find in a week — a sandbox that
silently forbids a write, a scheduler job nobody can name, a template that was not
followed. This skill is how that evidence becomes a change to the skill rather
than a repair to one host.

Use it on a host that can reach both sides: the machine that coordinates and the
machines that implement. Read everywhere, change one thing at a time, and only
after the run is safe to touch.

## Resolve the environment, never hard-code it

Everything needed is already recorded. Read it; do not ask, and do not put any of
it into this repository:

| Question | Answer lives in |
| --- | --- |
| Which hosts implement, and how are they started | the orchestrator's agent registry |
| What is this host for | the sync's host role file |
| Is the delivered skill set current | the sync status record |
| What is the wave doing | the orchestrator's project state and locks |
| What did the supervisor conclude | the scheduler's run output for that job |
| What actually happened to the work | the tracker issue and the repository |

Names of hosts, users, absolute paths, chat ids and project identifiers are local
facts. They belong in local state and in your report to the user, never in a
skill, a reference or an example.

## Observe without disturbing

Read-only until the run is finished or the user authorises otherwise. Inspecting a
wave is free; interrupting one costs a worker its context.

**A single reading is a rumour.** Wave state changes between commands, and the gaps
are exactly where a wrong conclusion forms — between initialisation and the wave
being enabled, between a merge and the closing tick, between a lock being released
and the report that says it was preserved. Every apparent inconsistency deserves a
second look a minute later before you name it a defect. Record the time of each
observation and quote it in the finding; "at 11:34 the lock had two renewals" is a
fact, "the lock is not being renewed" was a guess three times today.

Prefer the orchestrator's own status command over reading its state files: it is
the interface the design promises, and using it tests that promise.

## Signatures worth recognising

**A process at 0% CPU is blocked, not busy.** `futex_do_wait` with no database or
socket descriptors open means it is waiting on something that will not arrive.
Compare thread states: a main thread waiting while an event-loop thread polls is a
start-up that never completed, not a slow test.

**Run the same command outside the restricted environment.** If it succeeds in a
fraction of a second, the code is not the defect and no amount of reading it will
help. This single comparison separates "their change broke it" from "the
environment forbids it" faster than anything else.

**A parent that died leaves its children running.** Sandboxed or wrapped processes
whose launcher is gone keep holding their work and are reaped by nobody. Check the
parent id before concluding that something is still supervised.

**Reachability is not capability.** An agent that answers a connection check may
still be unable to write in its worktree or reach the network. Verify the capability
the work actually needs.

**A recorded id is not a running thing.** A stored scheduler job id, a wave marked
enabled, a lock with a future expiry: each says what was intended, not what is. Ask
the scheduler, the process table and the tracker directly.

## Turn a finding into a change

1. **Reproduce it deliberately** before writing anything. A finding you cannot
   reproduce is a hypothesis, and the report must say so.
2. **Ask which rule was missing**, not which host misbehaved. If the fix is a
   command on one machine, the skill will be wrong again on the next machine.
3. **Prefer making the failure impossible over documenting it.** Derive an identity
   instead of checking for duplicates; keep an id instead of warning that it was
   discarded. Documentation is the fallback when the mechanism cannot carry the
   rule.
4. **Verify against the runtime that will actually run it.** The coordinator, the
   workers and your own machine differ in interpreter version and installed tools.
   Run the packaged tests on the target host, not only where you edit.
5. **One finding, one change, one pull request**, with the evidence in the
   description: what was observed, at what time, what was ruled out. A finding
   without its evidence is unreviewable a week later.
6. **Roll out in the order the change requires.** A change to the sync or its
   delivery layout must reach every host before it lands, because an updater does
   not replace itself.

## Report honestly

Say what you observed and what you inferred, and keep them apart. Name the time of
each observation. When a second look contradicts the first, correct it plainly and
move on — the corrected picture is the deliverable, not a defence of the first
reading.

Where a finding touches someone else's work in progress, report it and stop.
Cleaning up another agent's processes, releasing its locks, or publishing its
commits is the user's decision, not a tidy-up you perform because you can.
