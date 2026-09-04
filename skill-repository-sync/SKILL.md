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
6. installs the third-party skills declared in `upstream-skills.json` from their own upstream repositories;
7. validates every skill's `SKILL.md` metadata;
8. rolls back to the previous commit if installation or validation fails.

Report whether the repository was already current or name the old and new commit IDs. If the updater reports a dirty clone, remote mismatch, failed upstream install, validation failure, or missing executable, stop and report the blocker. Do not repair it with `git reset --hard`, change the remote, reinstall the updater, edit the deployment clone, or modify cron unless the user explicitly authorizes that maintenance.

## Skills installed from upstream

This repository does not vendor third-party skills. `upstream-skills.json` names each source repository, its pinned revision, and the skills to install, and the updater materializes them in the deployment clone. They are therefore present in every agent without being copied into this repository, and the clone stays clean because installed directories are excluded through the clone's own `.git/info/exclude`.

Change what is deployed by editing the manifest and letting the sync run, not by copying directories into the deployment clone. A skill removed from the manifest is deleted from the clone on the next run.

The deployed skills are shared by Codex through `~/.agents/skills` and by Claude Code through `~/.claude/skills`. Updating either path therefore updates both agents.

For installation, cron, logging, and failure-handling details, read [the automatic-update reference](references/automatic-updates.md).
