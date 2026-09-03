# Agent Skills

Shared, public [Agent Skills](https://agentskills.io/) for autonomous coding agents such as OpenAI Codex and Claude Code.

## Included skills

- `agent-host-operations` — safe conventions for autonomous work on a shared agent host.
- `linear-coordinate-agents` — coordinate parallel agents through Linear, repository working agreements, isolated worktrees, and review gates.
- `skill-repository-sync` — safely update a deployed clone of this repository through an externally installed updater.
- **Matt Pocock Skills** — 37 MIT-licensed engineering and productivity skills vendored from [`mattpocock/skills`](https://github.com/mattpocock/skills), including eight explicitly marked upstream as in progress. They are installed as top-level skill directories for cross-agent discovery; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for the pinned revision, complete inventory, and license reference.

## Installation

Codex discovers user-level skills in `~/.agents/skills`. Claude Code discovers personal skills in `~/.claude/skills` and follows symlinks.

```bash
git clone https://github.com/skiweg1985/Agent-Skills.git ~/.agents/skills
mkdir -p ~/.claude
ln -s ../.agents/skills ~/.claude/skills
```

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

A cron example is included in the `skill-repository-sync` skill. The updater only accepts the expected GitHub remote, refuses a dirty deployment clone, performs a fast-forward-only update, validates skill metadata, and rolls back to the previous commit if validation fails.

## Project-specific skills

This repository is intended for skills that should apply across projects. Keep project-specific instructions in the repository that owns the project:

- Codex: `.agents/skills/<skill-name>/SKILL.md`
- Claude Code: `.claude/skills/<skill-name>/SKILL.md`

## Public repository policy

Never commit credentials, tokens, customer data, private infrastructure details, or sensitive logs. Use example identifiers and sanitized evidence only.
