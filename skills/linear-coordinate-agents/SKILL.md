---
name: linear-coordinate-agents
description: Coordinate multiple autonomous agents through shared Linear projects and repository issue trackers while reading durable repository working agreements ahead of finite project plans, repeatedly refreshing current state, resolving risk-aware autonomy, routing out-of-scope findings to sensitivity-appropriate records, and writing concise updates in a natural teammate voice. Use when an agent joins a Linear-managed project, selects or assigns work, claims an issue, collaborates with other agents, decides whether it may open or merge a PR, works autonomously or on a schedule, checks repository issues for work it owns, reports defects found outside its scope, publishes progress or blocker updates, hands work over, resumes stale work, must decide where a rule or a recurring checkpoint belongs, must prevent duplicate and conflicting changes across parallel tasks, or must tell apart several concurrent sessions signed in as the same Linear account.
---

# Coordinate Agents Through Linear

Use Linear as the shared coordination record for parallel agent work. Use the authenticated Linear account and issue assignee as the ownership lock; use readable comments and project updates as the audit trail. Where several sessions can sign in as one account, the account alone no longer identifies a worker — carry the session identifier in comments so the trail stays readable.

## Follow the authority order

Apply instructions in this order:

1. Follow the user's current request and approval boundaries.
2. Follow durable repository working agreements — `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, or their documented equivalent. These outlive any single planning project.
3. Follow the finite planning record: the Linear project description, its milestones, and its definition of done.
4. Follow the team's existing Linear workflow, language, statuses, labels, and assignment rules.
5. Apply the defaults in this skill only where neither the repository nor the project has a more specific rule.

**Read the repository's working-agreement file before the project description, and read it in the same session you act in.** A Linear project is a finite effort that gets closed; the repository is the product and outlives it. Durable rules — roles, write areas, autonomy, merge gates, traceability — therefore belong in the repository, and a closed project must not take them with it.

When the repository file and the project description disagree, the repository file wins for durable rules and the project description wins for current scope. Report the contradiction instead of silently picking one: a stale project description is a defect, not a variant. Watch specifically for rules that were true once and are now obsolete — "no CI exists in this repository" is the classic case, and acting on it skips a gate that has since been added.

If no working-agreement file exists but the project description carries durable rules, say so once and propose moving them into the repository. Do not create or edit that file unprompted; it governs everyone's work, not just this issue.

Treat the resolved autonomy policy as permission only for the actions it includes. No autonomy level permits production changes, secret exposure, irreversible external actions, destructive data changes, or expansion beyond the project scope without a current explicit user instruction.

## Resolve risk-aware autonomy

Resolve the effective autonomy level during discovery and every coordination refresh. Prefer the highest level that is clearly safe; do not impose production ceremony on a disposable prototype.

Use the mutually exclusive Linear project-label group `Agentenautonomie` when present:

- `A0 – Nur lesen`: read, analyze, claim, and report in Linear; do not modify repositories, applications, infrastructure, or external systems.
- `A1 – Bis PR`: additionally implement, test, commit, push, and create or update review-ready PRs; leave them unmerged and do not deploy.
- `A2 – Bis Merge`: additionally self-review and merge the agent's own PR for its assigned issue after the merge gates below pass; do not deploy.
- `A3 – Maximale Autonomie`: additionally select and split in-scope work, self-merge, and operate local, preview, development, or staging environments that are clearly non-production and reversible.

Resolve the level in this order:

1. Apply the user's current instruction first. A narrow current instruction can raise or lower permission for the named action.
2. Read the repository working-agreement file. When it states an autonomy level with its exclusions, that is the durable baseline — it survives project closure, whereas a project label does not. Its exclusions always apply, even under a higher level from another source.
3. Read the project autonomy label and an optional project document titled `Agenten-Autonomie`. The document may narrow the label or describe project-specific checks and targets; it is not required for routine prototype work.
4. If the project has no autonomy label, infer A3 when current evidence clearly identifies a prototype, proof of concept, experiment, or project without production. An explicit statement in the Linear project summary or description is sufficient. Otherwise require consistent repository evidence such as only local or preview targets and no production configuration. If production status is unclear, use A1.
5. Read an optional issue-description line matching `Agenten-Autonomie: A0|A1|A2|A3`. It may only lower the project level. Ignore a higher value as permission and report the mismatch when it affects the next action.
6. Apply repository instructions, branch protection, and active user restrictions. When rules conflict, use the stricter rule unless the user's current instruction explicitly resolves the conflict.

Treat a project as production-connected when it has any production environment or release target, live customer or employee data, public users, shared business-critical infrastructure, or writes to a live external system. The absence of the word "production" is not evidence that none exists. Re-evaluate this classification whenever project metadata, deployment configuration, or repository instructions change.

For A2 and A3, merge only when the issue remains assigned to the authenticated agent, the PR is linked to that issue, the latest Linear and Git refresh shows no overlap, acceptance criteria are verified, the branch is mergeable, and no requested changes or unresolved review findings remain.

- On a production-connected project, require every configured CI check to pass. If no CI exists, require replacement checks explicitly named in repository or project guidance.
- On an A3 prototype or no-production project, use the strongest relevant validation already available: tests, build, lint, type checks, or a focused smoke test. Missing CI alone is not a blocker, and creating process infrastructure is not a prerequisite for merging prototype work.
- For a disposable local or preview deployment under A3, a separate runbook is optional when the target, verification, and recreate or rollback path are obvious from the repository. For a shared development or staging target, establish the target, health check, and rollback or redeploy path before changing it.

An explicit project lead comment may grant one action-scoped exception up to A3. It does not authorize production or destructive work. Never reuse an old exception as standing permission for later issues or actions.

## Keep durable rules and finite plans apart

A repository is a product and does not end. A Linear project has a state that ends. Modelling one permanent project per repository breaks both: the project never reaches a completed state, its milestone percentages stop meaning anything once later efforts land in the same list, and nobody is ever forced to decide what happens to the leftovers.

Prefer one finite Linear project per effort with a beginning and an end — `<product> V1 – prototype`, then `<product> – IPv6 support` — each with its own milestones and a real completion. Use an initiative as the permanent product bracket above them when the workspace has initiatives. Propose this shape; do not restructure an existing workspace convention on your own, and check whether sibling projects follow the same convention before changing one of them.

Given that split, place each rule where it survives:

- **Repository, durable:** roles, write areas, autonomy level and its exclusions, merge gates, contract-before-implementation, traceability conventions, language conventions.
- **Linear project, finite:** goal, milestones, definition of done, scope boundaries, target dates.

**A recurring human checkpoint belongs to the team, not to a milestone.** A milestone is reached once and then closed forever, so it cannot express "the client tests this independently after every extension". A workflow state before the terminal one — an acceptance state owned by the client — applies automatically to every future issue and every future project. Propose the state; workflow states are typically not creatable through the API and need a person in the UI.

When acting inside a project whose description carries durable rules, treat that as the state to migrate, not as the intended design.

## Enforce the coordination invariants

- Resolve the authenticated Linear user before selecting or changing work. Use `get_user` with `query: "me"`, or the connector's exact equivalent. Record the returned user ID, display name, and email for this run. Never infer identity from the machine user, prompt, repository, or prior run.
- Resolve the current session identifier alongside the Linear identity and keep both for the run. Use whatever stable name the runtime exposes for this session — the session name other agents address it by, its session ID, or the worktree or branch it works in. One Linear account can be driven by several concurrent sessions, so the account alone does not say who wrote what.
- **The assignee lock does not separate two sessions on the same account.** An issue assigned to the authenticated user looks resumable to every session signed in as that user, and each one reads its own claim comment as confirmation. Before treating such an issue as yours, check whether a recent comment on it carries a different session identifier than the current one. If it does, treat the issue as actively owned by that session: do not edit its branch or write set, and negotiate the split with that session before continuing.
- Use the authenticated Linear account as the issue assignee. In the Codex Linear connector, assign with `save_issue` and `assignee: "me"`; do not use `delegate` as a substitute for ownership.
- Treat an issue assigned to another user as owned and unavailable. Never overwrite that assignee merely because the issue looks idle, blocked, or stale. Require an explicit handoff, reassignment by the user/project lead, or release by the current owner.
- Treat an issue assigned to the current authenticated user as resumable by that agent only after refreshing the issue and its activity.
- Keep one accountable agent per issue. Split parallel work into separate linked or child issues whenever scopes overlap or could touch the same files, resources, schemas, deployment targets, or decisions.
- Never perform modifying work from a coordination snapshot older than 15 minutes. Refresh sooner at every implementation boundary or when new project activity appears.
- Keep routine ownership, progress, blockers, and completion evidence on the issue. Use project comments or project status updates only for cross-issue decisions, project health, milestone changes, or coordination that affects multiple issues.
- Write comments in the project's established language and in the voice of a human teammate. Preserve existing technical status and label names unless the project explicitly says otherwise.
- Append corrections and new events. Do not delete or silently rewrite prior coordination comments; the activity stream is the audit trail.
- Stop before shared modifying work if the Linear connector is unavailable, the current user cannot be resolved, comments cannot be read, or assignment cannot be verified.

## Start every work session with discovery

1. Resolve the current user with `me` and retain the stable user ID and display name. Resolve the session identifier in the same step, and check whether other sessions are currently signed in as the same Linear account.
2. Fetch the target project, including labels, members, milestones, resources, the optional `Agenten-Autonomie` document, recent project comments, and recent project status updates when the connector exposes them.
3. List relevant project issues with assignee, state, priority, dependencies, parent, milestone, and recent update time.
4. Fetch each candidate issue with relations and read all recent comments before choosing it.
5. When a repository issue tracker exists, resolve the authenticated repository-host identity independently from Linear. Inspect open issues assigned to that account and recent mentions, handoffs, or blocker reports relevant to the project. Never infer that the Linear and repository accounts represent the same person.
6. For a scheduled, recurring, resumed, or otherwise autonomous run, review repository issue activity before selecting new work even when Linear already contains a candidate.
7. Read the repository working-agreement file — `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, or the documented equivalent — in every session that will modify anything, not only when the issue touches code. Note any rule there that the project description contradicts. Inspect active branches or worktrees when the issue changes code or configuration.
8. Build a short conflict map of active issues and their declared or observable write sets, branches, infrastructure targets, shared schemas, and dependencies.
9. Resolve the current autonomy level and whether the project is prototype-only, non-production, production-connected, or unclear. Record the evidence used.
10. Record a coordination watermark using the newest server timestamps observed in Linear and the repository issue tracker and, for code work, the fetched Git remote refs used for comparison.

Complete discovery only when the current Linear identity, any repository-host identity, the repository working agreements, effective autonomy level, production classification, assigned repository issues, every candidate's current owner, and overlapping activity are known. If repository identity or issue activity cannot be read, do not assume that no responsibility exists; report the missing surface and continue only with work whose ownership is independently verified.

## Join as project manager conservatively

When the user explicitly asks the agent to join or lead a Linear project as project manager, turn that mandate into the smallest useful, auditable project-level changes after discovery:

1. Resolve `me`, the exact project, current lead and members, project status, active issues, dependencies, recent project comments, and status updates.
2. If the project has no lead, set `lead: "me"` only when the user's request clearly delegates project leadership. Re-read the project and verify that the authenticated user appears as lead and member.
3. If issues are already `In Progress` or `In Review` while the project remains `Backlog`, move the project to its existing started state. Do not start an otherwise inactive project merely to signal presence.
4. Preserve issue ownership and declared write sets. A project-manager mandate does not authorize taking an implementer's issue or editing its branch.
5. Leave one concise project comment stating the current integration or dependency order, what the agent will coordinate, and any evidence surface that remains unavailable. Use `projectId`, not `issueId`.
6. Do not invent priority, target dates, milestones, health, autonomy, or delivery commitments merely to make the project look managed. Change them only from explicit user direction or current project/repository evidence.
7. Verify every project write by reading the project and newest comments back from Linear before reporting success.

Repository access may become available after discovery. When credentials are added or changed, resolve the repository-host identity and permissions again and then complete the previously missing repository checks; do not keep treating an earlier unauthenticated probe as current state.

## Keep the project state fresh

Treat the initial discovery as a snapshot that expires. Run a coordination refresh:

- before every new material implementation slice after planning or analysis;
- immediately after resuming from a pause, approval, handoff, tool wait, or new user turn;
- at least every 15 minutes during active modifying work, even when the planned scope has not changed;
- before expanding the scope or write set;
- before committing, pushing, opening or updating a review, integrating, changing the issue state, or declaring completion;
- after every scheduled wake or autonomous work-selection cycle;
- immediately when a notification, repository issue, comment, assignment change, branch update, or project-status change indicates other activity.

Use a delta refresh after the initial full discovery:

1. List every project issue changed since the coordination watermark. If the connector cannot filter by update time, perform a bounded full refresh of all active project issues.
2. Re-fetch every changed active issue with its assignee, relations, state, latest comments, ownership statements, declared write set, and branch or target. Recognize historical `[agent-coordination:*]` markers, but do not create new ones.
3. Re-fetch the current agent's issue and verify that its assignee still matches the authenticated Linear user.
4. Re-read project labels, the optional autonomy document, recent project comments, and project status updates created or changed since the watermark. Recalculate the effective autonomy level and production classification.
5. Re-fetch repository issues changed since the issue-tracker watermark, or perform a bounded refresh of open assigned issues, mentions, handoffs, and relevant blockers when filtering is unavailable. Verify which items still belong to the authenticated repository account.
6. For repository work, fetch the relevant Git remote without changing local work. Compare the current base branch and every branch or review named by another active claim against the current worktree and declared write set.
7. Rebuild the conflict map and advance the Linear, issue-tracker, and Git watermarks only after every required read succeeds.

Do not post a comment for a refresh that found no material change. Keep the exact watermark in working state. Mention it in a real update only when the timestamp or Git ref helps another person judge freshness or resolve a possible conflict, and write it as a natural sentence.

Complete a refresh only when the own issue assignment, assigned repository issues, effective autonomy level, production classification, every newly changed active claim, overlapping write surfaces, dependencies, and relevant remote repository state are current. If any required source cannot be refreshed, pause modifying work and report the stale coordination state; continue only read-only analysis that cannot create a conflict.

If a refresh reveals overlap, stop before the next edit, commit, push, or integration. Preserve existing local work, explain the conflict in a concise natural-language comment naming both issues and write sets, and resolve the overlap by splitting scope, adding a dependency, handing off, or obtaining a human decision. Never discard another agent's or the current agent's work to make the conflict disappear.

## Preserve attribution under a shared repository account

A shared GitHub or other repository-host account is transport authentication, not worker identity. When several agents publish through that account, make the actual agent and session visible in Git history and every repository-host write so a reviewer can distinguish workers without correlating external logs.

Before the first repository write, resolve four values from current evidence:

1. the authenticated repository-host account;
2. the agent's stable display name or persona for this run;
3. the current session identifier;
4. the owning Linear or repository issue identifier.

Use the persona explicitly supplied by the orchestrator, the current host or agent configuration, or the applicable host-operations skill. Otherwise use the authenticated Linear display name only when that identity is known to represent this worker. Product, runtime, provider, and model-family names such as `Codex`, `Claude Code`, `GPT`, `Gemini`, or `OpenRouter` are never a fallback persona unless an explicit host mapping assigns that exact name. Do not invent a persona from the machine username, shared GitHub login, branch author, or model provider. If the worker identity or session is ambiguous, stop before committing or writing on GitHub and ask the coordinator to resolve it; never emit a guessed signature merely to satisfy a format requirement.

For every new commit made through a shared account:

- set the Git author and committer **name** to the agent display name for that commit, for example with `git -c user.name="<Agent Display Name>" commit ...`; keep the repository's configured shared email unchanged so the commit remains linked to the intended repository-host account;
- if no commit email is configured, resolve the authenticated shared account first and use its provider-supported noreply address only for that commit. On GitHub.com, derive the recognized form from the authenticated account returned by `gh api user` as `<numeric-id>+<login>@users.noreply.github.com`; do not guess a human email, print it in comments, or persist it as global/shared repository configuration;
- do not change global Git configuration, and do not use repository-local `user.name` or `user.email` in a shared multi-worktree repository because it can leak into another worker's commits;
- keep the subject concise and conventional, then include these machine-readable trailers in the commit message:

  ```text
  Agent: <Agent Display Name>
  Agent-Session: <session-identifier>
  Linear-Issue: <ISSUE-KEY>
  ```

- use the repository issue key instead of `Linear-Issue` only when the work has no Linear record. Never claim another person's authorship and never place account emails, tokens, hostnames, or credentials in the trailers.

For every PR body, PR review, GitHub issue comment, and PR comment written through the shared account, append one natural signature line:

```markdown
— <Agent Display Name> / Session `<session-identifier>`
```

The signature is required even when the branch name contains the persona, because branches are mutable and GitHub renders every comment under the shared login. Keep routine Linear comments on their existing session-only signature: Linear already displays the distinct OAuth author, while GitHub does not.

Before push or handoff, verify the new commits without printing or publishing the shared email: inspect `%an` and `%B`, confirm the expected `Agent`, `Agent-Session`, and issue trailers, and ensure no commit from another active worktree was accidentally included. After every GitHub write, read the PR, review, or comment back and verify the visible signature. A successful API response alone is insufficient.

Apply this rule prospectively. If an unpublished current commit lacks attribution, amend it before push when safe. If a commit is already published or reviewed, do not force-push or rewrite history solely to add metadata; add the signed attribution to the PR body or a follow-up comment and preserve the immutable history. These labels improve operational provenance but are not cryptographic proof of identity.

## Write comments like a human teammate

Write the comment a helpful teammate would leave after doing the work. The reader should understand it on the first pass without decoding a template. Treat claim, status, conflict, blocker, release, handoff, and completion as internal event types, not labels to print.

- Start with what matters now, using everyday workplace language. Prefer "Ich übernehme ...", "Backend und Migration sind fertig", or "Ich hänge gerade an ..." over a formal status introduction.
- Most routine comments fit into one or two short paragraphs with two to five sentences. Use bullets only when three or more exact items are genuinely easier to scan. Most comments need no heading.
- Sound conversational and direct without becoming vague or chatty. Use first person where ownership matters and simple verbs such as "ist fertig", "fehlt noch", "ich prüfe", or "ich warte auf". Prefer these over audit language such as "verifiziert", "gemäß", or "vollständiger Status" when an ordinary sentence says the same thing.
- Let Linear identify the author and assignee. Do not repeat the account name in an `Agent:` field, and never publish Linear user IDs or account email addresses in routine comments.
- Sign every comment with the session identifier when the runtime exposes one, as a single trailing line separated from the body:

  ```markdown
  — Session `sud-15-secrets-a41f`
  ```

  This is the one exception to the no-scaffolding rule, and it exists because Linear shows only the account. Two sessions on one account otherwise appear as one person answering themselves, and neither can tell which comment it wrote. Keep the line to the identifier alone: no timestamp, no host, no account name, no status fields.
- Sign consistently or not at all. A signature only identifies a writer if every comment carries one — with gaps, a missing line is ambiguous between "another session" and "forgot". If the runtime exposes no session identifier, omit the line everywhere rather than inventing a name that will not match next run.
- Give each comment one purpose and only the context needed for that moment. Do not retell the full history or turn a short update into a criterion-by-criterion report.
- Keep a routine claim or progress comment around 120 words or less and a completion or handoff around 180 words or less. Put longer contracts, audits, or detailed evidence in the issue description, PR, document, or follow-up issue and link to it naturally.
- Keep technical facts exact where they help the next person act: issue ID, relevant path or service, branch, commit or PR, useful test result, blocker, protected scope, and next step. Precision should come from these concrete details, not from rigid fields.
- Write facts into sentences. Never use `[agent-coordination:*]`, `Agent:`, `Completed:`, `Current:`, `Next:`, `Write set:`, `Synchronized through:`, similar key-value scaffolding, or a table for a routine update. The trailing session line above is the only permitted exception, and it carries the identifier alone.
- Mention the last checked Linear time or Git ref only when it helps prevent a conflict. Write it naturally, for example: "Linear und `origin/main@abc1234` sind frisch abgeglichen."
- Mention another account with `@displayName` only when that person needs to decide, review, or accept a handoff.
- Read the draft once as the colleague receiving it. If it sounds like a generated status report, rewrite it as something you would actually send to a teammate while keeping the actionable details.

Include what the reader needs for the current situation and leave out fields that add no value:

- For a claim, say what you are taking on, the boundary that protects parallel work, and when you will update again. Name the branch or exclusions only when they help prevent overlap.
- For progress, say what is done, what remains, and the evidence that changes the next decision.
- For a blocker or conflict, say where you stopped, why, what work is preserved, and whose answer or action is needed.
- For a release or handoff, give the branch or commit, the useful validation result, the remaining work, and any risk the next person needs to know.
- For completion, say what now works, where it landed, how it was checked, the real review or merge state, and only genuine follow-up work.

Historical comments with the old machine markers remain valid evidence. Parse them during discovery, but never imitate their presentation in a new comment.

## Select suitable work

Prefer an existing issue that:

- belongs to the intended project and team;
- is unassigned or already assigned to the authenticated user;
- has clear acceptance criteria and enough context to act;
- has no unresolved blocker for the intended step;
- does not overlap another active issue's declared write set or target — files both issues declare as shared registration points are not an overlap;
- fits the user's authorized scope and the agent's available tools.

Choose by the project's priority and dependency order. Do not cherry-pick a convenient low-priority task while higher-priority unblocked work is ready unless the project rules or user direct otherwise.

Create or split issues only when decomposition is necessary and issue creation is within the requested project scope. Preserve the parent project, team, milestone, relations, and acceptance criteria. Do not create global statuses or labels for coordination unless the user explicitly requests that workspace-wide change.

Treat a repository issue as intake, not as a replacement for the Linear ownership lock. Before implementing it, link it to an existing Linear issue or create the smallest appropriate Linear work item when issue creation is authorized, then complete the normal claim flow. If no Linear record can be created or verified, report the repository issue but do not begin overlapping modifying work.

Do not automatically take stale assigned work. Post a coordination question or escalate it for reassignment, then select another safe issue while waiting.

Match work to each agent's explicit specialization before optimizing for availability. A user-stated role preference — for example, one agent should receive frontend-heavy slices while another handles backend or security work — overrides a merely convenient assignment. For a mixed issue, keep one accountable owner; when genuine parallelism would share files or decisions, split a linked issue at an observable contract boundary instead of assigning two workers to the same write set.

## Turn coordination into automatic execution

Treat ownership and execution as separate mechanisms:

- Assigning an issue to an ordinary Linear workspace user records ownership but does not inherently start Codex, Claude Code, or another local process.
- Delegating to an installed Linear agent/app user can trigger that integration through Agent Session events while the accountable assignee remains visible.
- When personas remain ordinary users but map to external coding CLIs, use a dispatcher triggered by a verified webhook or bounded polling loop.

Before launching a worker, the dispatcher must re-fetch the issue and repeat the same identity, assignment/delegate, blocker, overlap, autonomy, and repository-rule checks required for a manual claim. Never trust the webhook payload as the final coordination state.

Support parallel starts only across distinct issues with non-overlapping exclusive write sets (files declared shared on both issues may overlap), dedicated branches and worktrees, independently supervised processes, and explicit concurrency limits. Deduplicate launches with a durable key containing the issue, intended agent, and assignment/delegation revision. A repeated event returns the existing run rather than starting another worker.

Map agents to CLIs and specialties explicitly rather than inferring from display names. Each worker must receive the issue identifier, repository, working agreements, acceptance criteria, exclusions, autonomy boundary, validation requirements, and the requirement to report progress naturally in Linear. Successful tests or CI never imply merge or deployment permission.

Use [the automatic external-agent dispatch reference](references/automatic-external-agent-dispatch.md) for the event flow, webhook-versus-polling choice, worker contract, collision controls, credentials, and dry-run verification sequence. For a current heterogeneous control plane that combines Linear Agent Sessions with Codex, Claude Code, a durable workflow engine, and optional MCP/ACP/A2A adapters, also use [the heterogeneous coding-agent control-plane reference](references/heterogeneous-coding-agent-control-plane.md).

### Distribute this coordination skill to external workers completely

When Codex, Claude Code, or another worker runs on a separate agent host, install the whole `linear-coordinate-agents/` directory, including every referenced file, rather than copying only `SKILL.md`. A partial copy leaves valid-looking instructions with broken relative references. After transfer, compare file manifests or SHA-256 hashes and verify discovery with the client's explicit skill syntax.

Skill availability does not prove Linear connectivity. Check the Linear MCP or API authentication separately in every client and worker identity before allowing modifying coordination actions. One client having a healthy Linear connector says nothing about another client on the same host. Follow the shared-host installation and verification pattern in the `coding-agent-cli-orchestration` skill's `references/shared-agent-skills.md` when that umbrella is available.

## Claim an issue before implementation

Use the assignee as the ownership lock and a natural-language ownership comment as the declared scope:

1. Immediately re-fetch the issue and its latest comments.
2. Stop if another user is assigned or another active ownership comment covers the intended scope. Stop as well when a claim on the same account carries a different session identifier and is still active — same account is not same worker.
3. If unassigned, assign the issue to `me`. If already assigned to `me`, leave the assignment intact.
4. Re-fetch the issue and verify that the returned assignee ID equals the authenticated user ID.
5. Post a short ownership comment following the human-writing rules above.
6. Re-fetch the issue and comments once more. Begin modifying work only when the assignment still points to the authenticated user and no earlier competing claim exists.

Resolve a rare simultaneous claim deterministically: the earliest server-created comment that unambiguously claims the scope wins; if timestamps are exactly equal, the lexicographically smaller stable Linear user ID wins. When both claims come from the same account, that tiebreaker yields no winner — fall back to the lexicographically smaller session identifier, and if there is none, stop and ask a human rather than guessing. The losing agent must stop before implementation, explain the conflict naturally, and restore the winner as assignee when the connector permits it. If ownership cannot be restored safely, leave the issue unchanged, report the conflict, and select no overlapping work.

A same-account collision cannot be undone by reassignment, because the assignee is already correct for both sessions. The losing session resolves it by leaving the write set alone and saying so in a comment, not by changing anything in Linear.

Example:

```markdown
Ich übernehme SUD-46 und kümmere mich zuerst um das Runbook und die nicht-produktiven Nachweise. Ich arbeite auf `sudo-ai/sud-46-runbook`; `frontend/**` und Produktivläufe bleiben außen vor.

Linear und `origin/main@e870e0b` sind frisch abgeglichen. Sobald die bestehenden Nachweise sauber geprüft sind, melde ich mich mit dem Teststand.

— Session `sud-46-runbook-a41f`
```

Complete the claim only after the final read confirms ownership.

## Work without colliding

- Use a separate branch and worktree per code issue when repository rules permit. Include the Linear issue identifier in the branch name when no stricter convention exists.
- Run a coordination refresh before every material implementation slice. Planning does not authorize the next modifying step when the snapshot has expired.
- Stay within the claimed scope and write set. Before expanding either, complete a refresh, confirm no overlap, and explain the expansion in a concise status comment.
- Complete another refresh immediately before changing a shared schema, dependency manifest, release configuration, migration, deployment target, or cross-cutting interface.
- Represent real dependencies with Linear blocking relations when supported, and name the related issue IDs in the comment.
- Add a concise status comment after a material checkpoint, before a risky or cross-cutting step, when the plan or write set changes, and at the end of every autonomous run or user turn. During uninterrupted long work, publish an update at least every 45 minutes only when it contains actual progress. Keep the exact coordination watermark internal unless another agent needs it to assess freshness. Do not post empty heartbeat comments.
- Mention another agent's Linear display name when a decision, handoff, or conflict needs that agent's attention.
- Never place credentials, tokens, customer secrets, or sensitive logs in Linear. Link to an authorized secret-safe evidence location instead.

Example:

```markdown
Backendvertrag und Migration sind fertig. 326 Tests, Compile und OpenAPI sind grün. Ich warte noch auf den unabhängigen Review; danach kann der PR raus. `frontend/**` und die Produktivkonfiguration habe ich nicht angefasst.
```

## Surface findings outside the claimed scope

Treat a credible defect, regression, operational risk, or security concern found outside the claimed write set as a handoff obligation. Verify enough evidence to make the finding actionable, search Linear and the repository tracker for an existing record, and preserve the current work boundary. Do not silently fix the finding or fold it into the current issue.

Choose the narrowest useful record based on sensitivity and ownership:

- Use the repository's GitHub, Gitea, or equivalent issue tracker for a non-sensitive defect that belongs to that repository and is safe for everyone with repository visibility. Follow its issue template and link the relevant code, test, commit, or PR without copying secrets or customer data.
- Use a comment on the current Linear issue when the finding directly affects the current work and needs no independent owner. Create or link a separate Linear issue when it needs its own owner, priority, dependency, or cross-project decision.
- Treat suspected vulnerabilities, exploit paths, credentials, customer or employee data, and internal infrastructure details as sensitive. Use the project's private Linear issue or an established private security-reporting channel with the smallest necessary audience. Never place the sensitive details in a public issue; a public placeholder may only state that a private report exists when project policy requires one.
- Mention the responsible colleague or agent only when action or a decision is needed. Do not assign another account without an accepted handoff or project-lead direction. If the finding is already assigned to the authenticated agent, feed it back through the normal priority, dependency, claim, and refresh rules rather than fixing it opportunistically.

Create or update an external tracker record only when the resolved autonomy level and project rules permit that channel. At A0, report in Linear or provide a ready-to-post draft instead of writing to the repository tracker. If no safe writable channel is available, keep sensitive details out of public systems, tell the user where reporting stopped, and retain a concise private handoff.

For every scheduled wake, autonomous loop, or resumed run, inspect Linear work assigned to `me` and repository issues assigned to the independently resolved repository account before choosing the next task. Also inspect new mentions, accepted handoffs, and issues linked to the agent's active PRs or declared write set. Reconcile duplicate records with links; do not create parallel reports for the same finding.

Complete the handoff only when every confirmed relevant finding is linked to an existing record, recorded in the appropriate authorized channel, or explicitly reported to the user as awaiting a safe channel. Preserve uncertainty in the record instead of presenting an unverified suspicion as a confirmed bug.

## Handle blockers, release, and handoff explicitly

When blocked, explain the condition and the safe stopping point in ordinary prose.

```markdown
Ich hänge gerade an SUD-49: SUD-49 und SUD-50 ändern beide `frontend/src/types/index.ts`, und der Backendvertrag steht noch nicht fest. Mein Stand ist auf `claudia/sud-49-business-hours-ui` gesichert; die überlappenden Typen lasse ich bis zur Entscheidung in Ruhe.

@axel, gib mir bitte kurz Bescheid, ob der Vertrag in PR #32 so bleibt. An den unabhängigen UI-Texten kann ich währenddessen weiterarbeiten.
```

Keep the issue assigned to the current agent only while that agent remains accountable and intends to resume. If relinquishing ownership, first leave a natural comment containing the release facts listed above, then unassign. Do not assign a target agent until that account has accepted the handoff or the user/project lead has directed the reassignment.

For an accepted transfer, post a concise handoff with the same state and evidence, mention the receiving account, then reassign the issue to that exact Linear user. The receiving agent must independently resolve `me`, refresh the issue, verify the assignee ID, and leave a new ownership comment before continuing.

```markdown
@claudia, du kannst hier weitermachen. Mein Stand liegt in `834e99e` auf `sudo-ai/sud-50-email-business-hours`; lokal ist alles sauber. 333 Tests, Compile und OpenAPI sind grün.

Offen ist nur noch die Anbindung der vier Felder im Frontend. Zieh vorher bitte PR #32 und achte darauf, dass manuelle Läufe außerhalb des Fensters möglich bleiben.
```

## Finish and release the coordination state

1. Complete a final coordination refresh of the issue, assigned repository issues, autonomy policy, production classification, changed project activity, active claims, and relevant Git remote state before integration, deployment, or completion.
2. Verify every acceptance criterion and run the checks appropriate to the changed scope. For anything with a runtime effect, exercise the running result at least once end to end — a passing suite is not the same evidence. Green tests and healthy containers have both been observed while the service was in fact broken, because each test covered its own layer and none started the assembled system from the outside.
3. Post a natural completion comment with concrete evidence.
4. Move the issue to the project's completed state only when the work is actually complete and the project's review rules allow the transition. Otherwise move it only to the correct review state. When the team has a human acceptance state, completion is that state and not the terminal one — an agent does not mark its own work accepted.
5. Keep the completed issue assigned to the implementing account unless the project convention requires another final owner.
6. Publish a project-level status update only when this result changes project health, milestone readiness, priority, or cross-issue coordination.

Example:

```markdown
Das ist drin: PR #32 ist auf `main`. Die Bürozeiten werden jetzt gespeichert und DST-sicher ausgewertet. Automatische Läufe warten auf das Fenster, manuelle Läufe bleiben jederzeit möglich. 333 Tests, Compile und OpenAPI sind grün.

Für das Frontend bleibt nur SUD-49. Produktiv ist weiterhin nichts aktiviert oder gelaufen.
```

Complete the work session only when Linear shows the correct assignee and state, the latest comment exposes the true delivery state, assigned repository issues are reconciled, every confirmed out-of-scope finding has a safe handoff state, and no claimed write surface is left ambiguous.

## Avoid these connector pitfalls

These cost real rework in practice:

- **A project comment needs `projectId`, not `issueId`.** `save_comment` with `issueId: "<project-uuid>"` fails with `Could not find referenced Issue` even though the UUID is valid. Pass exactly one parent field and pick the one matching the entity type.
- **Linear rewrites issue references in stored text.** A plain `SUD-80` in a description is saved as `<issue id="..." href="...">SUD-80</issue>`. Two consequences: (a) a later `save_issue` `patch` whose `old_string` contains an issue identifier will fail with `old_string not found` — choose surrounding text that excludes the reference, or re-fetch with `get_issue` and copy the literal stored form; (b) `patch` is all-or-nothing, so one bad operation discards the whole call.
- **Do not predict identifiers you have not created yet.** When writing a set of linked issues, referencing "SUD-77" before it exists produces wrong cross-links, since numbering depends on creation order. Either create the issues first and patch the references afterwards, or describe the dependency in words and add the identifier later.
- **`get_issue` hides blocking relations by default.** Both `get_issue` and `list_issues` omit them unless you pass `includeRelations: true` to `get_issue`. After a `save_issue` with `blockedBy`, re-read with that flag before reporting the dependency as verified — a plain `get_issue` looks identical whether the relation exists or not.

## Report the result to the user

Name the issues selected, skipped because another agent owns them, completed, blocked, released, or handed off. Include out-of-scope findings routed to repository or private records, the authenticated Linear display name used for the work, links or identifiers for evidence, and any decision still requiring a human. Do not claim autonomous coordination succeeded if identity, assignment, or activity verification was unavailable.
