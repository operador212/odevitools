#!/usr/bin/env python3
"""Public-site browser QA for ODEVI+. Fails closed and writes a human-readable report."""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "https://odevitools.com"
PAGES = [
    "/", "/ferramentas.html", "/sobre.html", "/contacto.html",
    "/privacidade.html", "/tax-assistant.html",
    "/curriculo-ingles-reino-unido.html", "/documentos-verificacoes.html",
    "/guia-portugal.html", "/regularizacao.html", "/tax-assistant-demo.html",
]
findings = []
checks = 0

with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height, label in [(390, 844, "mobile"), (1365, 900, "desktop")]:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.on("pageerror", lambda error: findings.append(f"JavaScript error ({label}): {error}"))
        for path in PAGES:
            try:
                response = page.goto(BASE + path, wait_until="domcontentloaded", timeout=45000)
                checks += 1
                if response is None or response.status != 200:
                    findings.append(f"{label} {path}: expected HTTP 200, got {response.status if response else 'no response'}")
                    continue
                if not (page.title() or "").strip():
                    findings.append(f"{label} {path}: missing document title")
                if page.locator("body").count() != 1:
                    findings.append(f"{label} {path}: document body missing")
                overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 2")
                if overflow:
                    findings.append(f"{label} {path}: horizontal overflow at {width}px")
            except Exception as exc:
                findings.append(f"{label} {path}: navigation/test error: {exc}")
        if label == "desktop":
            try:
                page.goto(BASE + "/tax-assistant.html", wait_until="domcontentloaded", timeout=45000)
                page.locator("#pt").click()
                checks += 1
                if page.locator("#pt").get_attribute("aria-pressed") != "true":
                    findings.append("Tax Assistant: Portugal selector did not activate")
                page.locator("#uk").click()
                checks += 1
                if page.locator("#uk").get_attribute("aria-pressed") != "true":
                    findings.append("Tax Assistant: UK selector did not activate")
            except Exception as exc:
                findings.append(f"Tax Assistant selector interaction failed: {exc}")
    browser.close()

report = ["# ODEVI+ browser QA", "", f"- Checks: {checks}", f"- Findings: {len(findings)}", ""]
report += [f"- [ ] {item}" for item in findings] if findings else ["- [x] All browser checks passed."]
Path("odevi-browser-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
print("\n".join(report))
raise SystemExit(1 if findings else 0)
