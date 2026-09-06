#!/usr/bin/env python3
"""Measure how a wave delivered, so a coordination rule can be checked.

Four numbers, one line per wave. Each one exists because a rule claims to move
it; a rule whose number never moves is a candidate for removal rather than a
permanent cost.

    cycle_time_hours       pull request opened -> merged, median
    review_rounds          published review contributions per pull request
    issues_per_merged_pr   tracker issues created per merged pull request
    surface_screenshot     share of user-interface pull requests with a screenshot

The first two come from the repository host and always work. The last two need
a tracker; without one they are reported as unavailable with the reason, because
a gap in the series is worse than an incomplete row.

Requires the GitHub CLI, authenticated for the repository. Tracker access is
optional and read from LINEAR_API_KEY in the environment; no credential is ever
written to the output.

Runs on Python 3.10.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# A review verdict cannot be read from GitHub's `reviewDecision` when every
# agent pushes through one account: an author may not formally approve or
# request changes on their own pull request, so the field stays null and the
# verdict lives in the prose. Measured across 65 merged pull requests, all 65
# reported null while five carried a rejection in the text.
REJECTION_PATTERNS = re.compile(
    r"CHANGES\s+REQUESTED|Änderungen\s+verlangt|verlangt\s+Änderungen|REQUEST\s+CHANGES",
    re.IGNORECASE,
)

# A screenshot is a markdown image or an upload link from either host.
SCREENSHOT_PATTERNS = re.compile(
    r"!\[[^\]]*\]\([^)]+\)"
    r"|user-images\.githubusercontent\.com"
    r"|github\.com/user-attachments"
    r"|uploads\.linear\.app",
    re.IGNORECASE,
)

LINEAR_API = "https://api.linear.app/graphql"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_day(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def hours_between(start: str, end: str) -> float:
    return (parse_time(end) - parse_time(start)).total_seconds() / 3600


def share(count: int, total: int) -> float | None:
    return round(count / total, 3) if total else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 2) if values else None


def fetch_pull_requests(repo: str, limit: int) -> list[dict[str, Any]]:
    """Merged pull requests with the fields the metrics need."""
    fields = "number,title,createdAt,mergedAt,reviews,body,files"
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", repo, "--state", "merged",
             "--limit", str(limit), "--json", fields],
            capture_output=True, text=True, check=False,
        )
    except FileNotFoundError:
        # The coordinator host has no GitHub CLI. Reachability is not
        # capability: run this where the repository work happens.
        raise SystemExit(
            "the GitHub CLI is not on PATH; run this on a host that has it, "
            "authenticated for the repository"
        ) from None
    if result.returncode != 0:
        raise SystemExit(f"gh pr list failed for {repo}: {result.stderr.strip()[:400]}")
    return json.loads(result.stdout or "[]")


def in_window(value: str | None, since: datetime, until: datetime | None) -> bool:
    if not value:
        return False
    moment = parse_time(value)
    if moment < since:
        return False
    return until is None or moment <= until


def touches_surface(pull_request: dict[str, Any], prefixes: tuple[str, ...]) -> bool:
    return any(
        (path or "").startswith(prefixes)
        for path in (f.get("path", "") for f in pull_request.get("files") or [])
    )


def has_screenshot(pull_request: dict[str, Any]) -> bool:
    text = pull_request.get("body") or ""
    for review in pull_request.get("reviews") or []:
        text += "\n" + (review.get("body") or "")
    return bool(SCREENSHOT_PATTERNS.search(text))


def repository_metrics(
    pull_requests: list[dict[str, Any]],
    since: datetime,
    until: datetime | None,
    surface_prefixes: tuple[str, ...],
) -> dict[str, Any]:
    merged = [p for p in pull_requests if in_window(p.get("mergedAt"), since, until)]
    cycle = [hours_between(p["createdAt"], p["mergedAt"]) for p in merged]
    rounds = [len(p.get("reviews") or []) for p in merged]
    rejected = sum(
        1
        for p in merged
        if any(REJECTION_PATTERNS.search(r.get("body") or "") for r in p.get("reviews") or [])
    )
    surface = [p for p in merged if touches_surface(p, surface_prefixes)]
    with_shot = sum(1 for p in surface if has_screenshot(p))

    return {
        "merged_pull_requests": len(merged),
        "cycle_time_hours": {
            "median": median(cycle),
            "max": round(max(cycle), 2) if cycle else None,
            "sample": len(cycle),
        },
        "review_rounds": {
            "median": median([float(r) for r in rounds]),
            "share_two_or_more": share(sum(1 for r in rounds if r >= 2), len(rounds)),
            "share_rejected_in_text": share(rejected, len(merged)),
            "sample": len(rounds),
        },
        "surface_screenshot": {
            "share": share(with_shot, len(surface)),
            "with_screenshot": with_shot,
            "sample": len(surface),
        },
    }


def linear_issue_count(project: str, since: datetime, until: datetime | None) -> int:
    """Issues created in the window, counted through the tracker API."""
    key = os.environ.get("LINEAR_API_KEY")
    if not key:
        raise LookupError("LINEAR_API_KEY is not set")
    query = """
    query($filter: IssueFilter!) {
      issues(filter: $filter, first: 250) { nodes { id createdAt } }
    }
    """
    created = {"gte": since.isoformat()}
    if until is not None:
        created["lte"] = until.isoformat()
    variables = {"filter": {"project": {"name": {"eq": project}}, "createdAt": created}}
    request = urllib.request.Request(
        LINEAR_API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError) as error:
        raise LookupError(f"tracker unreachable: {type(error).__name__}") from error
    if payload.get("errors"):
        raise LookupError("tracker rejected the query")
    return len(payload["data"]["issues"]["nodes"])


def build_row(args: argparse.Namespace) -> dict[str, Any]:
    since = parse_day(args.since)
    until = parse_day(args.until) if args.until else None
    prefixes = tuple(p.strip() for p in args.surface_paths.split(",") if p.strip())

    metrics = repository_metrics(
        fetch_pull_requests(args.repo, args.limit), since, until, prefixes
    )

    unavailable = []
    issues_created: int | None = None
    if args.tracker_project:
        try:
            issues_created = linear_issue_count(args.tracker_project, since, until)
        except LookupError as error:
            unavailable.append(f"issues_per_merged_pr: {error}")
    else:
        unavailable.append("issues_per_merged_pr: no tracker project given")

    merged = metrics["merged_pull_requests"]
    metrics["issues_per_merged_pr"] = {
        "value": round(issues_created / merged, 2) if issues_created and merged else None,
        "issues_created": issues_created,
        "sample": merged,
    }

    row: dict[str, Any] = {
        "measured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "label": args.label,
        "repository": args.repo,
        "tracker_project": args.tracker_project,
        "window": {"since": args.since, "until": args.until},
        "metrics": metrics,
        "collection": "script",
    }
    if unavailable:
        row["unavailable"] = unavailable
    return row


def render_table(row: dict[str, Any]) -> str:
    m = row["metrics"]
    lines = [
        f"Window        {row['window']['since']} .. {row['window']['until'] or 'now'}",
        f"Repository    {row['repository']}",
        f"Merged PRs    {m['merged_pull_requests']}",
        "",
        f"Cycle time    median {m['cycle_time_hours']['median']} h, "
        f"max {m['cycle_time_hours']['max']} h (n={m['cycle_time_hours']['sample']})",
        f"Review rounds median {m['review_rounds']['median']}, "
        f"two or more {m['review_rounds']['share_two_or_more']}, "
        f"rejected in text {m['review_rounds']['share_rejected_in_text']} "
        f"(n={m['review_rounds']['sample']})",
        f"Surface shots {m['surface_screenshot']['share']} "
        f"({m['surface_screenshot']['with_screenshot']}/{m['surface_screenshot']['sample']})",
        f"Issues per PR {m['issues_per_merged_pr']['value']} "
        f"(created {m['issues_per_merged_pr']['issues_created']})",
    ]
    for note in row.get("unavailable", []):
        lines.append(f"unavailable   {note}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", required=True, help="owner/name of the repository")
    parser.add_argument("--since", required=True, help="window start, YYYY-MM-DD")
    parser.add_argument("--until", help="window end, YYYY-MM-DD; open when omitted")
    parser.add_argument("--tracker-project", help="tracker project name for issue counts")
    parser.add_argument("--label", default="", help="wave label recorded in the row")
    parser.add_argument("--limit", type=int, default=200, help="pull requests to inspect")
    parser.add_argument(
        "--surface-paths",
        default="frontend/",
        help="comma-separated path prefixes that count as a user interface",
    )
    parser.add_argument("--json-only", action="store_true", help="print the row only")
    args = parser.parse_args()

    row = build_row(args)
    if not args.json_only:
        print(render_table(row), file=sys.stderr)
    print(json.dumps(row, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
