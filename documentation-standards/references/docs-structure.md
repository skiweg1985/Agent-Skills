# Documentation Structure, Architecture, and Decisions

Choose documents from reader needs and maintenance risk. The following is a
starting model for new projects, not a migration requirement for existing ones:

```text
README.md
OPERATIONS.md
ARCHITECTURE.md
SECURITY.md
TROUBLESHOOTING.md
docs/
|-- decisions/
`-- reference/
```

## Selection guide

| Document | Create or retain when... |
|---|---|
| `README.md` | Readers need orientation and a first supported action. |
| `OPERATIONS.md` | The project is installed, updated, backed up, restored, recovered, or diagnosed as a running system. |
| `ARCHITECTURE.md` | Components, dependencies, data flows, responsibilities, or hard system rules are not obvious from one entry point. |
| `SECURITY.md` | Credentials, roles, certificates, exposure, or trust boundaries require deliberate handling. |
| `TROUBLESHOOTING.md` | Realistic or recurring failures have diagnostic and recovery steps worth preserving. |
| `docs/decisions/` | A durable decision is costly to reverse or security-sensitive. |
| `docs/reference/` | Detailed lookup material is useful and preferably generated. |

Respect established filenames and locations. Consolidate overlapping material
within the affected topic rather than creating a parallel structure.

## Architecture overview

An architecture overview should provide only the context needed to reason about
the system:

- one diagram showing the important components and boundaries;
- the responsibility owned by each component;
- the important data, control, and network flows;
- external dependencies and trust boundaries;
- hard system rules and meaningful failure or recovery behavior.

Document a component separately only when it has an independent operational
lifecycle, public extension contract, or non-obvious responsibility. Explain an
interface boundary once in the architecture or operations entry point, then
link to it instead of restating it in several forms.

Use a Mermaid flow or sequence diagram when relationships are harder to follow
in prose. Keep the diagram at the same abstraction level as the surrounding
text and omit implementation details that change routinely.

## Architecture Decision Records

Create an ADR when future maintainers will need the reasoning because changing
the decision would be expensive, risky, or security-sensitive. Typical cases
include:

- runtime, broker, protocol, persistence, or deployment model;
- bootstrap, management, and recovery channels;
- trust boundaries, credential custody, or signed update mechanisms;
- a deliberate constraint whose alternatives and consequences matter later.

Routine implementation choices are not ADRs. Keep filenames, function or class
boundaries, reversible configuration, ordinary dependency updates, and UI
details in code, tests, configuration, or the relevant task documentation.

Use the repository's existing ADR format. For a new repository, a compact ADR
contains:

- **Context:** the forces and constraints that made a decision necessary.
- **Decision:** the selected approach and its boundary.
- **Alternatives:** credible options considered.
- **Consequences:** benefits, costs, risks, and operational effects.
- **Revisit when:** a concrete condition that would justify reconsideration.

Prefer descriptive filenames in `docs/decisions/`; add sequence numbers only
when the repository already uses them or ordering materially helps navigation.
