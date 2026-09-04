# Role-based skill distribution

Supersedes [How skills reach a Hermes host](hermes-skill-distribution.md).

## Context

The superseded decision solved one host's problem: a Hermes coordinator needed
two shared skills that its tap does not carry, so the updater was to fill a
curated directory for Hermes alone. That decision was sound for the question it
answered and wrong about the shape of the problem.

The real question is not "how do two skills reach Hermes" but "which skills
belong on *this* host at all". A coordinator that must never implement should not
merely be told not to use `tdd` and `prototype` — it should not have them. The
same mechanism that answers this answers the Hermes question as a special case.

Four platforms consume skills, and three of them already read the same directory:

| Platform | Discovers in |
| --- | --- |
| Codex | `~/.agents/skills/<name>/` |
| Claude Code | `~/.claude/skills/<name>/` (symlinked to the above) |
| OpenCode | `~/.config/opencode/skills/`, and natively also `~/.claude/skills/` and `~/.agents/skills/` |
| Hermes | `~/.hermes/skills/`, plus any path in `skills.external_dirs` |

Selection is impossible while the delivery directory *is* the Git clone: a clone
always contains every skill, and deleting from it makes the working tree dirty,
which the updater refuses by design.

## Decision

**Skills are grouped, hosts declare roles, and the updater installs the
intersection.**

Groups are declared in the skill manifest, not encoded in directory names. A
directory name is the skill's name — our own validation enforces that — so a
`coordinator-` prefix would make the deployment decision part of the invocable
identity, turn a regrouping into a rename, and prevent a skill from belonging to
two groups.

Initial groups:

| Group | Skills |
| --- | --- |
| `base` | `agent-host-operations`, `linear-coordinate-agents`, `skill-repository-sync`, `documentation-standards`, `schreibstil-pruefen` |
| `coordinator` | `remote-agent-orchestrator`, `cost-aware-agent-routing` |
| `worker` | the skills installed from `mattpocock/skills` |

`linear-coordinate-agents` is in `base`, not `coordinator`. Most of its sections
address the agent doing the work — claiming an issue, commit attribution,
comment signatures, blockers and handoff. The orchestrator requires a worker to
author its own tracker start comment and then verifies it independently; a worker
without this skill cannot satisfy a check the coordinator performs.

**A skill with no group aborts the sync.** Not installing it would let a skill
disappear silently; installing it everywhere would defeat the separation. An
abort also means an upstream source cannot introduce a skill into any host
without someone assigning it first.

**The clone and the delivery directory are separate.** The clone lives at
`~/.local/share/agent-skills`; `~/.agents/skills` becomes generated content,
holding only what this host selected — no `README.md`, no `docs/`, no `.git`.

**Hosts declare roles in `~/.config/agent-skills/host.conf`**, overridable by
environment. The default is `base` alone, so a host is never a coordinator by
accident.

**Hermes points `skills.external_dirs` at the delivery directory.** The tap stays
registered as a browsable catalog for deliberate manual installs, but delivers
nothing by default — otherwise one platform would be exempt from the role
mechanism.

**Every sync writes `sync-status.json`** with the outcome, commit, counts, and a
separate `lastSuccessAt`. Under cron a failure is otherwise silent; with this
record, staleness is a one-line check rather than a log-reading exercise.

## Alternatives

**A curated directory for Hermes only** — the superseded decision. It leaves
every other host receiving every skill, and leaves the coordinator's role
boundary as an instruction rather than a fact.

**Point Hermes at the whole clone.** Offers a pure dispatcher some thirty
implementation skills and lets a third party extend that menu on every sync.
Under this decision the concern disappears: those skills are `worker` and are
never installed on a coordinator.

**A prefix in the directory name.** Rejected for the identity reasons above.

**Drop the upstream skills entirely** rather than group them. Considered and
rejected: grouping already protects the coordinator, and the mandatory-group rule
already blocks silent upstream additions, so dropping them would give up
capability to solve a problem that is solved. They are assigned to `worker` in
one stroke and can be curated later from a running system.

## Consequences

A host receives what its role needs and nothing else. The coordinator's
dispatcher boundary stops being an instruction and becomes a property of the
filesystem. One manifest governs both own and upstream skills, and no third party
can add a skill to any host without a deliberate assignment.

**The migration is disruptive and must be sequenced.** The delivery directory
changes meaning and the clone moves. A host still running the previous updater
would find its clone gone. The updater must be replaced on each host before this
lands, exactly as with the earlier upstream-skills change.

**Group assignments are a maintenance surface**, and the mandatory-group rule
makes a forgotten assignment a hard failure rather than a silent one. That is
deliberate: a visible stop at sync time is cheaper than discovering weeks later
that a host has been missing a skill. It does mean a new upstream revision that
adds skills will fail the sync until the manifest is updated.

**A skill can be installed twice on Hermes** — once from the tap by hand, once
through the external directory. Hermes resolves this by precedence (local wins),
and nothing installs from the tap by default, so this only arises from a
deliberate act.

## Revisit when

- A host needs a skill subset that roles cannot express — for example two
  coordinators with different tool access. The answer then is more groups, not
  per-host lists; if per-host lists become necessary, this model has reached its
  limit.
- The mandatory-group abort proves too brittle in practice, for instance if
  upstream revisions are bumped often enough that the sync fails routinely. A
  default group for a named source would relax it without losing the guarantee
  for unsourced skills.
- A platform appears that cannot read a shared directory and offers no equivalent
  of `external_dirs`. It would need its own delivery step, and the assumption
  that one generated directory serves everything would no longer hold.
