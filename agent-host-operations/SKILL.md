---
name: agent-host-operations
description: Safe operating conventions for autonomous coding work on this shared Codex and Claude Code agent host. Use when preparing, implementing, testing, reviewing, or publishing project changes on coder2.
---

# Agent Host Operations

## Working rules

1. Confirm the repository, issue, branch, and acceptance criteria before changing code.
2. Use a dedicated Git worktree and branch for each agent run; never let concurrent agents write to the same checkout.
3. Do not modify or merge `main`/`master` directly. Publish work through a reviewable branch or pull request when requested.
4. Read and follow repository-local `AGENTS.md`, `CLAUDE.md`, and project skills. Repository rules take precedence over this general skill.
5. Keep secrets out of prompts, logs, commits, patches, and final reports.
6. Run the relevant tests, linters, builds, or browser checks after changes. Report the real command results; do not infer success.
7. Before finishing, inspect the Git diff and status. State what changed, what was verified, and any remaining risk or blocker.
8. Ask for human approval before merge, deployment, destructive operations, or changes outside the assigned scope.
