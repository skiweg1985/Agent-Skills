#!/usr/bin/env python3
"""Install third-party skills into a deployment clone from their upstream source.

The shared repository does not vendor these skills. It records where they come
from in `skill-repository-sync/upstream-skills.json`, and this helper materializes
them in the deployment clone so both Codex and Claude Code discover them as
top-level `<skill-name>/SKILL.md` directories.

Installed directories are kept out of Git through a managed block in the clone's
`.git/info/exclude`, so the updater's dirty check still protects real local work.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

MANIFEST = "skill-repository-sync/upstream-skills.json"
BLOCK_BEGIN = "# BEGIN agent-skills upstream (managed; do not edit)"
BLOCK_END = "# END agent-skills upstream"
NAME_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
REVISION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,127}$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(20)


def git(*args: str, binary: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], capture_output=True, text=not binary, check=False
    )


def git_or_fail(*args: str) -> str:
    result = git(*args)
    if result.returncode != 0:
        fail(f"git {args[0]} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def load_manifest(repo: Path) -> list[dict]:
    path = repo / MANIFEST
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{MANIFEST} is not valid JSON: {exc}")
    if data.get("schemaVersion") != 1:
        fail(f"{MANIFEST}: unsupported schemaVersion {data.get('schemaVersion')!r}")
    sources = data.get("sources")
    if not isinstance(sources, list):
        fail(f"{MANIFEST}: 'sources' must be a list")
    for source in sources:
        for field in ("id", "repository", "revision", "skillRoot", "skills"):
            if field not in source:
                fail(f"{MANIFEST}: source is missing '{field}'")
        if not NAME_RE.fullmatch(source["id"]):
            fail(f"{MANIFEST}: invalid source id {source['id']!r}")
        if not source["repository"].startswith("https://"):
            fail(f"{MANIFEST}: source {source['id']} must use an https repository URL")
        if not REVISION_RE.fullmatch(source["revision"]):
            fail(f"{MANIFEST}: source {source['id']} has an invalid revision")
        if not isinstance(source["skills"], list) or not source["skills"]:
            fail(f"{MANIFEST}: source {source['id']} lists no skills")
        for name in source["skills"]:
            if not isinstance(name, str) or not NAME_RE.fullmatch(name):
                fail(f"{MANIFEST}: invalid skill name {name!r} in source {source['id']}")
    return sources


def planned_names(sources: list[dict]) -> list[str]:
    owner: dict[str, str] = {}
    for source in sources:
        for name in source["skills"]:
            if name in owner:
                fail(f"skill {name!r} is claimed by both {owner[name]} and {source['id']}")
            owner[name] = source["id"]
    return sorted(owner)


def write_exclude_block(repo: Path, names: list[str]) -> None:
    """Keep managed directories out of `git status` without touching .gitignore."""
    exclude = repo / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    kept: list[str] = []
    inside = False
    for line in existing.splitlines():
        if line.strip() == BLOCK_BEGIN:
            inside = True
        elif line.strip() == BLOCK_END:
            inside = False
        elif not inside:
            kept.append(line)
    while kept and not kept[-1].strip():
        kept.pop()
    block = [BLOCK_BEGIN, *(f"/{name}/" for name in names), BLOCK_END]
    exclude.write_text("\n".join([*kept, *block]) + "\n", encoding="utf-8")


def resolve_revision(cache: Path, source: dict) -> str:
    revision = source["revision"]
    for candidate in (revision, f"refs/remotes/origin/{revision}"):
        resolved = git(
            "-C", str(cache), "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}"
        ).stdout.strip()
        if resolved:
            return resolved
    fail(f"source {source['id']}: revision {revision!r} not found upstream")
    raise AssertionError("unreachable")


def upstream_directories(cache: Path, source: dict, revision: str) -> dict[str, str]:
    """Map skill name to its directory at `revision`, wherever upstream files it."""
    prefix = f"{source['skillRoot']}/"
    listing = git_or_fail("-C", str(cache), "ls-tree", "-r", "--name-only", revision)
    found: dict[str, str] = {}
    for line in listing.splitlines():
        if not line.startswith(prefix) or not line.endswith("/SKILL.md"):
            continue
        directory = line.rsplit("/", 1)[0]
        found[directory.rsplit("/", 1)[-1]] = directory
    return found


def sync_source(repo: Path, source: dict, cache_root: Path) -> list[str]:
    cache = cache_root / source["id"]
    if not (cache / ".git").is_dir():
        shutil.rmtree(cache, ignore_errors=True)
        cache.parent.mkdir(parents=True, exist_ok=True)
        git_or_fail("clone", "--quiet", source["repository"], str(cache))

    actual = git("-C", str(cache), "remote", "get-url", "origin").stdout.strip()
    if actual != source["repository"]:
        fail(f"cached clone for {source['id']} has unexpected remote {actual!r}")
    git_or_fail("-C", str(cache), "fetch", "--quiet", "--prune", "--tags", "origin")

    revision = resolve_revision(cache, source)
    available = upstream_directories(cache, source, revision)

    installed: list[str] = []
    for name in sorted(source["skills"]):
        if name not in available:
            fail(f"source {source['id']}: skill {name!r} not found at {revision[:12]}")
        archive = git(
            "-C", str(cache), "archive", "--format=tar", f"{revision}:{available[name]}",
            binary=True,
        )
        if archive.returncode != 0:
            fail(f"source {source['id']}: cannot export {name!r}")
        with tempfile.TemporaryDirectory(dir=str(repo)) as staging:
            staged = Path(staging) / name
            staged.mkdir()
            extract = subprocess.run(
                ["tar", "-x", "-C", str(staged)],
                input=archive.stdout, capture_output=True, check=False,
            )
            if extract.returncode != 0:
                fail(f"source {source['id']}: cannot unpack {name!r}: "
                     f"{extract.stderr.decode(errors='replace').strip()}")
            if not (staged / "SKILL.md").exists():
                fail(f"source {source['id']}: exported {name!r} has no SKILL.md")
            destination = repo / name
            if destination.exists():
                shutil.rmtree(destination)
            shutil.move(str(staged), str(destination))
        installed.append(name)

    source["resolvedRevision"] = revision
    return installed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--record", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    cache_root = Path(args.cache_root).expanduser()
    record_path = Path(args.record).expanduser()

    sources = load_manifest(repo)
    names = planned_names(sources)

    previous: list[str] = []
    if record_path.exists():
        try:
            stored = json.loads(record_path.read_text(encoding="utf-8"))
            previous = [n for n in stored.get("skills", []) if isinstance(n, str)]
        except (json.JSONDecodeError, AttributeError):
            previous = []

    if not names and not previous:
        print("No upstream skill sources are configured.")
        return 0

    # Reserve the exclude entries first, so the next dirty check stays quiet even
    # if this run is interrupted part-way through.
    write_exclude_block(repo, sorted(set(names) | set(previous)))

    if names:
        tracked = git_or_fail("-C", str(repo), "ls-files", "--", *names).split()
        if tracked:
            fail("the shared repository still tracks upstream skill directories "
                 f"(for example {tracked[0]}); remove them there first")

    installed: list[str] = []
    for source in sources:
        installed.extend(sync_source(repo, source, cache_root))

    removed = 0
    for stale in sorted(set(previous) - set(installed)):
        target = repo / stale
        if target.is_dir():
            shutil.rmtree(target)
            removed += 1

    write_exclude_block(repo, sorted(installed))
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps({
        "schemaVersion": 1,
        "installedAt": datetime.now(UTC).isoformat(),
        "skills": sorted(installed),
        "sources": [
            {"id": s["id"], "repository": s["repository"],
             "revision": s["revision"], "resolvedRevision": s.get("resolvedRevision")}
            for s in sources
        ],
    }, indent=2) + "\n", encoding="utf-8")

    print(f"Installed {len(installed)} upstream skills"
          + (f"; removed {removed} no longer in the manifest" if removed else "") + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
