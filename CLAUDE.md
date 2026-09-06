# Repository Working Agreement

This repository contains public, cross-agent skills.

- Every skill lives in `skills/<skill-name>/SKILL.md` and follows the Agent Skills standard.
- Every skill has at least one group in `skills/skill-repository-sync/skill-manifest.json`. A skill without one stops the sync, so add the entry in the same change that adds the skill.
- Hosts receive skills through the generated delivery directory, never by editing it directly.
- Packaged scripts must run on Python 3.10; agent hosts are not all current. Verify against 3.10 rather than the development machine's version.
- Keep the required frontmatter limited to a valid `name` and a precise `description`; provider-specific optional fields must degrade safely in other agents.
- Put reusable scripts and documentation below the owning skill directory.
- Do not commit secrets, private URLs, customer data, credentials, internal logs, or machine-specific authentication state.
- Keep examples generic unless public project identifiers are intentionally part of the documentation.
- Do not hard-code deployment-specific hostnames, IP addresses, usernames, or absolute home paths in shared skills or examples. Use placeholders, `$HOME`, or documented environment variables instead.
- Validate every changed skill before publishing.
- Use a branch and pull request for material changes; do not edit deployed clones as a distribution mechanism.

## A rule carries a number and can be removed

A skill is read in full on every run that loads it, so every rule costs context
and compliance for as long as it exists. Rules that only accumulate make each
future project slower, which is the opposite of why they were written.

- **A new behavioural rule names the number it should move**, its current value,
  and when it will be re-checked. Point at the measurement that carries the
  figures instead of restating them in several places.
- **Rules about security or correctness need no number.** Those two are exempt.
  Anything else that cannot name a number is an opinion and does not become a
  rule.
- **A rule whose number has not moved across two measured waves is a removal
  candidate.** Remove it or sharpen it. Keeping it needs a stated reason, in the
  same place as the rule.
- **Removing a rule needs the evidence that introducing it needed.** Record it
  under `docs/decisions/` and mark the superseded decision, the way the existing
  decisions there already do.

See [the rule lifecycle decision](docs/decisions/rules-carry-a-number.md) for
what the missing half of this cost.
