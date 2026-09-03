# README Guide

The root README is the repository's front door. It should orient the intended
reader and lead to a useful first action without becoming the complete manual.

## Questions the README answers

- What does this project do, for whom, and why does it exist?
- What does the deployed or operating system look like at a glance?
- What is the shortest safe path to a first useful result?
- Where should users, operators, and contributors go next?

## Adaptive structure

Use only the sections that answer those questions. A useful starting shape is:

```markdown
# Project name

One or two sentences describing the purpose and intended audience.

## Quick start

The shortest supported path to a useful result.

## How it works

A compact operating picture or architecture sketch when needed.

## Next steps

Links organized by reader task or role.
```

Add installation, configuration, usage, development, contributing, or license
sections only when they are the reader's next action and remain concise. Move
operational procedures, architecture detail, security guidance, recurring
incident handling, and generated reference to their authoritative documents.

## Task-oriented navigation

Prefer links such as:

| I want to... | Go to... |
|---|---|
| Install or upgrade the service | Operations guide |
| Understand components and data flow | Architecture overview |
| Configure authentication or certificates | Security guide |
| Diagnose a known failure | Troubleshooting guide |
| Look up exact API or CLI details | Generated reference |

Use the repository's real filenames and omit rows that do not apply.

## Presentation

- Follow the repository's existing heading and language conventions.
- Use copyable commands and show expected results when they help readers verify
  success.
- Add one diagram when it explains the operating picture faster than prose.
- Use badges only when they communicate maintained, actionable status.
- Use emojis only when they are already part of the repository's style.
- Keep feature lists short and user-oriented; release history belongs in
  releases or a changelog when the project maintains one.
