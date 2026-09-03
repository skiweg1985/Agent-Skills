# Documentation Completion Checklist

Use this checklist for the affected documentation, not as a demand that every
repository contain every document type.

## Impact and scope

- [ ] Every user-visible, operational, architectural, security, API, or
  configuration impact of the change is updated or explicitly absent.
- [ ] The work stays within the affected topic; a repository-wide
  reorganization occurs only as a dedicated documentation task.
- [ ] Existing repository language, terminology, filenames, and style are
  respected.

## Accuracy and usefulness

- [ ] Touched claims match the current implementation and supported workflow.
- [ ] Commands and examples are copyable and verified where practical.
- [ ] Links, anchors, and referenced filenames resolve.
- [ ] Each retained page enables an action or explains a durable decision.
- [ ] Diagrams, screenshots, tables, and callouts are present only when they
  materially improve understanding or verification.

## Authority and consolidation

- [ ] The affected topic has one clear authoritative source.
- [ ] Generated contracts, schemas, `--help`, code, tests, and releases own the
  detailed facts they can express reliably.
- [ ] Unique useful content is preserved before redundant or obsolete prose is
  removed.
- [ ] Other pages link to the authoritative explanation instead of restating
  it.

## Decisions and maintenance

- [ ] ADRs are limited to costly-to-reverse, security-sensitive, or fundamental
  architecture decisions.
- [ ] Routine implementation details remain in code, tests, configuration, or
  task documentation.
- [ ] The resulting documentation is smaller or no harder to maintain than the
  state it replaces.
