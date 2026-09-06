# Delivery measurements

One row per wave. Each number exists because a coordination rule claims to move
it, so a rule can be checked instead of only believed — and a rule whose number
never moves becomes a candidate for removal rather than a permanent cost that
every future project pays in context and compliance.

This is one series, not one per skill. The rules being measured live in both
`linear-coordinate-agents` and `remote-agent-orchestrator`, but the numbers come
from one wave and would drift apart if they were written down twice.

## Which number checks which rule

| Number | Rule it checks |
| -- | -- |
| `cycle_time_hours.median` | the four blocking classes; one review round as the default; merging without a second reviewer at A3 |
| `review_rounds.share_two_or_more` | one review round as the default |
| `review_rounds.share_rejected_in_text` | the four blocking classes |
| `surface_screenshot.share` | an issue names its design; the running application is the evidence |
| `issues_per_merged_pr` | one collector record per wave |

## When each rule is decided

The six rules of 2026-09-06 are due for a decision once two further waves have
been measured against the baseline below. For each one: keep, sharpen, or remove.
A number that has not moved makes its rule a removal candidate, and keeping it
then needs a stated reason next to the rule itself. Security and correctness are
exempt from this test; see
[the rule lifecycle decision](../../../docs/decisions/rules-carry-a-number.md).

## How a new row is made

Run the collector on a host that has the GitHub CLI, then append the section it
prints. Cut the window at the moment a rule landed, not at midnight: a rule that
merges at noon splits its own day, and a day-granular window mixes the wave
before it with the wave after.

```sh
python3 ../scripts/delivery_metrics.py \
  --repo <owner>/<name> --since <ISO> --until <ISO> --label <wave>
```

When a source is unavailable, the row still goes in with the reason recorded. A
gap in the series is worse than an incomplete row: a missing row looks like a
wave that never happened.

## Reading the first two rows

The two rows below are both from before the rules of 2026-09-06, and only the
second one is a fair baseline.

In the first window almost no review happened at all — no round, no rejection,
a median of five minutes. That is not a fast process; it is an absent one. It is
recorded as context so that nobody later reads the arrival of reviewing as a
regression caused by the rules.

The second window is the review regime as it actually ran, up to the moment the
rules merged. **That is the baseline the six rules must be measured against.**

---

### 2026-09-01 .. 2026-09-05 — before the review regime

Context only. Reviewing had not started; treat these numbers as the floor of an
absent process rather than as a target.

- 34 merged pull requests, cycle time median 0.09 h
- review rounds median 0.0, two or more 0 %, rejected in text 0 %
- interface pull requests with a screenshot: 0 of 20

```json
{"collection": "script", "label": "vor-review-regime", "measured_at": "2026-09-06T15:10:00+00:00", "metrics": {"cycle_time_hours": {"max": 18.96, "median": 0.09, "sample": 34}, "issues_per_merged_pr": {"issues_created": null, "sample": 34, "value": null}, "merged_pull_requests": 34, "review_rounds": {"median": 0.0, "sample": 34, "share_rejected_in_text": 0.0, "share_two_or_more": 0.0}, "surface_screenshot": {"sample": 20, "share": 0.0, "with_screenshot": 0}}, "repository": "skiweg1985/operations-monitor", "tracker_project": null, "unavailable": ["issues_per_merged_pr: no tracker project given"], "window": {"since": "2026-09-01", "until": "2026-09-05"}}
```

### 2026-09-05 .. 2026-09-06T12:37Z — review regime, before the rules

**The baseline.** The independent-review regime was in force; the six rules were
not yet merged.

- 30 merged pull requests, cycle time median 0.61 h
- review rounds median 1.0, two or more 20 %, rejected in text 16.7 %
- interface pull requests with a screenshot: 0 of 10

```json
{"collection": "script", "label": "review-regime-vor-den-regeln", "measured_at": "2026-09-06T15:10:00+00:00", "metrics": {"cycle_time_hours": {"max": 22.67, "median": 0.61, "sample": 30}, "issues_per_merged_pr": {"issues_created": null, "sample": 30, "value": null}, "merged_pull_requests": 30, "review_rounds": {"median": 1.0, "sample": 30, "share_rejected_in_text": 0.167, "share_two_or_more": 0.2}, "surface_screenshot": {"sample": 10, "share": 0.0, "with_screenshot": 0}}, "repository": "skiweg1985/operations-monitor", "tracker_project": null, "unavailable": ["issues_per_merged_pr: no tracker project given"], "window": {"since": "2026-09-05", "until": "2026-09-06T12:37:00Z"}}
```

### 2026-09-06, counted by hand — the observations behind the rules

Not produced by the collector. These are the numbers that led to the six rules
and are kept because two of them cannot be derived from the repository host
alone.

- one merge took 97 minutes from claim to merge, of which 15 minutes were
  implementation; its last blocking finding was the language of the pull request
  title
- six pull requests with green checks sat 21 hours without a single review
  contribution
- 29 of 38 issues created after the initial plan were process, review findings
  or hardening rather than product
- four separate records existed to collect non-blocking findings, one per pull
  request

```json
{"collection": "manual", "label": "beobachtungen-hinter-den-regeln", "measured_at": "2026-09-06T12:00:00+00:00", "metrics": {"claim_to_merge_minutes_worst": 97, "implementation_share_of_worst": 0.15, "hours_unreviewed_worst": 21, "process_issue_share": 0.76, "collector_records": 4}, "repository": "skiweg1985/operations-monitor", "tracker_project": "Operations Monitor", "window": {"since": "2026-09-02", "until": "2026-09-06T12:37:00Z"}}
```
