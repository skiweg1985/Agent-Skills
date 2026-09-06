# A rule carries a number and can be removed

## Context

Skills in this repository already record why a rule exists. Rules carry their
founding evidence in the prose — "measured across seven open pull requests from
one wave, five carried it and two did not" — so a reader sees what a rule rests
on without leaving the file.

Nothing records whether a rule then worked. Every rule enters with evidence and
none ever leaves, which has two costs.

The first is size. `remote-agent-orchestrator` is around 600 lines and
`linear-coordinate-agents` around 500. A supervisor tick loads four skills, and
every rule in them is read on every run. Growth is not free: it costs context on
each invocation and it dilutes the rules that matter.

The second is that a rule which turns out to be wrong survives. One project
observed on 2026-09-06 shows the shape. A rule requiring pull request metadata
in the reader's language was created at 08:02 and merged at 08:04. At 08:25 it
blocked a pull request that had been opened at 07:25, before the rule existed.
The correction took 40 minutes and changed nothing about the product. Nobody
would have questioned that rule later, because there was no moment at which a
rule is questioned.

## Decision

A behavioural rule names the number it should move, that number's current value,
and when it will be re-checked. A rule whose number has not moved across two
measured waves is a removal candidate: it is removed or sharpened, and keeping
it needs a stated reason. Removal needs the evidence that introduction needed
and is recorded here, with supersession, like any other decision.

Security and correctness are exempt. A rule that prevents a credential leak or a
wrong result does not have to prove throughput, and demanding a number there
would be a way of arguing such rules away.

Anything else that cannot name a number is an opinion. It may be written down as
guidance, but it does not become a rule.

The numbers live in
[the delivery measurements](../../skills/linear-coordinate-agents/references/delivery-measurements.md),
one series rather than one per skill, because the rules being measured sit in
several skills while the numbers come from one wave.

## Alternatives considered

**Leave it as it is and rely on judgement.** This is what produced the situation
above. Judgement did notice the problem eventually, but only because somebody
looked at five days of history by hand, and only after the cost had been paid
several times.

**Review the whole rule set periodically.** A recurring review of everything
competes with product work and is the first thing dropped. Attaching the check
to the rule itself means the reader of a rule sees whether its check is overdue,
with no separate ceremony to keep alive.

**Expire rules automatically after a fixed time.** Simple, and wrong for the
rules that matter most: a security rule would lapse precisely because nothing
went wrong while it was in force. The exemption for security and correctness
exists for the same reason.

**Measure everything.** The failure being corrected here is an apparatus that
generates its own work. A measurement apparatus can repeat it. Four numbers, one
row per wave, is deliberately close to the minimum that can still falsify a
rule.

## Consequences

A rule now needs a measurable claim before it is written, which is a real bar
and will stop some proposals. That is the intent.

The series needs to keep being written, otherwise the removal condition can
never be evaluated and the rules quietly become permanent again. Writing the row
is therefore part of closing a wave rather than a separate good intention.

The six rules introduced on 2026-09-06 are the first subject. Their baseline is
recorded; the decision on each of them is due once two further waves have been
measured.
