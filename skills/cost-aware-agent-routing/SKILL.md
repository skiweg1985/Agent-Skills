---
name: cost-aware-agent-routing
description: Route software work between a low-cost support agent, premium frontend or backend specialists, and a coordinator. Use when assigning, splitting, escalating, reviewing, or handing off work across multiple coding agents, choosing a cheap versus premium model, or preventing overlapping agent work.
---

# Cost-Aware Agent Routing

Use the least expensive capable role for each bounded slice of work, but escalate before low confidence turns into rework. Cost optimization never overrides repository rules, ownership, security, verification, or merge and deployment gates.

## Resolve the team profile

Map the active agents to these role classes from current configuration, repository guidance, or the coordinator's prompt. Do not infer a role only from a display name.

- **Coordinator:** owns assignment, dependency and conflict checks, acceptance criteria, independent verification, and human gates. The coordinator does not silently take implementation work already owned by another agent.
- **Support agent:** the low-cost default for reconnaissance, issue triage, repository mapping, documentation, test and log analysis, first-pass review, and small isolated changes with obvious verification.
- **Frontend specialist:** owns interaction design, accessibility, frontend implementation, visual consistency, browser verification, and frontend architecture.
- **Backend specialist:** owns APIs, persistence, migrations, integrations, security-sensitive implementation, performance investigation, and deep debugging.

A person or model may cover more than one class only when the current team profile says so. Keep one accountable owner per issue.

## Route work in this order

1. Read the current request, repository working agreement, issue, dependencies, and active ownership before selecting a role.
2. Describe the smallest observable work slice and its write set.
3. Start with the support agent when the task is bounded, low risk, reversible, and independently verifiable.
4. Route directly to a specialist when the task is clearly within that specialty or carries an escalation trigger below.
5. For mixed work, define the contract boundary first, then split into non-overlapping issues or sequential handoffs. Do not assign two agents to the same files or decision surface concurrently.
6. Require independent verification before accepting a worker's completion claim.

## Route a decision, not only work

A question that needs a judgement call is routed like work, with one difference:
it goes to the **most capable** agent for its domain, not to the cheapest one
that could produce an answer. Cost control applies to volume. It does not apply
to the few decisions a project turns on, where a cheap wrong answer is paid for
in the rework it causes.

- A decision inside one specialty goes to that specialist.
- A decision spanning specialties goes to the agent whose specialty owns the
  contract the decision changes. When none does, it goes to the strongest
  generalist on the team.
- The support agent prepares decisions and does not make them alone. Gathering
  the options, the evidence and the trade-offs is exactly the bounded, verifiable
  work it is good at; choosing between them is not.

Require the answer to name the option chosen, the options rejected, and the
evidence that would change the choice. An answer without the rejected options is
an opinion, and the next agent cannot tell whether the alternatives were weighed
or never seen.

Record the decision on the issue that raised the question, not in a report. A
decision nobody can find is made again, differently.

## Good support-agent work

Prefer the support role for:

- locating relevant code, documentation, tests, ownership, and recent changes;
- refining an issue into concrete acceptance criteria and exclusions;
- reproducing a defect without changing production state;
- summarizing logs, test failures, diffs, or external documentation;
- generating fixtures, documentation, test plans, and review checklists;
- first-pass code review that identifies candidates for specialist attention;
- a small local fix when the expected behavior, affected files, and validation command are already clear.

A support agent may prepare a patch or branch, but tests passing do not grant permission to push, merge, deploy, or change external systems.

## Escalate early

Escalate to the appropriate specialist or coordinator when any of these applies:

- requirements or product behavior remain ambiguous after a bounded discovery pass;
- the change affects architecture, shared contracts, authentication, authorization, secrets, personal data, migrations, production, or destructive behavior;
- the work crosses frontend and backend boundaries without an agreed contract;
- the fix requires a broad refactor or touches another agent's active write set;
- failures are intermittent, environment-dependent, or still unexplained after one focused attempt;
- the support agent cannot state a reliable verification method;
- a review finding has high security, data-loss, compatibility, or operational impact;
- the user, repository, or project requires a premium-model review.

Do not keep retrying a cheap model with increasingly large context when the uncertainty itself is the reason to escalate.

## Control cost without losing evidence

- Give the support agent a narrow question, explicit paths, and a concrete output contract.
- Reuse concise evidence summaries instead of forwarding entire transcripts.
- Separate discovery from implementation so specialists receive a small, grounded handoff.
- Prefer cached or stable repository context where the provider supports it.
- Stop after one focused failed implementation attempt and reassess routing.
- Use premium specialists for decisions and hard implementation, not for mechanical repository inventory that the support role can prepare.

## Handoff contract

A handoff must contain:

1. **Goal:** the observable result and acceptance criteria.
2. **Evidence:** relevant issue state, repository rules, current behavior, and reproduction details.
3. **Scope:** files, interfaces, write set, and explicit exclusions.
4. **Work completed:** analysis, branch or patch, and commands already run.
5. **Open risk:** uncertainty, failed attempts, conflicting ownership, or decisions still needed.
6. **Next action:** the smallest specialist or coordinator action that moves the work forward.

Use concise prose in the project's language. Include exact identifiers and paths only when they help the receiver act. Never include credentials or sensitive logs.

## Coordinate with other skills

- Use `agent-host-operations` for worktree, branch, test, secret, and approval safety.
- Use `linear-coordinate-agents` when Linear owns assignment, state, handoffs, or activity records.
- Repository-local instructions and the user's current direction override this routing default.

## Invocation examples

Explicit support assignment:

```text
Use cost-aware-agent-routing as the support agent. Map the repository and produce a handoff; do not implement cross-cutting changes.
```

Specialist assignment after discovery:

```text
Use cost-aware-agent-routing as the backend specialist. Continue from this support handoff, verify its evidence independently, and stay inside the declared write set.
```

Coordinator routing:

```text
Use cost-aware-agent-routing to split this issue between support discovery and one accountable specialist without overlapping files.
```

## Completion check

Before reporting completion, confirm that the selected role matched the risk and specialty, ownership stayed unambiguous, real verification was run, the handoff exposed remaining uncertainty, and no merge, deployment, destructive, or external-write gate was assumed from model capability alone.
