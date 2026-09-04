#!/usr/bin/env python3
"""Build a host's skill delivery directory from the manifest and its declared roles.

The Git clone and the delivery directory are separate. The clone holds every
skill; the delivery directory holds only what this host's roles select, so a
coordinator does not merely refrain from using implementation skills — it does
not have them.

Own skills are copied from the clone. Skills belonging to a declared source are
exported from that upstream repository at its pinned revision. A skill with no
group aborts the run, so nothing is installed by accident and no upstream source
can introduce a skill without a deliberate assignment.

A host may also keep skills of its own — ones that name real addresses, paths or
identifiers the shared repository forbids. They live in their own directory, so
this rebuild cannot destroy them, and are linked into the delivery directory
after it is built. A shared skill of the same name always wins.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = "skills/skill-repository-sync/skill-manifest.json"
SKILL_ROOT = "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
REVISION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")
LOCAL = "local"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(20)


def git(*args: str, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=not binary, check=False)


def git_or_fail(*args: str) -> str:
    result = git(*args)
    if result.returncode != 0:
        fail(f"git {args[0]} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def load_manifest(repo: Path) -> dict:
    path = repo / MANIFEST
    if not path.exists():
        fail(f"{MANIFEST} not found in {repo}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{MANIFEST} is not valid JSON: {exc}")
    if data.get("schemaVersion") != 2:
        fail(f"{MANIFEST}: unsupported schemaVersion {data.get('schemaVersion')!r}")

    roles = data.get("roles")
    if not isinstance(roles, dict) or not roles:
        fail(f"{MANIFEST}: 'roles' must be a non-empty object")

    sources = {}
    for source in data.get("sources", []):
        for field in ("id", "repository", "revision", "skillRoot"):
            if field not in source:
                fail(f"{MANIFEST}: source is missing '{field}'")
        if not NAME_RE.fullmatch(source["id"]) or source["id"] == LOCAL:
            fail(f"{MANIFEST}: invalid source id {source['id']!r}")
        if not source["repository"].startswith("https://"):
            fail(f"{MANIFEST}: source {source['id']} must use an https repository URL")
        if not REVISION_RE.fullmatch(source["revision"]):
            fail(f"{MANIFEST}: source {source['id']} has an invalid revision")
        sources[source["id"]] = source

    skills = data.get("skills")
    if not isinstance(skills, dict) or not skills:
        fail(f"{MANIFEST}: 'skills' must be a non-empty object")
    for name, meta in skills.items():
        if not NAME_RE.fullmatch(name):
            fail(f"{MANIFEST}: invalid skill name {name!r}")
        groups = meta.get("groups")
        if not isinstance(groups, list) or not groups:
            fail(f"{MANIFEST}: skill {name!r} declares no group; assign one before syncing")
        unknown = [g for g in groups if g not in roles]
        if unknown:
            fail(f"{MANIFEST}: skill {name!r} names undefined group(s) {', '.join(unknown)}")
        origin = meta.get("source", LOCAL)
        if origin != LOCAL and origin not in sources:
            fail(f"{MANIFEST}: skill {name!r} names undeclared source {origin!r}")

    data["_sources"] = sources
    return data


def ungrouped_local_skills(repo: Path, manifest: dict) -> list[str]:
    """A skill in the clone that the manifest never mentions would ship nowhere."""
    present = {p.parent.name for p in (repo / SKILL_ROOT).glob("*/SKILL.md")}
    return sorted(present - set(manifest["skills"]))


def selected(manifest: dict, roles: list[str]) -> dict[str, dict]:
    return {
        name: meta
        for name, meta in manifest["skills"].items()
        if set(meta["groups"]) & set(roles)
    }


def export_local(repo: Path, name: str, destination: Path) -> None:
    source = repo / SKILL_ROOT / name
    if not (source / "SKILL.md").exists():
        fail(f"skill {name!r} is in the manifest but not in {SKILL_ROOT}/ of the clone")
    shutil.copytree(source, destination)


def upstream_directories(cache: Path, source: dict, revision: str) -> dict[str, str]:
    prefix = f"{source['skillRoot']}/"
    listing = git_or_fail("-C", str(cache), "ls-tree", "-r", "--name-only", revision)
    found: dict[str, str] = {}
    for line in listing.splitlines():
        if line.startswith(prefix) and line.endswith("/SKILL.md"):
            directory = line.rsplit("/", 1)[0]
            found[directory.rsplit("/", 1)[-1]] = directory
    return found


def prepare_source(source: dict, cache_root: Path) -> tuple[Path, str, dict[str, str]]:
    cache = cache_root / source["id"]
    if not (cache / ".git").is_dir():
        shutil.rmtree(cache, ignore_errors=True)
        cache.parent.mkdir(parents=True, exist_ok=True)
        git_or_fail("clone", "--quiet", source["repository"], str(cache))
    actual = git("-C", str(cache), "remote", "get-url", "origin").stdout.strip()
    if actual != source["repository"]:
        fail(f"cached clone for {source['id']} has unexpected remote {actual!r}")
    git_or_fail("-C", str(cache), "fetch", "--quiet", "--prune", "--tags", "origin")

    revision = source["revision"]
    resolved = ""
    for candidate in (revision, f"refs/remotes/origin/{revision}"):
        resolved = git("-C", str(cache), "rev-parse", "--verify", "--quiet",
                       f"{candidate}^{{commit}}").stdout.strip()
        if resolved:
            break
    if not resolved:
        fail(f"source {source['id']}: revision {revision!r} not found upstream")
    return cache, resolved, upstream_directories(cache, source, resolved)


def export_upstream(cache: Path, revision: str, upstream_dir: str,
                    source_id: str, name: str, destination: Path) -> None:
    archive = git("-C", str(cache), "archive", "--format=tar",
                  f"{revision}:{upstream_dir}", binary=True)
    if archive.returncode != 0:
        fail(f"source {source_id}: cannot export {name!r}")
    destination.mkdir(parents=True)
    extract = subprocess.run(["tar", "-x", "-C", str(destination)],
                             input=archive.stdout, capture_output=True, check=False)
    if extract.returncode != 0:
        fail(f"source {source_id}: cannot unpack {name!r}: "
             f"{extract.stderr.decode(errors='replace').strip()}")


MARKER = ".agent-skills-managed.json"


def marker_of(directory: Path) -> dict | None:
    """Return the sync's ownership marker for this skill, or None if it has none.

    The delivery directory is shared ground: agents create skills here through
    their own tooling, and people drop them in by hand. The marker is how this
    tool tells what it placed from what it merely found, so it can update and
    remove its own without ever touching anyone else's.
    """
    path = directory / MARKER
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # A marker we cannot read is still a marker we wrote.
        return {}


def install_skill(target: Path, name: str, build, marker: dict) -> None:
    """Materialize one skill and swap it into place, so it is never half-written."""
    staging = Path(tempfile.mkdtemp(dir=str(target), prefix=f".{name}-"))
    try:
        build(staging / name)
        if not (staging / name / "SKILL.md").is_file():
            fail(f"exported {name!r} has no SKILL.md")
        (staging / name / MARKER).write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        destination = target / name
        previous = staging / f"{name}.previous"
        if destination.exists():
            destination.rename(previous)
        (staging / name).rename(destination)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="the Git clone")
    parser.add_argument("--target", required=True, help="the shared delivery directory")
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--roles", required=True, help="space-separated role names")
    parser.add_argument("--status", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    target = Path(args.target).expanduser()
    cache_root = Path(args.cache_root).expanduser()
    status_path = Path(args.status).expanduser()

    manifest = load_manifest(repo)
    roles = [r for r in args.roles.split() if r]
    if not roles:
        roles = list(manifest.get("defaultRoles") or ["base"])
    unknown = [r for r in roles if r not in manifest["roles"]]
    if unknown:
        fail(f"host declares undefined role(s): {', '.join(unknown)}")

    orphans = ungrouped_local_skills(repo, manifest)
    if orphans:
        fail(f"skills present in the clone but absent from the manifest: {', '.join(orphans)}; "
             "assign a group before syncing")

    chosen = selected(manifest, roles)
    if not chosen:
        fail(f"roles {' '.join(roles)} select no skills")

    target.mkdir(parents=True, exist_ok=True)
    # Who owns what is already here. Anything without our marker belongs to
    # someone else — an agent's skill-creation tool, or a person — and is left
    # exactly as it is.
    present = {
        entry.name: marker_of(entry)
        for entry in target.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    }
    # Skills installed before markers existed carry none. The previous status
    # record names them, so adopt those rather than mistaking our own earlier
    # work for someone else's and refusing to touch it ever again.
    previously_installed = set()
    if status_path.exists():
        try:
            record = json.loads(status_path.read_text(encoding="utf-8"))
            previously_installed = {n for n in record.get("skills", []) if isinstance(n, str)}
        except json.JSONDecodeError:
            previously_installed = set()
    adopted = sorted(
        name for name, mark in present.items()
        if mark is None and name in previously_installed
    )
    foreign = sorted(
        name for name, mark in present.items()
        if mark is None and name not in previously_installed
    )
    conflicts = sorted(name for name in chosen if name in foreign)

    prepared: dict[str, tuple[Path, str, dict[str, str]]] = {}
    installed: list[str] = []
    for name in sorted(chosen):
        if name in conflicts:
            continue
        origin = chosen[name].get("source", LOCAL)
        marker = {
            "schemaVersion": 1,
            "installedAt": datetime.now(timezone.utc).isoformat(),
            "source": origin,
            "groups": chosen[name]["groups"],
        }
        if origin == LOCAL:
            marker["commit"] = git("-C", str(repo), "rev-parse", "HEAD").stdout.strip()
            install_skill(target, name,
                          lambda dest, n=name: export_local(repo, n, dest), marker)
        else:
            if origin not in prepared:
                prepared[origin] = prepare_source(manifest["_sources"][origin], cache_root)
            cache, revision, available = prepared[origin]
            if name not in available:
                fail(f"source {origin}: skill {name!r} not found at {revision[:12]}")
            marker["revision"] = revision
            install_skill(target, name,
                          lambda dest, n=name, c=cache, r=revision, a=available, o=origin:
                              export_upstream(c, r, a[n], o, n, dest), marker)
        installed.append(name)

    # Remove only what we installed and no longer select. A skill we never placed
    # is never ours to delete.
    removed = []
    for name, mark in sorted(present.items()):
        if mark is not None and name not in chosen:
            shutil.rmtree(target / name)
            removed.append(name)

    status_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    status = {}
    if status_path.exists():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {}
    status.update({
        "schemaVersion": 1,
        "lastRunAt": now,
        "lastSuccessAt": now,
        "outcome": "ok",
        "roles": roles,
        "target": str(target),
        "commit": git("-C", str(repo), "rev-parse", "HEAD").stdout.strip(),
        "skillCount": len(installed),
        "skills": sorted(installed),
        "removed": removed,
        "unmanaged": foreign,
        "adopted": adopted,
        "conflicts": conflicts,
        "sources": [
            {"id": sid, "revision": manifest["_sources"][sid]["revision"],
             "resolvedRevision": prepared[sid][1]}
            for sid in sorted(prepared)
        ],
    })
    status_path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {len(installed)} skills for role(s) {' '.join(roles)} into {target}.")
    if removed:
        print(f"Removed {len(removed)} no longer selected: {', '.join(removed)}.")
    if adopted:
        print(f"Adopted {len(adopted)} skill(s) installed before markers existed.")
    if foreign:
        print(f"Left {len(foreign)} skill(s) not managed here untouched: {', '.join(foreign)}.")
    for name in conflicts:
        print(f"WARNING: {name} is selected for this host but a skill of that name is "
              "already here and was not placed by the sync; it was left alone and the "
              "shared version was not installed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
