#!/usr/bin/env python3
"""Local, opt-in configuration and state for the public A3 coordinator skill.

This helper never creates Cron jobs, connects to workers, or starts agents. It
only creates and records local, secrets-free configuration/state. A coordinator
performs any remote readiness checks and external actions.
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

ROLE_NAMES = ("coordinator", "support", "frontend", "backendSecurity", "review")


def now() -> str:
    return datetime.now(UTC).isoformat()


def state_root(value: str | None) -> Path:
    base = value or os.environ.get("A3_COORDINATION_ROOT")
    return Path(
        base
        or Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
        / "a3-coordinator"
    ).expanduser()


def config_root(value: str | None) -> Path:
    base = value or os.environ.get("A3_CONFIG_ROOT")
    return Path(
        base
        or Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
        / "a3-coordinator"
    ).expanduser()


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


def blank_roles() -> dict[str, str | None]:
    return {role: None for role in ROLE_NAMES}


def team_profile_path(args: argparse.Namespace) -> Path:
    return config_root(args.config_root) / "team-profile.json"


def readiness_path(args: argparse.Namespace) -> Path:
    return state_root(args.state_root) / "worker-readiness.json"


def default_team_profile() -> dict:
    return {
        "schemaVersion": 1,
        "configuredAt": now(),
        "roles": blank_roles(),
        "notes": (
            "Local desired role bindings only. Keep hosts, credentials, tokens, "
            "and machine-specific connection details in private policy, not here."
        ),
    }


def default_readiness() -> dict:
    return {
        "schemaVersion": 1,
        "observedAt": None,
        "workers": {},
        "notes": (
            "A coordinator records only secrets-free remote readiness evidence here. "
            "A3 START requires a fresh independent remote preflight."
        ),
    }


def parse_role_bindings(values: list[str]) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for value in values:
        role, separator, agent = value.partition("=")
        if not separator or role not in ROLE_NAMES:
            raise ValueError(
                "--role must be ROLE=AGENT; ROLE is one of " + ", ".join(ROLE_NAMES)
            )
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", agent):
            raise ValueError("agent identifier must be a non-secret local identifier")
        bindings[role] = agent
    return bindings


def local_roles(args: argparse.Namespace) -> dict[str, str | None]:
    path = team_profile_path(args)
    if not path.exists():
        return blank_roles()
    profile = read_json(path)
    stored = profile.get("roles", {})
    if not isinstance(stored, dict):
        raise ValueError("team profile roles must be an object")
    roles = blank_roles()
    for role in ROLE_NAMES:
        value = stored.get(role)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"team profile role '{role}' must be a string or null")
        roles[role] = value
    return roles


def folder(args: argparse.Namespace) -> Path:
    return state_root(args.state_root) / "projects" / safe_slug(args.project)


def cmd_setup(args: argparse.Namespace) -> int:
    profile_path = team_profile_path(args)
    readiness = readiness_path(args)
    created_profile = not profile_path.exists()
    profile = default_team_profile() if created_profile else read_json(profile_path)
    profile_changed = created_profile
    if not isinstance(profile.get("roles"), dict):
        raise ValueError("existing team profile roles must be an object")
    for role in ROLE_NAMES:
        if role not in profile["roles"]:
            profile["roles"][role] = None
            profile_changed = True
    bindings = parse_role_bindings(args.role)
    if bindings:
        profile["roles"].update(bindings)
        profile["updatedAt"] = now()
        profile_changed = True
    if profile_changed:
        atomic_json(profile_path, profile)
    created_readiness = not readiness.exists()
    if created_readiness:
        atomic_json(readiness, default_readiness())
    print(json.dumps({
        "configured": True,
        "teamProfileCreated": created_profile,
        "readinessCreated": created_readiness,
        "teamProfilePath": str(profile_path),
        "readinessPath": str(readiness),
        "roles": local_roles(args),
        "nextAction": (
            "Run a fresh, independent remote worker preflight before A3 INIT or A3 START; "
            "ask the user only for missing access, approval, or a role decision."
        ),
    }, ensure_ascii=False))
    return 0


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
    roles = local_roles(args)
    atomic_json(root / "team.json", {
        "schemaVersion": 1,
        "project": project,
        "resolvedAt": now() if any(roles.values()) else None,
        "roles": roles,
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
    readiness = readiness_path(args)
    result["workerReadiness"] = read_json(readiness) if readiness.exists() else None
    print(json.dumps(result, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root")
    parser.add_argument("--config-root")
    subs = parser.add_subparsers(dest="command", required=True)
    setup = subs.add_parser("setup")
    setup.add_argument("--role", action="append", default=[], metavar="ROLE=AGENT")
    setup.set_defaults(func=cmd_setup)
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
