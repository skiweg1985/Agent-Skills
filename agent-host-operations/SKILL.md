---
name: agent-host-operations
description: Safe operating conventions for autonomous coding work on shared Claude Code, Codex, and OpenCode agent hosts. Use when preparing, implementing, testing, reviewing, or publishing project changes on a multi-agent development host.
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
9. When several agents share one repository-host account, preserve the real worker identity on every new commit and GitHub write: use the agent's display name as the per-commit Git author/committer name, add `Agent`, `Agent-Session`, and issue trailers, and sign PR bodies, reviews, issue comments, and PR comments with the agent name plus session identifier. Keep the shared account's configured email unchanged; if none exists, resolve and use that authenticated account's provider-supported noreply address per commit. Never modify global or shared repository Git identity, and do not rewrite published history merely to add attribution. Follow the detailed shared-account procedure in `linear-coordinate-agents` when that skill is available.

## Agent personas on a shared host

Resolve the worker persona for each agent from the current host or orchestrator configuration, not from this shared skill. Do not hard-code a persona-to-agent mapping or a hostname here; different hosts assign different display names, and this skill must stay portable across all of them. A model family or provider name such as GPT, Claude, Gemini, or OpenRouter is never itself an agent persona.

Before any Linear write, verify that the client's OAuth/MCP identity matches the intended persona. Every dispatched run must also receive a stable session identifier and owning issue identifier; stop before repository-host writes when either is missing.
