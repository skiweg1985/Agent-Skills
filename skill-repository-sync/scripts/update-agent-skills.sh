#!/usr/bin/env bash
set -euo pipefail

repo="${AGENT_SKILLS_DIR:-$HOME/.agents/skills}"
branch="${AGENT_SKILLS_BRANCH:-main}"
expected_remote="${AGENT_SKILLS_REMOTE:-https://github.com/skiweg1985/Agent-Skills.git}"
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-skills"
lock_file="${XDG_RUNTIME_DIR:-/tmp}/agent-skills-update-${UID}.lock"

mkdir -p "$state_dir"
exec 9>"$lock_file"
if ! flock -n 9; then
  printf 'Another Agent-Skills update is already running.\n'
  exit 0
fi

if [[ ! -d "$repo/.git" ]]; then
  printf 'ERROR: %s is not a Git deployment clone.\n' "$repo" >&2
  exit 10
fi

actual_remote="$(git -C "$repo" remote get-url origin 2>/dev/null || true)"
if [[ "$actual_remote" != "$expected_remote" ]]; then
  printf 'ERROR: unexpected origin remote: %s\n' "$actual_remote" >&2
  exit 11
fi

if [[ -n "$(git -C "$repo" status --porcelain --untracked-files=normal)" ]]; then
  printf 'ERROR: deployment clone is dirty; refusing to overwrite local work.\n' >&2
  exit 12
fi

old_commit="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" fetch --quiet --prune origin "$branch"
new_commit="$(git -C "$repo" rev-parse FETCH_HEAD)"

if [[ "$old_commit" == "$new_commit" ]]; then
  printf 'Agent-Skills already current at %s.\n' "${old_commit:0:12}"
  exit 0
fi

if ! git -C "$repo" merge-base --is-ancestor "$old_commit" "$new_commit"; then
  printf 'ERROR: origin/%s is not a fast-forward from the deployed commit.\n' "$branch" >&2
  exit 13
fi

git -C "$repo" merge --quiet --ff-only "$new_commit"

if ! python3 - "$repo" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
name_re = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
seen = set()
errors = []
skills = []

for skill_file in sorted(root.glob("*/SKILL.md")):
    skills.append(skill_file)
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{skill_file}: missing YAML frontmatter")
        continue
    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        errors.append(f"{skill_file}: malformed YAML frontmatter")
        continue
    fields = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"').strip("'")
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name_re.fullmatch(name):
        errors.append(f"{skill_file}: invalid or missing name")
    if name and name != skill_file.parent.name:
        errors.append(f"{skill_file}: name does not match directory")
    if not description:
        errors.append(f"{skill_file}: missing description")
    if name in seen:
        errors.append(f"{skill_file}: duplicate skill name {name}")
    seen.add(name)

if not skills:
    errors.append("repository contains no skills")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(skills)} shared skills.")
PY
then
  printf 'ERROR: validation failed; restoring %s.\n' "${old_commit:0:12}" >&2
  git -C "$repo" reset --quiet --hard "$old_commit"
  exit 14
fi

printf 'Updated Agent-Skills from %s to %s.\n' "${old_commit:0:12}" "${new_commit:0:12}"
