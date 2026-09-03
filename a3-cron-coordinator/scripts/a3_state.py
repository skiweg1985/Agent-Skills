#!/usr/bin/env python3
"""Durable per-project A3 Cron coordinator state and issue locks.

No credentials are read or stored. Lock mutation is guarded by a filesystem lock.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path


def utc_now() -> datetime:
    return datetime.now(UTC)


def root_path(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    configured = os.environ.get("A3_COORDINATION_ROOT")
    if configured:
        return Path(configured).expanduser()
    return Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser() / "a3-coordinator"


def project_dir(root: Path, project: str) -> Path:
    if not project.replace("-", "").replace("_", "").isalnum():
        raise ValueError("project must contain only letters, digits, '-' or '_'")
    return root / "projects" / project


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp = Path(handle.name)
    temp.replace(path)


def with_project_lock(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    handle = (folder / ".state.lock").open("a+")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def load_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_init(args: argparse.Namespace) -> int:
    root = root_path(args.state_root)
    folder = project_dir(root, args.project)
    profile = Path(args.profile).expanduser().resolve()
    data = json.loads(profile.read_text(encoding="utf-8"))
    if data.get("slug") != args.project:
        raise ValueError("profile slug must match --project")
    handle = with_project_lock(folder)
    try:
        atomic_json(folder / "state.json", {
            "schemaVersion": 1,
            "project": args.project,
            "profile": str(profile),
            "initializedAt": utc_now().isoformat(),
            "lastSnapshot": None,
        })
        (folder / "locks").mkdir(exist_ok=True)
    finally:
        handle.close()
    print(json.dumps({"initialized": True, "project": args.project, "path": str(folder)}))
    return 0


def cmd_acquire(args: argparse.Namespace) -> int:
    root = root_path(args.state_root)
    folder = project_dir(root, args.project)
    lock_path = folder / "locks" / f"{args.issue}.json"
    now = utc_now()
    handle = with_project_lock(folder)
    try:
        existing = load_json(lock_path, None)
        if existing:
            expires = datetime.fromisoformat(existing["expiresAt"])
            same = existing.get("session") == args.session
            if expires > now and not same:
                print(json.dumps({"acquired": False, "reason": "locked", "lock": existing}))
                return 3
        payload = {
            "project": args.project,
            "issue": args.issue,
            "agent": args.agent,
            "session": args.session,
            "revision": args.revision,
            "acquiredAt": now.isoformat(),
            "expiresAt": (now + timedelta(minutes=args.lease_minutes)).isoformat(),
        }
        atomic_json(lock_path, payload)
    finally:
        handle.close()
    print(json.dumps({"acquired": True, "lock": payload}))
    return 0


def cmd_release(args: argparse.Namespace) -> int:
    root = root_path(args.state_root)
    folder = project_dir(root, args.project)
    lock_path = folder / "locks" / f"{args.issue}.json"
    handle = with_project_lock(folder)
    try:
        existing = load_json(lock_path, None)
        if not existing:
            print(json.dumps({"released": False, "reason": "missing"}))
            return 0
        if existing.get("session") != args.session and not args.force:
            print(json.dumps({"released": False, "reason": "session_mismatch", "lock": existing}))
            return 4
        lock_path.unlink()
    finally:
        handle.close()
    print(json.dumps({"released": True, "issue": args.issue}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    folder = project_dir(root_path(args.state_root), args.project)
    locks = []
    for path in sorted((folder / "locks").glob("*.json")) if (folder / "locks").exists() else []:
        locks.append(load_json(path, {}))
    print(json.dumps({"project": args.project, "state": load_json(folder / "state.json", None), "locks": locks}, ensure_ascii=False))
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    """Store a normalized, non-secret live-state snapshot and report whether it changed."""
    root = root_path(args.state_root)
    folder = project_dir(root, args.project)
    raw = Path(args.input).expanduser().read_text(encoding="utf-8")
    payload = json.loads(raw)
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    handle = with_project_lock(folder)
    try:
        state_path = folder / "state.json"
        state = load_json(state_path, None)
        if not state:
            raise ValueError("project state is not initialized")
        previous = (state.get("lastSnapshot") or {}).get("sha256")
        changed = previous != digest
        state["lastSnapshot"] = {
            "sha256": digest,
            "capturedAt": utc_now().isoformat(),
            "summary": args.summary,
        }
        atomic_json(state_path, state)
    finally:
        handle.close()
    print(json.dumps({"changed": changed, "sha256": digest, "previous": previous}))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--state-root")
    subs = p.add_subparsers(dest="command", required=True)
    init = subs.add_parser("init")
    init.add_argument("--project", required=True)
    init.add_argument("--profile", required=True)
    init.set_defaults(func=cmd_init)
    acquire = subs.add_parser("acquire")
    acquire.add_argument("--project", required=True)
    acquire.add_argument("--issue", required=True)
    acquire.add_argument("--agent", required=True)
    acquire.add_argument("--session", required=True)
    acquire.add_argument("--revision", required=True)
    acquire.add_argument("--lease-minutes", type=int, default=120)
    acquire.set_defaults(func=cmd_acquire)
    release = subs.add_parser("release")
    release.add_argument("--project", required=True)
    release.add_argument("--issue", required=True)
    release.add_argument("--session", required=True)
    release.add_argument("--force", action="store_true")
    release.set_defaults(func=cmd_release)
    status = subs.add_parser("status")
    status.add_argument("--project", required=True)
    status.set_defaults(func=cmd_status)
    snapshot = subs.add_parser("snapshot")
    snapshot.add_argument("--project", required=True)
    snapshot.add_argument("--input", required=True, help="path to a JSON snapshot without secrets")
    snapshot.add_argument("--summary", default="")
    snapshot.set_defaults(func=cmd_snapshot)
    return p


def main() -> int:
    try:
        args = parser().parse_args()
        return args.func(args)
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
