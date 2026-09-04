#!/usr/bin/env python3
"""Focused regression tests for a3ctl's local setup behavior."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("a3ctl.py")


class A3SetupTests(unittest.TestCase):
    def run_cli(self, root: Path, *args: str, expected: int = 0) -> dict:
        result = subprocess.run(
            [
                "python3",
                str(SCRIPT),
                "--config-root",
                str(root / "config"),
                "--state-root",
                str(root / "state"),
                *args,
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return json.loads(result.stdout) if result.stdout else json.loads(result.stderr)

    def test_setup_is_idempotent_and_preserves_explicit_roles(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            initial = self.run_cli(root, "setup")
            self.assertTrue(initial["teamProfileCreated"])
            self.assertTrue(initial["readinessCreated"])
            configured = self.run_cli(root, "setup", "--role", "backendSecurity=backend-agent")
            self.assertEqual(configured["roles"]["backendSecurity"], "backend-agent")
            repeated = self.run_cli(root, "setup")
            self.assertFalse(repeated["teamProfileCreated"])
            self.assertFalse(repeated["readinessCreated"])
            self.assertEqual(repeated["roles"]["backendSecurity"], "backend-agent")

    def test_init_uses_local_role_bindings_without_activation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            self.run_cli(root, "setup", "--role", "frontend=frontend-agent")
            self.run_cli(
                root,
                "init",
                "--project",
                "example-project",
                "--repo",
                "https://github.com/example/example-project.git",
                "--tracker",
                "tracker-id",
            )
            team = json.loads((root / "state" / "projects" / "example-project" / "team.json").read_text())
            activation = json.loads((root / "state" / "projects" / "example-project" / "activation.json").read_text())
            self.assertEqual(team["roles"]["frontend"], "frontend-agent")
            self.assertFalse(activation["enabled"])
            self.assertIsNone(activation["cronJobId"])

    def test_setup_backfills_older_profile_without_overwriting_choice(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            profile = root / "config" / "team-profile.json"
            profile.parent.mkdir(parents=True)
            profile.write_text(json.dumps({"schemaVersion": 1, "roles": {"frontend": "frontend-agent"}}))
            result = self.run_cli(root, "setup")
            self.assertFalse(result["teamProfileCreated"])
            stored = json.loads(profile.read_text())
            self.assertEqual(stored["roles"]["frontend"], "frontend-agent")
            self.assertIn("backendSecurity", stored["roles"])

    def test_invalid_role_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            error = self.run_cli(Path(raw), "setup", "--role", "unknown=agent", expected=2)
            self.assertIn("--role", error["error"])


if __name__ == "__main__":
    unittest.main()
