# Automatic update operation

The updater runs from outside the clone so that an ordinary pull cannot change
the program cron executes:

```bash
install -Dm755 \
  ~/.local/share/agent-skills/skills/skill-repository-sync/scripts/update-agent-skills.sh \
  ~/.local/bin/update-agent-skills
```

Recommended user crontab entry:

```cron
*/15 * * * * $HOME/.local/bin/update-agent-skills >> $HOME/.local/state/agent-skills/update.log 2>&1
```

## Requirements

`git`, `tar`, `flock` and **Python 3.10 or newer**. Agent hosts run a range of
distributions, so keep these scripts to what 3.10 provides: `datetime.UTC`, for
example, exists only from 3.11 and must be written `timezone.utc`.

## Roles

A host declares what it is in `~/.config/agent-skills/host.conf`:

```bash
AGENT_SKILLS_ROLES="base worker"
```

Omit the file and the host gets `base` alone. `AGENT_SKILLS_ROLES` in the
environment overrides the file. An undefined role name stops the run rather than
being ignored.

## Paths

| Variable | Default | Meaning |
| --- | --- | --- |
| `AGENT_SKILLS_REPO` | `~/.local/share/agent-skills` | the Git clone |
| `AGENT_SKILLS_DIR` | `~/.agents/skills` | the generated delivery directory |
| `AGENT_SKILLS_CONFIG` | `~/.config/agent-skills/host.conf` | role declaration |
| `AGENT_SKILLS_BRANCH` | `main` | branch to follow |
| `AGENT_SKILLS_REMOTE` | the GitHub URL | the only accepted remote |

State lives under `~/.local/state/agent-skills`: `sync-status.json` for the last
outcome and `upstream/` for cached source clones.

## Manual checks

```bash
~/.local/bin/update-agent-skills
cat ~/.local/state/agent-skills/sync-status.json
ls ~/.agents/skills
```

## Failure behavior

- A concurrent update exits without starting a second run.
- A dirty clone is not modified.
- An unexpected `origin` URL is rejected.
- Non-fast-forward history is rejected.
- A skill in the clone with no group in the manifest stops the run before
  anything is copied, as does an undefined role or a skill missing from its
  declared upstream source.
- A failing install (exit 15) or failing validation (exit 14) rolls the clone
  back and rebuilds the previous delivery directory.
- The delivery directory is built beside its target and swapped into place, so an
  interrupted run never leaves a half-built directory.
- Every run records `outcome`, `lastRunAt` and `lastSuccessAt` in
  `sync-status.json`. A failure preserves the earlier `lastSuccessAt`, so
  staleness stays measurable even after several failed runs.
- Cron output is retained in `~/.local/state/agent-skills/update.log`.

## A skill for this host only

Create it in the delivery directory like any other:

```bash
mkdir -p ~/.agents/skills/<name>
$EDITOR ~/.agents/skills/<name>/SKILL.md
```

Do not give it a `.agent-skills-managed.json` marker. Without one the sync treats
it as someone else's and never updates, replaces or removes it — which is what
lets it name real hosts and paths that the shared repository forbids. Agent
tooling that writes skills into this directory is covered by the same rule
automatically.

`sync-status.json` lists what the run installed under `skills`, what it removed
under `removed`, what it left alone under `unmanaged`, and any name collision
under `conflicts`. `lastManagedSkills` keeps the last non-empty set the sync
installed, so a run that installs nothing cannot erase the record of what belongs
to the sync.

## Adding or regrouping a skill

Edit `skills/skill-repository-sync/skill-manifest.json`: every skill needs at
least one group, and a skill may be in several. A skill from an upstream source
also names that source's `id`. Then let the sync run; do not copy directories
into the delivery directory by hand, because the next run rebuilds it.
