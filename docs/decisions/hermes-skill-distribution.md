# How skills reach a Hermes host

> **Superseded by [Role-based skill distribution](role-based-skill-distribution.md).**
> The decision below solved the narrower question of how two shared skills reach a
> Hermes host. The successor generalizes it: skills carry groups, hosts declare
> roles, and the updater installs the intersection — which answers this question
> as a special case and additionally keeps implementation skills off a coordinator
> entirely. The context and the rejected alternatives here remain accurate.

## Context

This repository serves two kinds of consumer from one tree:

- **Codex and Claude Code** read top-level `<skill-name>/` directories out of the
  deployment clone at `~/.agents/skills`, which the updater keeps current.
- **Hermes** registers the repository as a tap and indexes `skills/` only.

The remote-agent orchestrator published through the tap deliberately owns no
autonomy ladder and no agent-selection heuristic. It defers autonomy to
`linear-coordinate-agents` and agent selection to `cost-aware-agent-routing`.
Both of those live at the top level, so the tap does not install them: Hermes
would get the orchestrator without the two skills it delegates to.

Three facts constrain the fix:

- Hermes reads additional skill directories through `skills.external_dirs` in
  `~/.hermes/config.yaml`. External skills enter the system prompt index
  automatically — unlike a tap, where each skill is installed deliberately.
- Symlinked directories under a Hermes skills directory are not discovered
  ([NousResearch/hermes-agent#8293](https://github.com/NousResearch/hermes-agent/issues/8293)),
  so a symlink farm is not an option.
- The deployment clone holds 44 skills. 37 of them come from `mattpocock/skills`
  and refresh from that third party on every sync.

## Decision

The tap surface (`skills/`) carries **Hermes-exclusive** skills only.

Shared skills reach Hermes through a **curated directory** that the updater fills
from a list declared in the sync manifest. `skills.external_dirs` points at that
directory, not at the deployment clone. The initial list is
`linear-coordinate-agents` and `cost-aware-agent-routing`.

A skill is either tap-surface or shared, never both. The orchestrator therefore
never appears in the curated directory, so Hermes' local-over-external precedence
is never load-bearing.

## Alternatives

**Point `external_dirs` at the whole deployment clone.** No new machinery, and a
newly shared skill needs no action. Rejected on role hygiene: the orchestrator is
a pure dispatcher that must never implement, and this would offer it `tdd`,
`implement`, `prototype`, `scaffold-exercises` and roughly thirty more
implementation skills in every prompt. Against a threat model of honest mistakes,
that is the most likely way the dispatcher boundary gets crossed. It would also
let a third party extend the orchestrator's menu on every sync without anyone
deciding. The measured context overhead — about 1,676 tokens per prompt against
323 for the two needed skills — is real but was not the deciding factor.

**Point at the whole clone and disable unwanted skills in Hermes.** Hermes tracks
an enabled state per skill, but new upstream skills arrive enabled. That trades a
list maintained deliberately for one maintained reactively.

**Copy or symlink shared skills into `~/.hermes/skills/`.** Symlinks are not
discovered (see above). Copies into a second tree owned by a different mechanism
become a stale second state.

**Absorb the routing rules into the orchestrator.** Duplicates content that will
drift — the same reason the orchestrator delegates rather than decides. The
updater's own validation also rejects a same-named copy as a duplicate skill.

## Consequences

The orchestrator sees exactly the skills it needs. Nobody outside this repository
can extend what Hermes is offered. One sync run keeps both surfaces current, and
no content is duplicated in the repository.

**The curated list is a maintenance surface, and this is the risk to watch.** A
skill that becomes shared later is absent on Hermes until someone adds a line to
the manifest. Because the orchestrator treats `linear-coordinate-agents` and
`cost-aware-agent-routing` as hard preconditions, a forgotten entry surfaces as a
refusal at `A3 SETUP` rather than as silent degradation — visible, but it will
surface at an inconvenient moment rather than when the list was edited.

The curated directory is a second materialization of content that also exists in
the deployment clone. If the updater fails partway, Hermes can read a stale copy
while the clone is current. Both are written in the same sync run and recorded in
the install record, so the drift is detectable, but it is not impossible.

## Revisit when

- The curated list passes roughly five entries, or entries start being added
  reactively rather than deliberately. At that point the maintenance cost has
  overtaken the hygiene benefit: switch to the whole deployment clone and write
  the no-implementation rule explicitly into the orchestrator instead.
- Hermes gains per-skill enable/disable that survives upstream additions, which
  would make the whole-clone option safe without a list.
- [NousResearch/hermes-agent#8293](https://github.com/NousResearch/hermes-agent/issues/8293)
  is fixed. Symlinks would then remove the second-materialization risk entirely.
