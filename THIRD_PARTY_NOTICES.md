# Third-party notices

## Matt Pocock Skills

This repository does not vendor these skills. It records where they come from, and
the updater installs them into a deployment clone directly from upstream.

- Source: [mattpocock/skills](https://github.com/mattpocock/skills)
- License: MIT, by Matt Pocock — full text in [`licenses/mattpocock-skills-MIT.txt`](licenses/mattpocock-skills-MIT.txt)
- Pinned revision and skill inventory: [`skill-repository-sync/upstream-skills.json`](skill-repository-sync/upstream-skills.json)

The manifest is the single source of truth for which skills are installed and at
which revision. Upstream groups its skills into category directories; the installer
flattens that layer so each one stays discoverable as `<skill-name>/SKILL.md`.
Skill contents are installed unchanged.

Eight of the installed skills sit in the upstream `in-progress` category:
`claude-handoff`, `implement-spec`, `loop-me`, `retro`, `setup-ts-deep-modules`,
`writing-beats`, `writing-fragments`, `writing-shape`. Remove them from the
manifest if you would rather not deploy work upstream still marks as unfinished.
