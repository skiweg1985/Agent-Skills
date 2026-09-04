# Automatic update operation

The deployed repository is updated by a trusted copy of the updater installed outside the clone:

```bash
install -Dm755 \
  ~/.agents/skills/skill-repository-sync/scripts/update-agent-skills.sh \
  ~/.local/bin/update-agent-skills
```

Recommended user crontab entry:

```cron
*/15 * * * * $HOME/.local/bin/update-agent-skills >> $HOME/.local/state/agent-skills/update.log 2>&1
```

## Manual checks

```bash
~/.local/bin/update-agent-skills
git -C ~/.agents/skills status --short --branch
git -C ~/.agents/skills log -1 --oneline
```

## Upstream skills

Third-party skills are not stored in this repository. `skill-repository-sync/upstream-skills.json`
declares each source repository, its pinned revision, and the skills to install; the
updater materializes them in the deployment clone on every run.

```bash
python3 ~/.agents/skills/skill-repository-sync/scripts/install-upstream-skills.py \
  --repo ~/.agents/skills \
  --cache-root ~/.local/state/agent-skills/upstream \
  --record ~/.local/state/agent-skills/installed-upstream.json
```

- Source clones are cached under `~/.local/state/agent-skills/upstream/<source-id>`.
- What was installed is recorded in `~/.local/state/agent-skills/installed-upstream.json`.
  A skill dropped from the manifest is removed from the clone on the next run.
- Installed directories are listed in a managed block in the clone's `.git/info/exclude`,
  so they never make the deployment clone look dirty. Do not edit that block by hand.
- `revision` may be a commit SHA (reproducible; the default) or a branch name such as
  `main` (always the newest upstream state). Change it in the manifest, not on the host.

To add a source, append an entry with `id`, an `https` `repository`, a `revision`, the
`skillRoot` directory to search, and the `skills` to install. To stop deploying a skill,
remove it from the manifest; the next run deletes it from the clone.

## Failure behavior

- A concurrent update exits without starting a second pull.
- A dirty clone is not modified.
- An unexpected `origin` URL is rejected.
- Non-fast-forward history is rejected.
- A failing upstream install rolls the deployment back to its previous commit (exit 15).
- Invalid or duplicate skill metadata causes the deployment to roll back to its previous commit (exit 14).
- Validation covers the top-level directories the agents discover and any skill published under `skills/`. The latter are not discovered by Codex or Claude Code; validating them keeps a broken one from shipping unnoticed. A name reused across both is reported as a duplicate.
- A skill name claimed by two sources, a missing upstream skill, an unreachable revision,
  or a manifest entry that is still tracked in Git stops the run before anything is copied.
- Cron output is retained in `~/.local/state/agent-skills/update.log`.

The updater installed in `~/.local/bin` does not automatically replace itself. Updating the updater executable requires an explicit maintenance action after review. This prevents an ordinary repository pull from silently changing the program executed by cron.
