---
name: skill-repository-sync
description: Safely check for and install updates from the shared skiweg1985/Agent-Skills GitHub repository on an agent host. Use when asked to update, refresh, pull, or synchronize the shared Codex and Claude Code skills.
---

# Sync the Shared Skill Repository

Use the host-installed updater rather than running arbitrary Git reset or pull commands yourself:

```bash
$HOME/.local/bin/update-agent-skills
```

The updater:

1. locks against concurrent updates;
2. verifies that the deployment clone uses the expected GitHub remote;
3. refuses to overwrite local or untracked changes;
4. fetches `origin/main`;
5. permits only a fast-forward update;
6. validates every skill's `SKILL.md` metadata;
7. rolls back to the previous commit if validation fails.

Report whether the repository was already current or name the old and new commit IDs. If the updater reports a dirty clone, remote mismatch, validation failure, or missing executable, stop and report the blocker. Do not repair it with `git reset --hard`, change the remote, reinstall the updater, edit the deployment clone, or modify cron unless the user explicitly authorizes that maintenance.

The deployed skills are shared by Codex through `~/.agents/skills` and by Claude Code through `~/.claude/skills`. Updating either path therefore updates both agents.

For installation, cron, logging, and failure-handling details, read [the automatic-update reference](references/automatic-updates.md).
