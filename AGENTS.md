# Repository Working Agreement

This repository contains public, cross-agent skills.

- Every skill lives in `<skill-name>/SKILL.md` and follows the Agent Skills standard.
- A skill intended for the Hermes tap instead lives in `skills/<skill-name>/SKILL.md`; that path is indexed by the tap and is not discovered by Codex or Claude Code. See the README for which surface to choose.
- Keep the required frontmatter limited to a valid `name` and a precise `description`; provider-specific optional fields must degrade safely in other agents.
- Put reusable scripts and documentation below the owning skill directory.
- Do not commit secrets, private URLs, customer data, credentials, internal logs, or machine-specific authentication state.
- Keep examples generic unless public project identifiers are intentionally part of the documentation.
- Do not hard-code deployment-specific hostnames, IP addresses, usernames, or absolute home paths in shared skills or examples. Use placeholders, `$HOME`, or documented environment variables instead.
- Validate every changed skill before publishing.
- Use a branch and pull request for material changes; do not edit deployed clones as a distribution mechanism.
