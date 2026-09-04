# Third-party notices

## Matt Pocock Skills

This repository does not vendor these skills. It records where they come from, and
the updater installs them into a deployment clone directly from upstream.

- Source: [mattpocock/skills](https://github.com/mattpocock/skills)
- License: MIT, by Matt Pocock — full text in [`licenses/mattpocock-skills-MIT.txt`](licenses/mattpocock-skills-MIT.txt)
- Pinned revision and skill inventory: [`skills/skill-repository-sync/skill-manifest.json`](skills/skill-repository-sync/skill-manifest.json)

The manifest is the single source of truth for which skills exist, which group
each belongs to, and at which revision an upstream one is pinned. A host receives
only those whose group matches its declared roles. Upstream groups its skills into category directories; the installer
flattens that layer so each one stays discoverable as `<skill-name>/SKILL.md`.
Skill contents are installed unchanged.

Eight of the installed skills sit in the upstream `in-progress` category:
`claude-handoff`, `implement-spec`, `loop-me`, `retro`, `setup-ts-deep-modules`,
`writing-beats`, `writing-fragments`, `writing-shape`. Remove them from the
manifest if you would rather not deploy work upstream still marks as unfinished.
