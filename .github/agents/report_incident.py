#!/usr/bin/env python3
"""Create/update one deduplicated GitHub incident for automated QA failures."""
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

token = os.getenv("GITHUB_TOKEN")
repo = os.getenv("GITHUB_REPOSITORY")
report = Path("odevi-browser-report.md")
if not token or not repo or not report.exists():
    print("Incident reporting skipped: token, repository, or report unavailable.")
    raise SystemExit(0)
body = report.read_text(encoding="utf-8")
if "- [ ] " not in body:
    print("No browser QA findings; no incident created.")
    raise SystemExit(0)

api = f"https://api.github.com/repos/{repo}/issues"
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
def request(url, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode())

try:
    open_issues = request(api + "?state=open&per_page=100")
    existing = next((item for item in open_issues if item.get("title") == "[Agent] ODEVI+ browser QA needs attention"), None)
    issue_body = (
        "## Automated diagnosis\n\n"
        "The ODEVI+ browser QA agent detected production-site failures. "
        "The workflow is intentionally not allowed to modify production files or merge code.\n\n"
        "### Evidence\n\n" + body +
        "\n\n### Required agent response\n"
        "1. Reproduce each finding.\n"
        "2. Identify the smallest safe correction.\n"
        "3. Implement it on an isolated branch and open a pull request.\n"
        "4. Run the full QA suite before proposing deployment.\n"
    )
    if existing:
        request(existing["url"], "PATCH", {"body": issue_body})
        print(f"Updated incident #{existing['number']}")
    else:
        created = request(api, "POST", {"title": "[Agent] ODEVI+ browser QA needs attention", "body": issue_body})
        print(f"Created incident #{created['number']}: {created['html_url']}")
except urllib.error.HTTPError as exc:
    print(f"Could not publish QA incident: HTTP {exc.code}: {exc.read().decode()[:500]}")
    raise SystemExit(0)
