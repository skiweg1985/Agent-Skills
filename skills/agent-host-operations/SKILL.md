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


## Sandboxed shells and worktrees

A CLI agent may run its shell commands inside a sandbox whose writable area is
derived from the **repository the agent was started in** — not from the worktree
it was told to work in. When those differ, writes inside the worktree are denied,
and a process that writes during start-up does not fail loudly: it blocks. A test
suite whose fixture boots the application then hangs indefinitely at zero CPU,
looking like a deadlock in the code while the same test passes in a fraction of a
second outside the sandbox.

Such a sandbox usually also unshares the network, so `git push`, tracker calls and
package installs from a sandboxed shell cannot work, even though the agent's own
API and MCP calls still do. Work can then be committed but never published, which
reads from outside as an agent that stopped for no reason.

Before dispatching an agent into a worktree, verify both properties rather than
assuming them:

```bash
touch <worktree>/.write-probe && rm <worktree>/.write-probe   # writable?
git -C <worktree> ls-remote origin >/dev/null                  # network?
```

If either fails, fix the invocation rather than the code. For Codex specifically,
`--add-dir <dir>` adds a writable directory alongside the primary workspace and
`-C, --cd <dir>` moves the working root; a flag that forces an automatic-approval
sandbox overrides whatever `sandbox_mode` the configuration file sets. Keep the
repository itself writable when the worktree's `.git` file points back into it,
or commits will fail too.

Diagnose a suspected sandbox block by its signature: the process sits in
`futex_do_wait` at 0% CPU with no database or socket file descriptors open, and
the same command succeeds immediately when run outside the sandbox. Orphaned
processes whose sandbox parent has died keep running and must be cleaned up
explicitly; nothing reaps them.

## A changed SSH host key is a stop, not an obstacle

When a host key no longer matches, SSH is doing its job. The change may be a
rebuilt machine, or it may be someone in the middle — and nothing you can see from
your side tells the two apart. Removing the known-hosts entry to get the command
through discards the only warning you were going to get.

Report it and stop. Replace a key only after the user confirms the change is
expected, and keep a backup of the file you edited. Host keys are per port as well
as per host, so the same machine reached on another port legitimately presents a
different key — that is not a mismatch and needs no action.

## Agent personas on a shared host

Resolve the worker persona for each agent from the current host or orchestrator configuration, not from this shared skill. Do not hard-code a persona-to-agent mapping or a hostname here; different hosts assign different display names, and this skill must stay portable across all of them. A model family or provider name such as GPT, Claude, Gemini, or OpenRouter is never itself an agent persona.

Before any Linear write, verify that the client's OAuth/MCP identity matches the intended persona. Every dispatched run must also receive a stable session identifier and owning issue identifier; stop before repository-host writes when either is missing.
