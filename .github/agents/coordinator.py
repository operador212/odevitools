#!/usr/bin/env python3
"""Deterministic ODEVI+ agent coordinator. Aggregates evidence; never edits production."""
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime, timezone

REPORTS = {
    "site": Path("odevi-audit-report.md"),
    "browser": Path("odevi-browser-report.md"),
}
findings = []
evidence = {}
for agent, path in REPORTS.items():
    if not path.exists():
        evidence[agent] = {"status": "missing", "path": str(path)}
        findings.append({"agent": agent, "severity": "high", "code": "REPORT_MISSING",
                         "message": f"Expected report missing: {path}"})
        continue
    content = path.read_text(encoding="utf-8", errors="replace")
    evidence[agent] = {"status": "present", "path": str(path)}
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            findings.append({"agent": agent, "severity": "high", "code": "CHECK_FAILED",
                             "message": stripped[5:].strip()})
        elif "Findings: " in stripped:
            try:
                evidence[agent]["finding_count"] = int(stripped.rsplit(" ", 1)[-1])
            except ValueError:
                pass

status = "blocked" if findings else "passed"
result = {
    "schema_version": 1,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "release_allowed": not findings,
    "findings_count": len(findings),
    "evidence": evidence,
    "findings": findings,
    "policy": {
        "auto_merge": False,
        "production_secrets_in_pr_jobs": False,
        "ai_repair_enabled": bool(os.getenv("OPENAI_API_KEY")),
        "note": "AI repair remains disabled until the isolated repair worker and budget controls are reviewed."
    },
}
Path("odevi-agent-coordination.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
lines = ["# ODEVI+ Agent Coordination", "", f"- Status: **{status.upper()}**",
         f"- Release allowed: **{'yes' if result['release_allowed'] else 'no'}**",
         f"- Findings: **{len(findings)}**", "",
         "## Evidence"]
for name, item in evidence.items():
    lines.append(f"- {name}: {item['status']}" + (f" ({item.get('finding_count', 0)} findings)" if "finding_count" in item else ""))
lines += ["", "## Findings"]
lines += [f"- [{x['severity'].upper()}] {x['agent']} / {x['code']}: {x['message']}" for x in findings] or ["- None."]
lines += ["", "AI repair is not enabled by this coordinator. It only aggregates evidence and fails closed."]
Path("odevi-agent-coordination.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
if findings:
    raise SystemExit(1)
