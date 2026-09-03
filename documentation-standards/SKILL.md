---
name: documentation-standards
description: >-
  Keep software-repository documentation accurate, lean, and task-oriented.
  Use when creating or restructuring repository documentation, or when changes
  affect user-visible behavior, operations, architecture, security boundaries,
  or public interfaces such as APIs and configuration. Covers READMEs,
  runbooks, architecture and security documents, ADRs, references, and
  troubleshooting guides. Skip pure internal refactors with no documentation
  impact.
---

# Documentation Standards

Treat documentation as a small, reliable cockpit for the people who use,
operate, or extend the software. A page earns its maintenance cost when it
enables a concrete action or preserves a durable decision that would otherwise
be expensive to rediscover.

## Workflow

1. Inspect repository instructions, existing documentation, implementation,
   generated references, and established language and naming conventions.
2. Identify the affected audience and tasks. For an internal refactor with no
   behavior or interface impact, leave the documentation unchanged.
3. Choose the smallest set of authoritative documents that covers the change.
   Use the selection guide below rather than creating every possible page.
4. Update the affected topic and consolidate its duplicate or obsolete content.
   Preserve unique useful information before removing a redundant page. Treat a
   repository-wide reorganization as a separate documentation task.
5. Verify touched claims, commands, links, examples, and diagrams against the
   implementation or machine-readable source of truth.

The work is complete when every documentation impact of the change is either
updated or explicitly determined to be absent, and the affected topic has one
clear authoritative source.

## Core rules

**Follow the repository.** Use its established language, terminology, style,
and filenames. If it has no convention, write documentation in clear English.
Emojis, badges, tables, callouts, and diagrams are optional tools, not quality
requirements.

**Organize around tasks and roles.** Help readers find the next action: install,
configure, operate, observe, recover, troubleshoot, or extend. Prefer a short
task-oriented index over a tour of the directory tree.

**Keep one source of truth.** State a responsibility, constraint, or workflow
once in its authoritative location and link to it elsewhere. Prefer generated
or machine-readable references for details already owned by code, schemas, or
tools. See `references/topic-guides.md`.

**Explain durable reasons.** Architecture documentation explains boundaries,
data flows, responsibilities, and hard system rules. An ADR is reserved for a
decision that is costly to reverse, security-sensitive, or fundamental to the
runtime or deployment model. See `references/docs-structure.md`.

**Write for use.** Keep prose direct and scannable. Include examples, diagrams,
expected results, warnings, or screenshots only when they materially help a
reader complete or verify a task.

## Document selection

- A root `README.md` provides orientation and the first useful action.
- Operational software gets an operations guide for update, backup, restore,
  recovery, and diagnosis that actually apply to it.
- Non-obvious systems get an architecture overview with one useful diagram,
  data flows, responsibilities, and hard rules.
- Projects with credentials, roles, certificates, network trust, or other real
  trust boundaries get security documentation.
- Projects with realistic recurring incidents get troubleshooting guidance.
- Durable decisions go in the repository's existing ADR location; for a new
  repository, prefer `docs/decisions/`.
- Detailed reference material belongs in `docs/reference/` only when useful and
  should be generated whenever a machine-readable source exists.

Do not force these filenames onto an established repository. Adapt the model to
the existing structure and consolidate the affected topic in place.

## References

- Read `references/readme-template.md` before creating or substantially
  restructuring a README.
- Read `references/docs-structure.md` for architecture, system workflows,
  document selection, or ADR work.
- Read `references/topic-guides.md` for configuration, API, CLI, UI,
  observability, security, or operational documentation.
- Read `references/quality-checklist.md` before declaring documentation work
  complete.

## Golden rule

If a page neither enables an action nor explains a durable decision, move its
useful truth to code, tests, generated reference, or an authoritative document,
then remove the redundant prose.
