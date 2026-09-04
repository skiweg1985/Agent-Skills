# Automatic external-agent dispatch from Linear

Use this reference when a Linear assignment or delegation should launch external coding workers such as Codex or Claude Code automatically and concurrently.

## Choose the ownership model first

- A normal Linear **assignee** is an ownership record. Changing it does not inherently start a local CLI process.
- An installed Linear **agent/app user** is triggered through the issue's delegate/agent relationship and Agent Session events. Keep a human or accountable teammate as assignee when the workspace uses delegation semantics.
- If existing personas are ordinary workspace users but must launch local CLIs, add an external dispatcher. Do not assume assignment itself is executable.

## Preferred event flow

1. The project manager refreshes Linear and Git state, verifies the issue is unblocked, and checks write-set overlap.
2. Set the accountable assignee and the intended agent/delegate.
3. Linear emits an Agent Session or issue-change event.
4. A signature-validating receiver acknowledges quickly and puts a launch request on a durable queue.
5. The dispatcher re-fetches the issue instead of trusting webhook payload state.
6. It verifies project/team, delegate, status, labels, blockers, ownership comments, autonomy, and repository rules.
7. It acquires an idempotency lock keyed by issue, delegate, and assignment/delegation revision.
8. It creates a dedicated branch and worktree, then launches the mapped CLI in a supervised process.
9. The worker claims the issue in natural language, implements only its declared write set, validates the result, pushes only when authorized, opens or updates one linked PR, and reports evidence to Linear.
10. The dispatcher records terminal state and releases only the process slot, not the issue's ownership record.

## Parallelism and collision control

Parallel workers are safe only when each has:

- a different Linear issue;
- one accountable owner;
- an explicit write set whose exclusive paths overlap no other worker's (files declared shared on both issues may overlap);
- a dedicated branch and worktree;
- an independently supervised process;
- a per-agent and global concurrency limit.

Use a deterministic process name such as `linear-agent-<issue>-<agent>`. A duplicate delivery must return the existing run rather than launch another worker. Reassignment, delegate removal, or a newly discovered blocker should prevent a queued run from starting; do not kill an active run destructively without an explicit policy.

## Webhook versus polling

Prefer Agent Session webhooks for immediate starts when a publicly reachable, signature-compatible receiver and durable queue exist. Use bounded polling when inbound connectivity is unavailable. Pollers must retain the same re-fetch, idempotency, and ownership checks; a shorter interval is not a substitute for event identity.

Do not assume one webhook implementation accepts another provider's signature header or canonicalization. Verify the exact header and signed bytes end to end. If formats differ, add a small provider-specific receiver that validates the original signature before forwarding an authenticated internal event.

## Worker prompt contract

Every external worker prompt should name:

- Linear issue identifier and repository;
- current branch/worktree;
- required repository working agreements to read first;
- acceptance criteria and explicit exclusions;
- resolved autonomy level;
- allowed delivery boundary, normally PR-only unless explicitly raised;
- required Linear refreshes and natural-language progress comments;
- validation and runtime smoke-test requirements.

The worker must not infer that successful CI permits merge or deployment.

## Identity and credentials

Give every worker an independently auditable Linear identity or agent actor. If several sessions share one account, require stable session identifiers in every comment. Prefer a GitHub App or scoped machine identity over a project owner's personal credential. Keep Linear, repository, and model-provider credentials separate and never place them in prompts, issue comments, logs, or commits.

## Agent specialization

Maintain a capability map from explicit user direction and observed role boundaries, for example frontend-focused versus backend/security-focused. User-stated specialization overrides a merely convenient assignment. For mixed full-stack issues, keep one accountable owner and split a separate linked issue at an observable contract boundary when parallel work would otherwise share files or decisions.

## Verification before enabling live dispatch

Test in this order:

1. signature validation with a recorded synthetic event;
2. duplicate delivery produces one launch;
3. blocked or wrong-project issue produces no launch;
4. one dry-run worker reads and comments but does not modify the repository;
5. one real non-production issue reaches a review-ready PR;
6. two disjoint test issues run concurrently in separate worktrees;
7. reassignment and failure paths leave truthful Linear comments and no orphaned locks or processes.
