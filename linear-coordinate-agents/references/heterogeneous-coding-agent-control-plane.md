# Heterogeneous coding-agent control plane

Use this reference when Linear or another tracker should trigger and supervise several different coding-agent runtimes (for example Codex, Claude Code, and a third reviewer) concurrently.

## Recommended architecture

Separate five concerns:

1. **Work record:** Linear issue, relations, accountable assignee, acceptance criteria, and autonomy boundary.
2. **Trigger:** Prefer an authenticated event. Use polling only when inbound connectivity is unavailable and as a reconciliation fallback.
3. **Durable control plane:** Persist workflow state, idempotency, retries, timeouts, concurrency, cancellation, and human approval outside the coding-agent process.
4. **Agent adapter:** Normalize each vendor SDK/CLI into `start`, `send`, `status`, `cancel`, `resume`, and `stream_events`.
5. **Execution isolation:** One issue, branch, worktree/container, credential scope, process supervisor, and resource budget per run.

Do not make peer-to-peer agent chat the primary coordination mechanism. Keep one planner/control plane authoritative and let Linear plus the workflow journal hold shared state.

## Linear trigger choices

### Native agent integration

This is the preferred user experience when the personas can become Linear app users:

- Create an OAuth application with `actor=app`, request `app:assignable` and the minimum other scopes, and enable **Agent session events**.
- Delegation sets the app as `delegate`; the accountable human remains `assignee`.
- Delegation or mention creates an `AgentSession` and sends a `created` `AgentSessionEvent` containing issue context and `promptContext`.
- A webhook receiver must return within 5 seconds. For a newly created session, emit an activity or external URL within 10 seconds so Linear does not mark it unresponsive.
- Agent sessions expose native lifecycle states such as `pending`, `active`, `awaitingInput`, `error`, `complete`, and `stale`. Link the run dashboard and eventual PR through session external URLs.

Official references:
- https://linear.app/developers/agents
- https://linear.app/developers/agent-interaction

### Ordinary assignees

Assigning an issue to an ordinary workspace user does not start a local process. Use a signed Linear issue-change webhook or bounded poller and re-fetch the issue before launch.

Linear signs the exact raw request body with HMAC-SHA256 in the `Linear-Signature` header. The endpoint must be public HTTPS, answer within 5 seconds, and expect retries. Do not assume a generic webhook adapter accepts this header; validate the original Linear signature before forwarding an authenticated internal event.

Official reference: https://linear.app/developers/webhooks

## Durable execution choices

Choose according to operating scale rather than novelty:

- **Restate:** strong default for a small self-hosted control plane; durable webhooks/steps, key-scoped state and concurrency, signals, pause/resume, human approval, journals, and Python/TypeScript/Go/Java support.
- **Temporal:** mature choice for business-critical, multi-team workflows; strong workflow identity, retries, signals/updates, child workflows, pause, history, and operational tooling, with more infrastructure and determinism discipline.
- **Hatchet:** practical task-queue/workflow alternative with workers, affinity, concurrency, rate limits, retries, event waits, cancellation, OpenTelemetry, and self-hosting.
- **Trigger.dev / Inngest:** convenient managed options for event-triggered long-running tasks, retries, checkpoints, queues, and dashboards when SaaS or their self-hosted worker model is acceptable.
- **systemd + SQLite/Postgres:** acceptable MVP for a few local workers, but recovery, lease renewal, retry policy, reconciliation, and audit history must be implemented explicitly.

The workflow engine owns lifecycle state; a process supervisor or container runtime owns the live OS process. A durable workflow cannot magically resume an arbitrary subprocess after host loss, so persist the vendor session ID and make resume/reconciliation explicit.

References:
- https://docs.restate.dev/ai
- https://docs.temporal.io/ai
- https://docs.hatchet.run/
- https://trigger.dev/docs
- https://www.inngest.com/docs/learn/inngest-functions

## Codex adapter

Preferred order:

1. Use the supported Codex Python or TypeScript SDK for programmatic threads, continuation/resume, sandbox selection, and structured events.
2. Use `codex exec --json` for a simpler CI/MVP adapter; persist `thread_id`, parse JSONL events, use an output schema where useful, and set an explicit least-privilege sandbox.
3. Use app-server only for a rich local client that needs approvals, history, and streaming. Its remote WebSocket transport is documented as experimental/unsupported for production; do not expose it as the production control-plane API.

Avoid deprecated `--full-auto`; use explicit `--sandbox workspace-write`. Full access belongs only inside a separately isolated runner.

References:
- https://learn.chatgpt.com/docs/codex-sdk
- https://learn.chatgpt.com/docs/non-interactive-mode
- https://learn.chatgpt.com/docs/app-server
- https://learn.chatgpt.com/docs/environments/git-worktrees

## Claude Code adapter

Preferred order:

1. Use the Claude Agent SDK for Python or TypeScript when the controller needs structured messages, tool approval callbacks, interruption, and resume.
2. Use `claude -p` with JSON/stream-JSON for a simpler runner. For deterministic scripted execution, prefer `--bare` and pass settings, MCP config, prompts, and allowed tools explicitly. Bare mode requires explicit provider credentials rather than subscription OAuth.
3. Use hooks for deterministic lifecycle enforcement and notifications, not as the durable queue.

Do not base cross-vendor orchestration on:

- **Claude Routines:** useful schedule/API/GitHub-triggered cloud sessions, but currently research preview and account-scoped.
- **Claude Agent Teams:** experimental, coordination-heavy, and unavailable as teams in `-p`/Agent SDK headless sessions; use them only for interactive Claude-only parallel exploration.

Self-hosted Claude environments can route cloud sessions to organization-controlled runners and support runner capacity/autoscaling, but remain a Claude-specific execution plane rather than the heterogeneous control plane.

References:
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/hooks-guide
- https://code.claude.com/docs/en/routines
- https://code.claude.com/docs/en/agent-teams
- https://code.claude.com/docs/en/self-hosted-environments

## Protocol boundaries

- **MCP:** gives an agent tools and data. It is not a scheduler, queue, lease, or run-state store.
- **ACP:** standardizes coding-agent/client sessions, plans, tools, permissions, diffs, cancellation, and transports. It is useful as an adapter surface when a worker supports it, but remote-agent support is still evolving; it does not replace durable execution.
- **A2A 1.0:** supports discovery through Agent Cards and stateful remote tasks, streaming, artifacts, cancellation, and push notifications across independent agent services. Use it when workers truly run as separate remote services; it is unnecessary overhead for three local subprocesses.

References:
- https://modelcontextprotocol.io/
- https://agentclientprotocol.com/get-started/introduction
- https://a2a-protocol.org/latest/

## Parallelism and third-agent policy

Use a capability map rather than round-robin routing. Keep one implementation owner per issue and split work at observable contract boundaries. Start the third agent as an independent reviewer or verifier before adding another concurrent writer; model/provider diversity is most useful for review, security, test, and acceptance-criteria checks.

Normalize every adapter to these states:

`queued → preparing → working → awaiting_input → validating → review_ready → completed|failed|canceled`

Persist vendor session IDs, workflow/run IDs, Linear session ID, branch/worktree, process/container ID, last event, cost/resource counters, and current approval gate.

## Production verification sequence

1. Validate provider-specific webhook signatures against the exact raw bytes.
2. Acknowledge fast and enqueue durably before doing model or Git work.
3. Prove duplicate delivery returns the existing run.
4. Prove blocked, reassigned, wrong-project, or overlapping issues do not launch.
5. Run a read-only dry run through each adapter.
6. Run one non-production issue to a review-ready change.
7. Run two disjoint issues concurrently in isolated worktrees/containers.
8. Exercise input-required, cancellation, process crash, controller restart, provider timeout, and resume.
9. Keep a periodic reconciler for missed events and orphaned runs; do not use cron as the primary execution lifecycle.
