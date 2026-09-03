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

## Failure behavior

- A concurrent update exits without starting a second pull.
- A dirty clone is not modified.
- An unexpected `origin` URL is rejected.
- Non-fast-forward history is rejected.
- Invalid or duplicate skill metadata causes the deployment to roll back to its previous commit.
- Cron output is retained in `~/.local/state/agent-skills/update.log`.

The updater installed in `~/.local/bin` does not automatically replace itself. Updating the updater executable requires an explicit maintenance action after review. This prevents an ordinary repository pull from silently changing the program executed by cron.
