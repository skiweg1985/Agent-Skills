# Agent Skills

Shared, public [Agent Skills](https://agentskills.io/) for autonomous coding agents such as OpenAI Codex and Claude Code.

## Included skills

- `agent-host-operations` — safe conventions for autonomous work on a shared agent host.
- `cost-aware-agent-routing` — route work between low-cost and premium coding agents.
- `documentation-standards` — keep software-repository documentation accurate, lean, and task-oriented.
- `linear-coordinate-agents` — coordinate parallel agents through Linear, repository working agreements, isolated worktrees, and review gates.
- `schreibstil-pruefen` — review and improve German technical writing against repository conventions and a measured fallback style guide.
- `skill-repository-sync` — safely update a deployed clone of this repository through an externally installed updater.

## Skills installed from upstream

This repository stores only its own skills. Third-party collections are declared in
[`skill-repository-sync/upstream-skills.json`](skill-repository-sync/upstream-skills.json)
and installed straight from their source by the updater, so they stay available in
every agent without being copied into this repository.

Currently declared: **37 MIT-licensed engineering and productivity skills** from
[`mattpocock/skills`](https://github.com/mattpocock/skills), eight of which upstream
marks as in progress. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for
provenance and license.

Installed directories are excluded from Git inside the deployment clone, so the
updater's dirty check keeps protecting genuine local changes. Run the updater once
after cloning to materialize them.

## Installation

Codex discovers user-level skills in `~/.agents/skills`. Claude Code discovers personal skills in `~/.claude/skills` and follows symlinks.

```bash
git clone https://github.com/skiweg1985/Agent-Skills.git ~/.agents/skills
mkdir -p ~/.claude
ln -s ../.agents/skills ~/.claude/skills
```

Then install the updater as described below and run it once. It fetches the declared
upstream skills into the clone; without that step only this repository's own skills
are present.

If either path already exists, back it up and reconcile its contents before cloning. Do not overwrite existing skills blindly.

## Automatic updates

Install a trusted copy of the updater outside the repository:

```bash
install -Dm755 \
  ~/.agents/skills/skill-repository-sync/scripts/update-agent-skills.sh \
  ~/.local/bin/update-agent-skills
```

Run it manually:

```bash
~/.local/bin/update-agent-skills
```

A cron example is included in the `skill-repository-sync` skill. The updater only accepts the expected GitHub remote, refuses a dirty deployment clone, performs a fast-forward-only update, installs the declared upstream skills at their pinned revisions, validates skill metadata, and rolls back to the previous commit if installation or validation fails.

## Project-specific skills

This repository is intended for skills that should apply across projects. Keep project-specific instructions in the repository that owns the project:

- Codex: `.agents/skills/<skill-name>/SKILL.md`
- Claude Code: `.claude/skills/<skill-name>/SKILL.md`

## Public repository policy

Never commit credentials, tokens, customer data, private infrastructure details, or sensitive logs. Use example identifiers and sanitized evidence only.
