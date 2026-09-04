#!/usr/bin/env python3
"""Local state for the remote-agent orchestrator.

One tool, one state root. The previous split between a configuration helper and a
lock helper is where most of this skill's defects lived: two notions of the state
root, a documented lock path that nested itself, and a snapshot store no
documented command ever initialized.

This tool never creates cron jobs, connects to a worker, or starts an agent. It
records local, secrets-free configuration and state; the coordinator performs
every remote action.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

ROLE_NAMES = ("coordinator", "support", "frontend", "backendSecurity", "review")
TRANSPORTS = ("ssh", "local")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
ISSUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,253}$")


class Problem(Exception):
    """An error the coordinator can act on, reported as JSON rather than a traceback."""


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp() -> str:
    return now().isoformat()


def config_root(override: str | None) -> Path:
    base = override or os.environ.get("ORCHESTRATOR_CONFIG_ROOT")
    if base:
        return Path(base).expanduser()
    return Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "agent-orchestrator"


def state_root(override: str | None) -> Path:
    base = override or os.environ.get("ORCHESTRATOR_STATE_ROOT")
    if base:
        return Path(base).expanduser()
    return Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser() / "agent-orchestrator"


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
        temp = Path(handle.name)
    temp.replace(path)


def read_json(path: Path, default=None, what: str = "file"):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Problem(f"{what} at {path} is not valid JSON ({exc.msg} at line {exc.lineno}); "
                      "inspect or remove it") from exc


def canonical_repo(url: str) -> str:
    value = url.strip().removesuffix(".git").rstrip("/")
    value = re.sub(r"^git@([^:]+):", r"https://\1/", value)
    value = re.sub(r"^ssh://git@", "https://", value)
    return value.lower()


def project_key(repo: str, tracker: str) -> str:
    """Derive the directory from identity, so a duplicate cannot be created.

    A freely chosen slug let the same repository and tracker be initialized twice
    under different names, each believing it was alone.
    """
    canonical = canonical_repo(repo)
    digest = hashlib.sha256(f"{canonical}\0{tracker.strip()}".encode()).hexdigest()[:8]
    name = re.sub(r"[^a-z0-9]+", "-", canonical.rsplit("/", 1)[-1]).strip("-") or "project"
    return f"{name}-{digest}"


# --- coordinator identity -------------------------------------------------

def coordinator_id(config: Path, create: bool = False) -> str:
    """Identity belongs to the installation, not to a session.

    A later session of the same installation is the same coordinator and simply
    continues, which is what makes a wave findable in a new session.
    """
    path = config / "coordinator.json"
    record = read_json(path, what="coordinator identity")
    if record:
        value = record.get("coordinatorId", "")
        if not ID_RE.fullmatch(value):
            raise Problem(f"coordinator identity at {path} is malformed")
        return value
    if not create:
        raise Problem("this installation has no coordinator identity yet; run setup first")
    value = uuid.uuid4().hex[:16]
    atomic_json(path, {"schemaVersion": 1, "coordinatorId": value, "createdAt": stamp()})
    return value


# --- registry and roles ---------------------------------------------------

def blank_roles() -> dict[str, str | None]:
    return {role: None for role in ROLE_NAMES}


def load_roles(config: Path) -> dict[str, str | None]:
    profile = read_json(config / "team-profile.json", what="team profile")
    roles = blank_roles()
    if not profile:
        return roles
    stored = profile.get("roles", {})
    if not isinstance(stored, dict):
        raise Problem("team profile roles must be an object")
    for role in ROLE_NAMES:
        value = stored.get(role)
        if value is not None and not isinstance(value, str):
            raise Problem(f"team profile role {role!r} must be a string or null")
        roles[role] = value
    return roles


def load_agents(config: Path) -> dict[str, dict]:
    registry = read_json(config / "agents.json", what="agent registry")
    if not registry:
        return {}
    agents = registry.get("agents", {})
    if not isinstance(agents, dict):
        raise Problem("agent registry 'agents' must be an object")
    return agents


def check_agent(agent_id: str, entry: dict) -> None:
    if not ID_RE.fullmatch(agent_id):
        raise Problem(f"invalid agent id {agent_id!r}")
    transport = entry.get("transport")
    if transport not in TRANSPORTS:
        raise Problem(f"agent {agent_id!r}: transport must be one of {', '.join(TRANSPORTS)}")
    if transport == "ssh":
        for field in ("host", "user"):
            if not entry.get(field):
                raise Problem(f"agent {agent_id!r}: ssh transport requires '{field}'")
        if not HOST_RE.fullmatch(str(entry["host"])):
            raise Problem(f"agent {agent_id!r}: invalid host")
    if not entry.get("invocation"):
        raise Problem(f"agent {agent_id!r}: an explicit invocation template is required; "
                      "agent CLIs differ and must never be guessed from a name")
    # The registry says where an agent lives, never how to authenticate as one.
    leaked = sorted(k for k in entry if re.search(r"key|token|secret|password|passphrase", k, re.I))
    if leaked:
        raise Problem(f"agent {agent_id!r}: registry must not hold credentials "
                      f"(found {', '.join(leaked)}); public-key auth is set up on the host")


def parse_bindings(values: list[str]) -> dict[str, str]:
    bindings: dict[str, str] = {}
    for value in values:
        role, separator, agent = value.partition("=")
        if not separator or role not in ROLE_NAMES:
            raise Problem("--role must be ROLE=AGENT; ROLE is one of " + ", ".join(ROLE_NAMES))
        if not ID_RE.fullmatch(agent):
            raise Problem("agent identifier must be a non-secret local identifier")
        bindings[role] = agent
    return bindings


# What reaches the delivery channel. A subscription, not a volume dial: each level
# includes the ones above it, so the question is always "is this urgent enough to
# reach a person right now", never "how chatty should I be".
NOTICE_LEVELS = ("blocker", "milestone", "progress")
DEFAULT_LEVEL = "milestone"
QUIET_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)-([01]\d|2[0-3]):([0-5]\d)$")


def notify_path(config: Path) -> Path:
    return config / "notify.json"


def load_notify(config: Path) -> dict:
    return read_json(notify_path(config), default={}, what="notification policy") or {}


def in_quiet_hours(window: str | None, when: datetime | None = None) -> bool:
    if not window:
        return False
    match = QUIET_RE.match(window)
    if not match:
        raise Problem(f"quiet hours must look like 22:00-07:00, got {window!r}")
    start_h, start_m, end_h, end_m = (int(g) for g in match.groups())
    now = (when or datetime.now()).time()
    start, end = time(start_h, start_m), time(end_h, end_m)
    if start <= end:
        return start <= now < end
    return now >= start or now < end  # window crosses midnight


def effective_policy(config: Path, state: Path, project: str | None) -> dict:
    """Wave beats project beats host default. Report where each value came from."""
    host = load_notify(config)
    level, source = host.get("level", DEFAULT_LEVEL), "host" if host.get("level") else "default"
    if project:
        folder = project_dir(state, project)
        profile = read_json(folder / "profile.json", default={}, what="project profile") or {}
        if profile.get("notifyLevel"):
            level, source = profile["notifyLevel"], "project"
        wave = read_json(folder / "wave.json", default={}, what="wave state") or {}
        if wave.get("notifyLevel"):
            level, source = wave["notifyLevel"], "wave"
    if level not in NOTICE_LEVELS:
        raise Problem(f"unknown notification level {level!r}; use one of {', '.join(NOTICE_LEVELS)}")
    quiet = host.get("quietHours")
    return {
        "level": level,
        "levelFrom": source,
        "quietHours": quiet,
        "inQuietHours": in_quiet_hours(quiet),
    }


# --- projects -------------------------------------------------------------

def project_dir(state: Path, key: str) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,127}", key):
        raise Problem(f"invalid project key {key!r}")
    return state / "projects" / key


def require_project(state: Path, key: str) -> Path:
    folder = project_dir(state, key)
    if not (folder / "profile.json").exists():
        raise Problem(f"project {key!r} is not initialized")
    return folder


class WaveLock:
    """One active wave per project, enforced by the operating system.

    A dead session's lock is released by the kernel, so a new session continues
    without a takeover ritual.
    """

    def __init__(self, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        self.handle = (folder / "wave.lock").open("a+")

    def __enter__(self):
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.close()
            raise Problem("another wave is active for this project on this host") from exc
        return self

    def __exit__(self, *_):
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()


# --- commands -------------------------------------------------------------

def cmd_setup(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    identity = coordinator_id(config, create=True)

    profile_path = config / "team-profile.json"
    created_profile = not profile_path.exists()
    profile = read_json(profile_path, default={
        "schemaVersion": 1,
        "configuredAt": stamp(),
        "roles": blank_roles(),
        "notes": "Local role bindings only. Reachability belongs in agents.json, "
                 "credentials in neither.",
    }, what="team profile")
    if not isinstance(profile.get("roles"), dict):
        raise Problem("existing team profile roles must be an object")
    changed = created_profile
    for role in ROLE_NAMES:
        if role not in profile["roles"]:
            profile["roles"][role] = None
            changed = True
    bindings = parse_bindings(args.role)
    if bindings:
        profile["roles"].update(bindings)
        profile["updatedAt"] = stamp()
        changed = True
    if changed:
        atomic_json(profile_path, profile)

    registry_path = config / "agents.json"
    created_registry = not registry_path.exists()
    registry = read_json(registry_path, default={
        "schemaVersion": 1,
        "agents": {},
        "notes": "Where an agent lives and how to invoke it. Never credentials: "
                 "public-key authentication is provisioned on the host itself.",
    }, what="agent registry")
    if args.agent:
        entry = {
            "transport": args.transport,
            "invocation": args.invocation,
            "workdir": args.workdir,
        }
        if args.transport == "ssh":
            entry["host"] = args.host
            entry["user"] = args.user
            if args.port:
                entry["port"] = args.port
        if args.branch_prefix:
            entry["branchPrefix"] = args.branch_prefix
        entry = {k: v for k, v in entry.items() if v is not None}
        check_agent(args.agent, entry)
        registry.setdefault("agents", {})[args.agent] = entry
        registry["updatedAt"] = stamp()
        atomic_json(registry_path, registry)
    else:
        for agent_id, entry in registry.get("agents", {}).items():
            check_agent(agent_id, entry)
        if created_registry:
            atomic_json(registry_path, registry)

    readiness_path = state / "worker-readiness.json"
    created_readiness = not readiness_path.exists()
    if created_readiness:
        atomic_json(readiness_path, {
            "schemaVersion": 1,
            "observedAt": None,
            "workers": {},
            "notes": "Secrets-free readiness evidence. A wave still requires a fresh "
                     "preflight on the actual worker host.",
        })

    roles = load_roles(config)
    agents = load_agents(config)
    unbound = sorted({a for a in roles.values() if a} - set(agents))
    return {
        "coordinatorId": identity,
        "teamProfileCreated": created_profile,
        "registryCreated": created_registry,
        "readinessCreated": created_readiness,
        "teamProfilePath": str(profile_path),
        "registryPath": str(registry_path),
        "roles": roles,
        "agents": sorted(agents),
        "rolesWithoutRegistryEntry": unbound,
        "nextAction": (
            "Add a registry entry for every bound role, then run a fresh remote preflight. "
            "Ask the user only for missing access, approval, or a role decision."
            if unbound else
            "Run a fresh remote preflight on each worker host before initializing a project."
        ),
    }


def cmd_project_init(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    identity = coordinator_id(config)
    key = project_key(args.repo, args.tracker)
    folder = project_dir(state, key)
    profile_path = folder / "profile.json"

    requested = {"repositoryUrl": canonical_repo(args.repo), "tracker": args.tracker.strip()}
    existing = read_json(profile_path, what="project profile")
    if existing:
        current = {"repositoryUrl": existing["repositoryUrl"], "tracker": existing["tracker"]}
        if current != requested:
            raise Problem(f"project key {key} already holds a different identity; refusing overwrite")
        return {"project": key, "deduped": True, "path": str(folder)}

    roles = load_roles(config)
    atomic_json(profile_path, {
        "schemaVersion": 1,
        "project": key,
        "label": args.label or requested["repositoryUrl"].rsplit("/", 1)[-1],
        "repositoryUrl": requested["repositoryUrl"],
        "tracker": requested["tracker"],
        "targetBranch": args.target_branch,
        "maxWorkers": args.max_workers,
        "coordinatorId": identity,
        "initializedAt": stamp(),
    })
    atomic_json(folder / "team.json", {
        "schemaVersion": 1,
        "project": key,
        "resolvedAt": stamp() if any(roles.values()) else None,
        "roles": roles,
    })
    atomic_json(folder / "wave.json", {
        "schemaVersion": 1,
        "project": key,
        "enabled": False,
        "scope": None,
        "cronJobId": None,
        "initializedAt": stamp(),
    })
    (folder / "locks").mkdir(exist_ok=True)
    return {"project": key, "deduped": False, "path": str(folder)}


def cmd_project_list(args: argparse.Namespace) -> dict:
    state = state_root(args.state_root)
    projects = []
    root = state / "projects"
    for folder in sorted(root.glob("*/profile.json")) if root.exists() else []:
        profile = read_json(folder, what="project profile") or {}
        wave = read_json(folder.parent / "wave.json", default={}, what="wave state")
        locks = list((folder.parent / "locks").glob("*.json"))
        projects.append({
            "project": profile.get("project"),
            "label": profile.get("label"),
            "repositoryUrl": profile.get("repositoryUrl"),
            "tracker": profile.get("tracker"),
            "waveEnabled": wave.get("enabled", False),
            "scope": wave.get("scope"),
            "openLocks": len(locks),
        })
    return {"projects": projects}


def cmd_wave_enable(args: argparse.Namespace) -> dict:
    state = state_root(args.state_root)
    folder = require_project(state, args.project)
    with WaveLock(folder):
        wave = read_json(folder / "wave.json", default={}, what="wave state")
        wave.update({
            "schemaVersion": 1,
            "project": args.project,
            "enabled": True,
            "scope": {"kind": args.scope_kind, "value": args.scope},
            "cronJobId": args.cron_job_id,
            "enabledAt": stamp(),
        })
        atomic_json(folder / "wave.json", wave)
    return {"project": args.project, "enabled": True, "scope": wave["scope"],
            "cronJobId": args.cron_job_id}


def cmd_wave_disable(args: argparse.Namespace) -> dict:
    state = state_root(args.state_root)
    folder = require_project(state, args.project)
    wave = read_json(folder / "wave.json", default={}, what="wave state")
    # Keep the scheduler job id. The scheduler entry outlives this record, and
    # forgetting the id leaves a supervisor that still runs and that nobody can
    # name any more.
    job = wave.get("cronJobId")
    wave.update({"enabled": False, "disabledAt": stamp()})
    atomic_json(folder / "wave.json", wave)

    held = [lock for lock in cmd_lock_list(args)["locks"] if not lock["expired"]]
    result = {
        "project": args.project,
        "enabled": False,
        "cronJobId": job,
        "heldLocks": [lock["issue"] for lock in held],
        "note": "future scheduling stopped; workers, worktrees and locks are preserved",
    }
    if job:
        result["nextAction"] = (
            f"remove scheduler job {job} yourself; disabling the wave does not stop it"
        )
    if held:
        # Disabling a wave that still holds locks is legitimate, but from now on
        # nothing renews their leases and nothing notices when the work finishes.
        result["warning"] = (
            f"{len(held)} lock(s) still held with no supervisor to renew or release them: "
            + ", ".join(lock["issue"] for lock in held)
        )
    return result


def read_lock(path: Path) -> dict | None:
    record = read_json(path, what="lock")
    if record is None:
        return None
    for field in ("issue", "agent", "coordinator", "expiresAt"):
        if field not in record:
            raise Problem(f"lock at {path} is missing '{field}'; inspect or remove it")
    try:
        datetime.fromisoformat(record["expiresAt"])
    except (TypeError, ValueError) as exc:
        raise Problem(f"lock at {path} has an unreadable expiry {record['expiresAt']!r}; "
                      "inspect or remove it") from exc
    return record


def cmd_lock_acquire(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    identity = coordinator_id(config)
    folder = require_project(state, args.project)
    if not ISSUE_RE.fullmatch(args.issue):
        raise Problem(f"invalid issue key {args.issue!r}")
    path = folder / "locks" / f"{args.issue}.json"

    with WaveLock(folder):
        existing = read_lock(path)
        superseded = None
        if existing:
            expires = datetime.fromisoformat(existing["expiresAt"])
            if expires > now():
                return {"acquired": False, "reason": "held", "lock": existing}
            # An expired lease is a liveness signal, not permission to forget the
            # previous holder: record whom this run superseded.
            superseded = {
                "agent": existing["agent"],
                "session": existing.get("session"),
                "expiredAt": existing["expiresAt"],
                "supersededAt": stamp(),
            }
        payload = {
            "project": args.project,
            "issue": args.issue,
            "agent": args.agent,
            "coordinator": identity,
            "session": args.session,
            "revision": args.revision,
            "acquiredAt": stamp(),
            "expiresAt": (now() + timedelta(minutes=args.lease_minutes)).isoformat(),
            "renewals": 0,
        }
        if superseded:
            payload["superseded"] = superseded
        atomic_json(path, payload)
    return {"acquired": True, "lock": payload}


def cmd_lock_renew(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    identity = coordinator_id(config)
    folder = require_project(state, args.project)
    path = folder / "locks" / f"{args.issue}.json"
    with WaveLock(folder):
        existing = read_lock(path)
        if not existing:
            raise Problem(f"no lock for issue {args.issue}")
        if existing["coordinator"] != identity:
            raise Problem("this installation does not hold that lock")
        existing["expiresAt"] = (now() + timedelta(minutes=args.lease_minutes)).isoformat()
        existing["renewedAt"] = stamp()
        existing["renewals"] = int(existing.get("renewals", 0)) + 1
        atomic_json(path, existing)
    return {"renewed": True, "lock": existing}


def cmd_lock_release(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    identity = coordinator_id(config)
    folder = require_project(state, args.project)
    path = folder / "locks" / f"{args.issue}.json"
    with WaveLock(folder):
        existing = read_lock(path)
        if not existing:
            return {"released": False, "reason": "missing"}
        # Release is authorized by coordinator identity, not by session equality:
        # the coordinator holds locks on behalf of workers and must be able to
        # close its own wave without disabling the check.
        if existing["coordinator"] != identity and not args.force:
            return {"released": False, "reason": "held_by_another_coordinator", "lock": existing}
        if existing["coordinator"] != identity:
            atomic_json(folder / "locks" / f"{args.issue}.forced.json", {
                "issue": args.issue,
                "forcedBy": identity,
                "reason": args.reason,
                "at": stamp(),
                "previous": existing,
            })
        path.unlink()
    return {"released": True, "issue": args.issue, "forced": existing["coordinator"] != identity}


def cmd_lock_list(args: argparse.Namespace) -> dict:
    state = state_root(args.state_root)
    folder = require_project(state, args.project)
    locks, expired = [], 0
    for path in sorted((folder / "locks").glob("*.json")):
        if path.name.endswith(".forced.json"):
            continue
        record = read_lock(path)
        if record:
            record["expired"] = datetime.fromisoformat(record["expiresAt"]) <= now()
            expired += record["expired"]
            locks.append(record)
    return {"project": args.project, "locks": locks, "expired": expired}


def cmd_snapshot(args: argparse.Namespace) -> dict:
    """Store a normalized, secrets-free snapshot and report whether it changed.

    Reachable directly after project init: the previous design required a command
    no documentation mentioned, so this never worked through the documented flow.
    """
    state = state_root(args.state_root)
    folder = require_project(state, args.project)
    payload = read_json(Path(args.input).expanduser(), what="snapshot input")
    if payload is None:
        raise Problem(f"snapshot input {args.input} does not exist")
    canonical = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    path = folder / "snapshot.json"
    previous = (read_json(path, default={}, what="snapshot") or {}).get("sha256")
    atomic_json(path, {
        "schemaVersion": 1,
        "sha256": digest,
        "capturedAt": stamp(),
        "summary": args.summary,
    })
    return {"changed": previous != digest, "sha256": digest, "previous": previous}


def cmd_status(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    if not args.project:
        overview = cmd_project_list(args)
        overview["coordinatorId"] = read_json(
            config / "coordinator.json", default={}, what="coordinator identity").get("coordinatorId")
        overview["agents"] = sorted(load_agents(config))
        overview["roles"] = load_roles(config)
        overview["workerReadiness"] = read_json(
            state / "worker-readiness.json", what="worker readiness")
        return overview
    folder = require_project(state, args.project)
    wave = read_json(folder / "wave.json", what="wave state") or {}
    snapshot = read_json(folder / "snapshot.json", what="snapshot")
    result = {
        "project": args.project,
        "profile": read_json(folder / "profile.json", what="project profile"),
        "team": read_json(folder / "team.json", what="team bindings"),
        "wave": wave,
        "snapshot": snapshot,
        "locks": cmd_lock_list(args)["locks"],
    }
    # Reporting only material changes means comparing against a stored state. An
    # active wave without one cannot do that and will restate everything it sees,
    # so say so rather than letting the omission stay quiet.
    if wave.get("enabled") and snapshot is None:
        result["warning"] = (
            "no snapshot stored for this wave: nothing to compare against, so every "
            "report will restate the full state instead of the delta"
        )
    return result


def cmd_notify_show(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    policy = effective_policy(config, state, args.project)
    policy["project"] = args.project
    policy["held"] = len(read_json(state / "pending-notices.json", default=[], what="held notices") or [])
    return policy


def cmd_notify_set(args: argparse.Namespace) -> dict:
    config, state = config_root(args.config_root), state_root(args.state_root)
    if args.level and args.level not in NOTICE_LEVELS:
        raise Problem(f"level must be one of {', '.join(NOTICE_LEVELS)}")
    if args.project:
        if args.quiet_hours is not None:
            raise Problem("quiet hours are a host setting; omit --project")
        folder = require_project(state, args.project)
        target = "wave" if args.wave else "project"
        path = folder / ("wave.json" if args.wave else "profile.json")
        record = read_json(path, default={}, what=f"{target} state") or {}
        if args.level:
            record["notifyLevel"] = args.level
        elif args.clear:
            record.pop("notifyLevel", None)
        atomic_json(path, record)
    else:
        record = load_notify(config)
        if args.level:
            record["level"] = args.level
        if args.quiet_hours is not None:
            if args.quiet_hours.lower() in ("none", "off", ""):
                record.pop("quietHours", None)
            else:
                in_quiet_hours(args.quiet_hours)  # validates the format
                record["quietHours"] = args.quiet_hours
        if args.clear and not args.level:
            record.pop("level", None)
        record["schemaVersion"] = 1
        record["updatedAt"] = stamp()
        atomic_json(notify_path(config), record)
    return effective_policy(config, state, args.project)


def cmd_notify_decide(args: argparse.Namespace) -> dict:
    """Answer whether this notice reaches the channel now, so nobody has to judge."""
    config, state = config_root(args.config_root), state_root(args.state_root)
    policy = effective_policy(config, state, args.project)
    if args.notice_class not in NOTICE_LEVELS:
        raise Problem(f"class must be one of {', '.join(NOTICE_LEVELS)}")
    subscribed = NOTICE_LEVELS.index(args.notice_class) <= NOTICE_LEVELS.index(policy["level"])
    if not subscribed:
        return {**policy, "class": args.notice_class, "deliver": False, "hold": False,
                "reason": f"level {policy['level']} does not include {args.notice_class}"}
    if policy["inQuietHours"] and args.notice_class != "blocker":
        return {**policy, "class": args.notice_class, "deliver": False, "hold": True,
                "reason": "inside quiet hours; hold it and deliver the summary afterwards"}
    return {**policy, "class": args.notice_class, "deliver": True, "hold": False,
            "reason": "subscribed and outside quiet hours"}


def cmd_notify_hold(args: argparse.Namespace) -> dict:
    """Park a notice suppressed by quiet hours. Held, never dropped."""
    state = state_root(args.state_root)
    path = state / "pending-notices.json"
    held = read_json(path, default=[], what="held notices") or []
    held.append({"at": stamp(), "class": args.notice_class,
                 "project": args.project, "text": args.text})
    atomic_json(path, held)
    return {"held": len(held)}


def cmd_notify_flush(args: argparse.Namespace) -> dict:
    """Return everything held and clear the store, for one summary message."""
    state = state_root(args.state_root)
    path = state / "pending-notices.json"
    held = read_json(path, default=[], what="held notices") or []
    if held:
        atomic_json(path, [])
    return {"flushed": len(held), "notices": held}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="orchestratorctl")
    parser.add_argument("--config-root")
    parser.add_argument("--state-root")
    subs = parser.add_subparsers(dest="command", required=True)

    setup = subs.add_parser("setup", help="create or review local configuration")
    setup.add_argument("--role", action="append", default=[], metavar="ROLE=AGENT")
    setup.add_argument("--agent", metavar="ID")
    setup.add_argument("--transport", choices=TRANSPORTS, default="ssh")
    setup.add_argument("--host")
    setup.add_argument("--user")
    setup.add_argument("--port", type=int)
    setup.add_argument("--workdir")
    setup.add_argument("--branch-prefix")
    setup.add_argument("--invocation", help="explicit command template for this agent")
    setup.set_defaults(func=cmd_setup)

    project = subs.add_parser("project").add_subparsers(dest="project_command", required=True)
    init = project.add_parser("init")
    init.add_argument("--repo", required=True)
    init.add_argument("--tracker", required=True)
    init.add_argument("--label")
    init.add_argument("--target-branch", default="main")
    init.add_argument("--max-workers", type=int, default=5)
    init.set_defaults(func=cmd_project_init)
    listing = project.add_parser("list")
    listing.set_defaults(func=cmd_project_list)

    wave = subs.add_parser("wave").add_subparsers(dest="wave_command", required=True)
    enable = wave.add_parser("enable")
    enable.add_argument("--project", required=True)
    enable.add_argument("--scope", required=True)
    enable.add_argument("--scope-kind", choices=("milestone", "issues"), required=True)
    enable.add_argument("--cron-job-id", required=True)
    enable.set_defaults(func=cmd_wave_enable)
    disable = wave.add_parser("disable")
    disable.add_argument("--project", required=True)
    disable.set_defaults(func=cmd_wave_disable)

    lock = subs.add_parser("lock").add_subparsers(dest="lock_command", required=True)
    acquire = lock.add_parser("acquire")
    for flag in ("--project", "--issue", "--agent", "--session", "--revision"):
        acquire.add_argument(flag, required=True)
    acquire.add_argument("--lease-minutes", type=int, default=120)
    acquire.set_defaults(func=cmd_lock_acquire)
    renew = lock.add_parser("renew")
    renew.add_argument("--project", required=True)
    renew.add_argument("--issue", required=True)
    renew.add_argument("--lease-minutes", type=int, default=120)
    renew.set_defaults(func=cmd_lock_renew)
    release = lock.add_parser("release")
    release.add_argument("--project", required=True)
    release.add_argument("--issue", required=True)
    release.add_argument("--force", action="store_true")
    release.add_argument("--reason", default="")
    release.set_defaults(func=cmd_lock_release)
    locks = lock.add_parser("list")
    locks.add_argument("--project", required=True)
    locks.set_defaults(func=cmd_lock_list)

    snapshot = subs.add_parser("snapshot")
    snapshot.add_argument("--project", required=True)
    snapshot.add_argument("--input", required=True)
    snapshot.add_argument("--summary", default="")
    snapshot.set_defaults(func=cmd_snapshot)

    notify = subs.add_parser("notify").add_subparsers(dest="notify_command", required=True)
    show = notify.add_parser("show")
    show.add_argument("--project")
    show.set_defaults(func=cmd_notify_show)
    setter = notify.add_parser("set")
    setter.add_argument("--project")
    setter.add_argument("--wave", action="store_true", help="apply to the active wave only")
    setter.add_argument("--level", choices=NOTICE_LEVELS)
    setter.add_argument("--quiet-hours", metavar="HH:MM-HH:MM")
    setter.add_argument("--clear", action="store_true")
    setter.set_defaults(func=cmd_notify_set)
    decide = notify.add_parser("decide")
    decide.add_argument("--class", dest="notice_class", required=True, choices=NOTICE_LEVELS)
    decide.add_argument("--project")
    decide.set_defaults(func=cmd_notify_decide)
    hold = notify.add_parser("hold")
    hold.add_argument("--class", dest="notice_class", required=True, choices=NOTICE_LEVELS)
    hold.add_argument("--project")
    hold.add_argument("--text", required=True)
    hold.set_defaults(func=cmd_notify_hold)
    flush = notify.add_parser("flush")
    flush.set_defaults(func=cmd_notify_flush)

    status = subs.add_parser("status")
    status.add_argument("--project")
    status.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        print(json.dumps(args.func(args), ensure_ascii=False))
    except Problem as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    except OSError as exc:
        print(json.dumps({"error": f"{exc.strerror or exc}: {exc.filename}"}), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
