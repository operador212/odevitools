from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import sys, json

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ["index.html", "ferramentas.html", "sobre.html", "contacto.html", "privacidade.html", "tax-assistant.html", "curriculo-ingles-reino-unido.html"]
issues = []
checked = 0

class Auditor(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.source = source
    def handle_starttag(self, tag, attrs):
        global checked
        for key, value in attrs:
            if key not in ("href", "src") or not value:
                continue
            value = value.strip()
            if value.startswith("#") or value.startswith("//"):
                continue
            parts = urlsplit(value)
            if parts.scheme in ("http", "https", "mailto", "tel", "javascript", "data"):
                continue
            if not parts.path:
                continue
            target = (self.source.parent / parts.path).resolve()
            if not target.is_relative_to(ROOT.resolve()):
                issues.append(f"{self.source.relative_to(ROOT)}: path escapes repository: {value}")
                continue
            checked += 1
            if not target.exists():
                issues.append(f"{self.source.relative_to(ROOT)}: missing local path: {value}")

for name in REQUIRED:
    if not (ROOT / name).is_file():
        issues.append(f"Missing required page: {name}")

pages = sorted(ROOT.glob("*.html"))
for page in pages:
    try:
        parser = Auditor(page)
        parser.feed(page.read_text(encoding="utf-8"))
        parser.close()
    except Exception as exc:
        issues.append(f"Could not inspect {page.name}: {exc}")

report = ["# ODEVI+ automated audit", "", f"- HTML pages: {len(pages)}", f"- Local paths checked: {checked}", f"- Findings: {len(issues)}", ""]
report += [f"- [ ] {item}" for item in issues] if issues else ["- [x] No missing required pages or local paths."]
Path("odevi-audit-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
print(json.dumps({"pages": len(pages), "paths_checked": checked, "findings": issues}, ensure_ascii=False, indent=2))
if issues:
    sys.exit(1)
