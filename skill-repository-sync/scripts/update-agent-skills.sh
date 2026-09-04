#!/usr/bin/env bash
set -euo pipefail

repo="${AGENT_SKILLS_DIR:-$HOME/.agents/skills}"
branch="${AGENT_SKILLS_BRANCH:-main}"
expected_remote="${AGENT_SKILLS_REMOTE:-https://github.com/skiweg1985/Agent-Skills.git}"
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-skills"
lock_file="${XDG_RUNTIME_DIR:-/tmp}/agent-skills-update-${UID}.lock"
cache_root="$state_dir/upstream"
install_record="$state_dir/installed-upstream.json"
installer="$repo/skill-repository-sync/scripts/install-upstream-skills.py"

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

install_upstream() {
  if [[ ! -f "$installer" ]]; then
    return 0
  fi
  python3 "$installer" \
    --repo "$repo" \
    --cache-root "$cache_root" \
    --record "$install_record"
}

validate_skills() {
  python3 - "$repo" <<'PY'
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
name_re = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
seen = {}
errors = []

# Top-level directories are what Codex and Claude Code discover. Directories
# under skills/ are published for other consumers and are deliberately not
# discovered here, but they are validated too so a broken one cannot ship
# unnoticed.
discovered = sorted(root.glob("*/SKILL.md"))
nested = sorted(root.glob("skills/*/SKILL.md"))

for skill_file in discovered + nested:
    rel = skill_file.relative_to(root)
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        errors.append(f"{rel}: missing YAML frontmatter")
        continue
    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        errors.append(f"{rel}: malformed YAML frontmatter")
        continue
    fields = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"').strip("'")
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name_re.fullmatch(name):
        errors.append(f"{rel}: invalid or missing name")
    if name and name != skill_file.parent.name:
        errors.append(f"{rel}: name does not match directory")
    if not description:
        errors.append(f"{rel}: missing description")
    if name:
        if name in seen:
            errors.append(f"{rel}: duplicate skill name {name} (also {seen[name]})")
        else:
            seen[name] = rel

if not discovered:
    errors.append("repository contains no discoverable skills")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(discovered)} discoverable and {len(nested)} nested skills.")
PY
}

old_commit="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" fetch --quiet --prune origin "$branch"
new_commit="$(git -C "$repo" rev-parse FETCH_HEAD)"

if [[ "$old_commit" == "$new_commit" ]]; then
  printf 'Agent-Skills already current at %s.\n' "${old_commit:0:12}"
else
  if ! git -C "$repo" merge-base --is-ancestor "$old_commit" "$new_commit"; then
    printf 'ERROR: origin/%s is not a fast-forward from the deployed commit.\n' "$branch" >&2
    exit 13
  fi
  git -C "$repo" merge --quiet --ff-only "$new_commit"
fi

# Third-party skills are installed from their own upstream, not vendored here.
if ! install_upstream; then
  if [[ "$old_commit" != "$new_commit" ]]; then
    printf 'ERROR: upstream skill install failed; restoring %s.\n' "${old_commit:0:12}" >&2
    git -C "$repo" reset --quiet --hard "$old_commit"
    install_upstream || printf 'WARNING: upstream skills may be inconsistent.\n' >&2
  else
    printf 'ERROR: upstream skill install failed.\n' >&2
  fi
  exit 15
fi

if ! validate_skills; then
  printf 'ERROR: validation failed; restoring %s.\n' "${old_commit:0:12}" >&2
  git -C "$repo" reset --quiet --hard "$old_commit"
  install_upstream || printf 'WARNING: upstream skills may be inconsistent.\n' >&2
  exit 14
fi

if [[ "$old_commit" == "$new_commit" ]]; then
  exit 0
fi

printf 'Updated Agent-Skills from %s to %s.\n' "${old_commit:0:12}" "${new_commit:0:12}"
