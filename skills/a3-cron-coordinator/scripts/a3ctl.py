#!/usr/bin/env python3
"""Local, opt-in state for the public A3 coordinator skill.

This tool never creates Cron jobs or starts agents. It only creates and records
local project activation metadata; the coordinator performs external actions.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def now() -> str:
    return datetime.now(UTC).isoformat()


def state_root(value: str | None) -> Path:
    base = value or os.environ.get("A3_COORDINATION_ROOT")
    return Path(base or Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser() / "a3-coordinator").expanduser()


def safe_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value):
        raise ValueError("project must be lowercase letters/digits plus '-' or '_'")
    return value


def canonical_url(url: str) -> str:
    return url.strip().rstrip("/").removesuffix(".git").lower()


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def folder(args: argparse.Namespace) -> Path:
    return state_root(args.state_root) / "projects" / safe_slug(args.project)


def cmd_init(args: argparse.Namespace) -> int:
    project = safe_slug(args.project)
    root = folder(args)
    profile_path = root / "profile.json"
    requested = {"repositoryUrl": canonical_url(args.repo), "tracker": args.tracker.strip()}
    if profile_path.exists():
        current = read_json(profile_path)
        existing = {"repositoryUrl": canonical_url(current["repositoryUrl"]), "tracker": current["tracker"]}
        if existing != requested:
            raise ValueError("existing project has a different repository or tracker identity; refusing overwrite")
        print(json.dumps({"initialized": True, "deduped": True, "project": project, "path": str(root)}))
        return 0
    root.mkdir(parents=True, exist_ok=True)
    atomic_json(profile_path, {
        "schemaVersion": 1,
        "slug": project,
        "repositoryUrl": requested["repositoryUrl"],
        "tracker": requested["tracker"],
        "targetBranch": args.target_branch,
        "initializedAt": now(),
    })
    atomic_json(root / "team.json", {
        "schemaVersion": 1,
        "project": project,
        "resolvedAt": None,
        "roles": {"coordinator": None, "support": None, "frontend": None, "backendSecurity": None, "review": None},
    })
    atomic_json(root / "activation.json", {
        "schemaVersion": 1,
        "project": project,
        "initializedAt": now(),
        "enabled": False,
        "cronJobId": None,
    })
    (root / "runtime").mkdir(exist_ok=True)
    print(json.dumps({"initialized": True, "deduped": False, "project": project, "path": str(root)}))
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    root = folder(args)
    path = root / "activation.json"
    activation = read_json(path)
    activation.update({"enabled": True, "cronJobId": args.cron_job_id, "enabledAt": now()})
    atomic_json(path, activation)
    print(json.dumps({"enabled": True, "project": args.project, "cronJobId": args.cron_job_id}))
    return 0


def cmd_disable(args: argparse.Namespace) -> int:
    root = folder(args)
    path = root / "activation.json"
    activation = read_json(path)
    activation.update({"enabled": False, "disabledAt": now(), "previousCronJobId": activation.get("cronJobId"), "cronJobId": None})
    atomic_json(path, activation)
    print(json.dumps({"enabled": False, "project": args.project}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = folder(args)
    result = {"project": args.project, "path": str(root)}
    for name in ("profile.json", "team.json", "activation.json"):
        path = root / name
        result[name.removesuffix(".json")] = read_json(path) if path.exists() else None
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root")
    subs = parser.add_subparsers(dest="command", required=True)
    init = subs.add_parser("init")
    init.add_argument("--project", required=True)
    init.add_argument("--repo", required=True)
    init.add_argument("--tracker", required=True)
    init.add_argument("--target-branch", default="main")
    init.set_defaults(func=cmd_init)
    for command, function in (("enable", cmd_enable), ("disable", cmd_disable), ("status", cmd_status)):
        sub = subs.add_parser(command)
        sub.add_argument("--project", required=True)
        if command == "enable":
            sub.add_argument("--cron-job-id", required=True)
        sub.set_defaults(func=function)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
