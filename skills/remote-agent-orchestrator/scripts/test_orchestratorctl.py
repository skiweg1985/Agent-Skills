#!/usr/bin/env python3
"""Regression tests for orchestratorctl.

Every test here corresponds to a defect that was reproduced in the previous
design, or to an invariant the orchestrator relies on: one wave per project,
one project per repository-and-tracker, locks releasable by the coordinator that
holds them, and an expired lease that leaves a trace.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("orchestratorctl.py")


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def run_cli(self, *args: str, expected: int = 0, root: Path | None = None) -> dict:
        root = root or self.root
        result = subprocess.run(
            ["python3", str(SCRIPT),
             "--config-root", str(root / "config"),
             "--state-root", str(root / "state"), *args],
            text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout or result.stderr)

    def setup_host(self, root: Path | None = None) -> dict:
        return self.run_cli("setup", root=root)

    def init_project(self, repo: str = "https://github.com/example/demo.git",
                     tracker: str = "Demo", root: Path | None = None) -> str:
        return self.run_cli("project", "init", "--repo", repo, "--tracker", tracker,
                            root=root)["project"]


class Setup(Base):
    def test_creates_identity_profile_registry_and_readiness(self) -> None:
        first = self.setup_host()
        self.assertTrue(first["teamProfileCreated"])
        self.assertTrue(first["registryCreated"])
        self.assertTrue(first["readinessCreated"])
        self.assertTrue(first["coordinatorId"])

    def test_identity_is_stable_across_runs(self) -> None:
        """A later session of the same installation is the same coordinator."""
        first = self.setup_host()
        again = self.setup_host()
        self.assertEqual(first["coordinatorId"], again["coordinatorId"])
        self.assertFalse(again["teamProfileCreated"])

    def test_preserves_role_choices_and_applies_explicit_override(self) -> None:
        self.setup_host()
        self.run_cli("setup", "--role", "frontend=frontend-agent")
        after = self.run_cli("setup")
        self.assertEqual(after["roles"]["frontend"], "frontend-agent")

    def test_rejects_unknown_role(self) -> None:
        self.setup_host()
        error = self.run_cli("setup", "--role", "nope=agent", expected=2)
        self.assertIn("--role", error["error"])

    def test_registers_an_agent_with_an_explicit_invocation(self) -> None:
        self.setup_host()
        self.run_cli("setup", "--agent", "worker-1", "--transport", "ssh",
                     "--host", "build-1.example", "--user", "agent",
                     "--invocation", "codex exec {prompt}", "--workdir", "/srv/work")
        registry = json.loads((self.root / "config" / "agents.json").read_text())
        entry = registry["agents"]["worker-1"]
        self.assertEqual(entry["host"], "build-1.example")
        self.assertEqual(entry["invocation"], "codex exec {prompt}")

    def test_agent_without_invocation_is_rejected(self) -> None:
        """An agent CLI must never be guessed from the agent's name."""
        self.setup_host()
        error = self.run_cli("setup", "--agent", "worker-1", "--host", "h.example",
                             "--user", "a", expected=2)
        self.assertIn("invocation", error["error"])

    def test_registry_refuses_credentials(self) -> None:
        self.setup_host()
        path = self.root / "config" / "agents.json"
        registry = json.loads(path.read_text())
        registry["agents"]["leaky"] = {
            "transport": "ssh", "host": "h.example", "user": "a",
            "invocation": "x", "sshKey": "-----BEGIN PRIVATE KEY-----",
        }
        path.write_text(json.dumps(registry))
        error = self.run_cli("setup", expected=2)
        self.assertIn("credentials", error["error"])

    def test_reports_roles_bound_to_unregistered_agents(self) -> None:
        self.setup_host()
        result = self.run_cli("setup", "--role", "review=ghost")
        self.assertIn("ghost", result["rolesWithoutRegistryEntry"])


class Projects(Base):
    def test_same_repository_and_tracker_dedupes_across_labels(self) -> None:
        """The previous design keyed on a free slug, so two names meant two waves."""
        self.setup_host()
        first = self.run_cli("project", "init", "--repo", "https://github.com/example/demo.git",
                             "--tracker", "Demo", "--label", "one")
        second = self.run_cli("project", "init", "--repo", "git@github.com:example/demo.git",
                              "--tracker", "Demo", "--label", "two")
        self.assertFalse(first["deduped"])
        self.assertTrue(second["deduped"])
        self.assertEqual(first["project"], second["project"])

    def test_different_tracker_is_a_different_project(self) -> None:
        self.setup_host()
        a = self.init_project(tracker="Demo")
        b = self.init_project(tracker="Other")
        self.assertNotEqual(a, b)

    def test_init_does_not_enable_a_wave(self) -> None:
        self.setup_host()
        key = self.init_project()
        wave = self.run_cli("status", "--project", key)["wave"]
        self.assertFalse(wave["enabled"])
        self.assertIsNone(wave["cronJobId"])

    def test_init_requires_a_coordinator_identity(self) -> None:
        error = self.run_cli("project", "init", "--repo", "https://github.com/e/d.git",
                             "--tracker", "T", expected=2)
        self.assertIn("setup", error["error"])


class Locks(Base):
    def setUp(self) -> None:
        super().setUp()
        self.setup_host()
        self.key = self.init_project()

    def acquire(self, issue: str = "ISS-1", agent: str = "worker-1",
                session: str = "s1", lease: str = "120") -> dict:
        return self.run_cli("lock", "acquire", "--project", self.key, "--issue", issue,
                            "--agent", agent, "--session", session,
                            "--revision", "abc123", "--lease-minutes", lease)

    def test_second_acquire_on_a_live_lease_is_refused(self) -> None:
        self.assertTrue(self.acquire()["acquired"])
        second = self.acquire(agent="worker-2", session="s2")
        self.assertFalse(second["acquired"])
        self.assertEqual(second["reason"], "held")

    def test_expired_lease_records_who_was_superseded(self) -> None:
        """An expired lease used to be taken over leaving no trace at all."""
        self.acquire(lease="-1")
        taken = self.acquire(agent="worker-2", session="s2")
        self.assertTrue(taken["acquired"])
        self.assertEqual(taken["lock"]["superseded"]["agent"], "worker-1")
        self.assertEqual(taken["lock"]["superseded"]["session"], "s1")

    def test_coordinator_releases_a_worker_lock_without_force(self) -> None:
        """The coordinator holds locks for its workers, so closing a wave is normal."""
        self.acquire(session="worker-session")
        released = self.run_cli("lock", "release", "--project", self.key, "--issue", "ISS-1")
        self.assertTrue(released["released"])
        self.assertFalse(released["forced"])

    def test_another_installation_cannot_release_without_force(self) -> None:
        self.acquire()
        other = self.root / "other"
        self.setup_host(root=other)
        other_key = self.init_project(root=other)
        # Point the other installation at the same project directory contents.
        target = other / "state" / "projects" / other_key / "locks"
        source = self.root / "state" / "projects" / self.key / "locks" / "ISS-1.json"
        target.mkdir(parents=True, exist_ok=True)
        (target / "ISS-1.json").write_text(source.read_text())

        refused = self.run_cli("lock", "release", "--project", other_key,
                               "--issue", "ISS-1", root=other)
        self.assertFalse(refused["released"])
        self.assertEqual(refused["reason"], "held_by_another_coordinator")

        forced = self.run_cli("lock", "release", "--project", other_key, "--issue", "ISS-1",
                              "--force", "--reason", "stale host", root=other)
        self.assertTrue(forced["forced"])
        record = json.loads((target / "ISS-1.forced.json").read_text())
        self.assertEqual(record["reason"], "stale host")
        self.assertEqual(record["previous"]["agent"], "worker-1")

    def test_renew_extends_the_lease_and_counts(self) -> None:
        first = self.acquire()
        renewed = self.run_cli("lock", "renew", "--project", self.key, "--issue", "ISS-1")
        self.assertGreater(renewed["lock"]["expiresAt"], first["lock"]["expiresAt"])
        self.assertEqual(renewed["lock"]["renewals"], 1)

    def test_listing_flags_expired_leases(self) -> None:
        self.acquire(issue="ISS-1", lease="-1")
        self.acquire(issue="ISS-2")
        listing = self.run_cli("lock", "list", "--project", self.key)
        self.assertEqual(listing["expired"], 1)
        self.assertEqual(len(listing["locks"]), 2)

    def test_corrupt_lock_reports_an_actionable_error(self) -> None:
        """A malformed expiry used to surface a raw Python ValueError."""
        path = self.root / "state" / "projects" / self.key / "locks" / "ISS-9.json"
        path.write_text(json.dumps({"issue": "ISS-9", "agent": "a",
                                    "coordinator": "c", "expiresAt": "not-a-date"}))
        error = self.run_cli("lock", "list", "--project", self.key, expected=2)
        self.assertIn("unreadable expiry", error["error"])
        self.assertIn("ISS-9", error["error"])

    def test_releasing_a_missing_lock_is_not_an_error(self) -> None:
        result = self.run_cli("lock", "release", "--project", self.key, "--issue", "NOPE")
        self.assertFalse(result["released"])
        self.assertEqual(result["reason"], "missing")


class Waves(Base):
    def test_snapshot_works_directly_after_init(self) -> None:
        """The snapshot store used to need a command no documentation mentioned."""
        self.setup_host()
        key = self.init_project()
        payload = self.root / "snap.json"
        payload.write_text(json.dumps({"prs": [], "ci": "green"}))
        first = self.run_cli("snapshot", "--project", key, "--input", str(payload))
        self.assertTrue(first["changed"])
        again = self.run_cli("snapshot", "--project", key, "--input", str(payload))
        self.assertFalse(again["changed"])

    def test_disable_preserves_locks(self) -> None:
        self.setup_host()
        key = self.init_project()
        self.run_cli("lock", "acquire", "--project", key, "--issue", "ISS-1",
                     "--agent", "w", "--session", "s", "--revision", "r")
        self.run_cli("wave", "enable", "--project", key, "--scope", "M1",
                     "--scope-kind", "milestone", "--cron-job-id", "job-1")
        disabled = self.run_cli("wave", "disable", "--project", key)
        self.assertFalse(disabled["enabled"])
        self.assertEqual(len(self.run_cli("lock", "list", "--project", key)["locks"]), 1)

    def test_status_without_project_lists_everything_known(self) -> None:
        """A new session finds existing work without being told a project name."""
        self.setup_host()
        self.run_cli("setup", "--agent", "worker-1", "--host", "h.example",
                     "--user", "a", "--invocation", "claude -p {prompt}")
        key = self.init_project()
        self.run_cli("wave", "enable", "--project", key, "--scope", "M1",
                     "--scope-kind", "milestone", "--cron-job-id", "job-1")
        overview = self.run_cli("status")
        self.assertEqual(len(overview["projects"]), 1)
        self.assertTrue(overview["projects"][0]["waveEnabled"])
        self.assertIn("worker-1", overview["agents"])
        self.assertTrue(overview["coordinatorId"])

    def test_unknown_project_is_rejected(self) -> None:
        self.setup_host()
        error = self.run_cli("status", "--project", "does-not-exist", expected=2)
        self.assertIn("not initialized", error["error"])


if __name__ == "__main__":
    unittest.main()
