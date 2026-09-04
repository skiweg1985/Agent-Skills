#!/usr/bin/env bash
set -euo pipefail

# The clone and the delivery directory are separate. The clone holds every skill;
# the delivery directory holds only what this host's roles select.
repo="${AGENT_SKILLS_REPO:-$HOME/.local/share/agent-skills}"
target="${AGENT_SKILLS_DIR:-$HOME/.agents/skills}"
branch="${AGENT_SKILLS_BRANCH:-main}"
expected_remote="${AGENT_SKILLS_REMOTE:-https://github.com/skiweg1985/Agent-Skills.git}"
config_file="${AGENT_SKILLS_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/agent-skills/host.conf}"
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/agent-skills"
lock_file="${XDG_RUNTIME_DIR:-/tmp}/agent-skills-update-${UID}.lock"
cache_root="$state_dir/upstream"
status_file="$state_dir/sync-status.json"
installer="$repo/skills/skill-repository-sync/scripts/install-skills.py"

mkdir -p "$state_dir"
exec 9>"$lock_file"
if ! flock -n 9; then
  printf 'Another Agent-Skills update is already running.\n'
  exit 0
fi

record_failure() {
  python3 - "$status_file" "$1" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
path, reason = Path(sys.argv[1]), sys.argv[2]
status = {}
if path.exists():
    try:
        status = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        status = {}
status["schemaVersion"] = 1
status["lastRunAt"] = datetime.now(timezone.utc).isoformat()
status["outcome"] = "failed"
status["failureReason"] = reason
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
PY
}

die() {
  printf 'ERROR: %s\n' "$1" >&2
  record_failure "$1"
  exit "$2"
}

# Roles decide what this host receives. The default is base alone, so a host is
# never a coordinator by accident.
roles="${AGENT_SKILLS_ROLES:-}"
if [[ -z "$roles" && -f "$config_file" ]]; then
  roles="$(
    grep -E '^[[:space:]]*AGENT_SKILLS_ROLES[[:space:]]*=' "$config_file" 2>/dev/null |
      tail -n1 | cut -d= -f2- |
      sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' || true
  )"
fi
roles="${roles:-base}"

[[ -d "$repo/.git" ]] || die "$repo is not a Git clone of the skill repository" 10

actual_remote="$(git -C "$repo" remote get-url origin 2>/dev/null || true)"
[[ "$actual_remote" == "$expected_remote" ]] || die "unexpected origin remote: $actual_remote" 11

if [[ -n "$(git -C "$repo" status --porcelain --untracked-files=normal)" ]]; then
  die "clone is dirty; refusing to overwrite local work" 12
fi

install_skills() {
  python3 "$installer" \
    --repo "$repo" \
    --target "$target" \
    --cache-root "$cache_root" \
    --roles "$roles" \
    --status "$status_file"
}

validate_skills() {
  python3 - "$repo" "$target" <<'PY'
import re
import sys
from pathlib import Path

name_re = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
errors = []


def check(files, label):
    seen = {}
    for skill_file in files:
        rel = f"{label}:{skill_file.parent.name}"
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
        if not name_re.fullmatch(name):
            errors.append(f"{rel}: invalid or missing name")
        if name and name != skill_file.parent.name:
            errors.append(f"{rel}: name does not match directory")
        if not fields.get("description", ""):
            errors.append(f"{rel}: missing description")
        if name and name in seen:
            errors.append(f"{rel}: duplicate skill name {name}")
        seen[name] = rel


# The clone is the source of truth and is validated whole, so a skill this host
# does not receive still cannot ship broken to a host that does.
source = sorted(Path(sys.argv[1]).resolve().glob("skills/*/SKILL.md"))
delivered = sorted(Path(sys.argv[2]).expanduser().resolve().glob("*/SKILL.md"))

check(source, "clone")
check(delivered, "delivered")

if not source:
    errors.append("the clone contains no skills")
if not delivered:
    errors.append("nothing was delivered for this host's roles")
if errors:
    print("\n".join(errors), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(source)} skills in the clone, {len(delivered)} delivered.")
PY
}

old_commit="$(git -C "$repo" rev-parse HEAD)"
git -C "$repo" fetch --quiet --prune origin "$branch"
new_commit="$(git -C "$repo" rev-parse FETCH_HEAD)"

if [[ "$old_commit" == "$new_commit" ]]; then
  printf 'Agent-Skills already current at %s.\n' "${old_commit:0:12}"
else
  if ! git -C "$repo" merge-base --is-ancestor "$old_commit" "$new_commit"; then
    die "origin/$branch is not a fast-forward from the deployed commit" 13
  fi
  git -C "$repo" merge --quiet --ff-only "$new_commit"
fi

restore() {
  if [[ "$old_commit" != "$new_commit" ]]; then
    git -C "$repo" reset --quiet --hard "$old_commit"
    install_skills >/dev/null || printf 'WARNING: delivered skills may be inconsistent.\n' >&2
  fi
}

if ! install_skills; then
  printf 'ERROR: skill install failed; restoring %s.\n' "${old_commit:0:12}" >&2
  restore
  die "skill install failed" 15
fi

if ! validate_skills; then
  printf 'ERROR: validation failed; restoring %s.\n' "${old_commit:0:12}" >&2
  restore
  die "validation failed" 14
fi

if [[ "$old_commit" != "$new_commit" ]]; then
  printf 'Updated Agent-Skills from %s to %s.\n' "${old_commit:0:12}" "${new_commit:0:12}"
fi
