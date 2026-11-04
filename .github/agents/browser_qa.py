#!/usr/bin/env python3
"""Public-site browser QA for ODEVI+. Fails closed and writes a human-readable report."""
from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas
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

def make_uber_pdf_fixture():
    """Create a synthetic, non-personal Uber-style PDF to exercise the real PDF.js upload path."""
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=(612, 792))
    lines = [
        "Uber", "01-31 Outubro 2026", "Resumo fiscal",
        "Ganhos totais", "£ 1.825,65",
        "Valores extras", "£ 73,47",
        "Total de despesas", "£ 0,00",
        "Valor liquido de repasse", "£ 1.825,65",
    ]
    y = 740
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 32
    pdf.save()
    return output.getvalue()

with sync_playwright() as p:
    browser = p.chromium.launch()
    for width, height, label in [(390, 844, "mobile"), (1365, 900, "desktop")]:
        page = browser.new_page(viewport={"width": width, "height": height})
        page.on("pageerror", lambda error, current=page: findings.append(
            f"JavaScript error ({label}, {current.url}): {error} | stack: {getattr(error, 'stack', '')}"
        ))
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
            try:
                page.goto(BASE + "/tax-assistant-demo.html", wait_until="domcontentloaded", timeout=45000)
                page.locator("#file").set_input_files({
                    "name": "odevi-qa-sample.csv",
                    "mimeType": "text/csv",
                    "buffer": b"date,description,amount,currency\n2026-11-01,Delivery payout,125.50,GBP\n2026-11-02,Fuel,-18.20,GBP\n",
                })
                page.locator("#results").wait_for(state="visible", timeout=10000)
                checks += 1
                if "2 transações reconhecidas" not in page.locator("#count").inner_text():
                    findings.append("Free Tax Assistant demo: CSV upload did not render the expected 2 transactions")
            except Exception as exc:
                findings.append(f"Free Tax Assistant demo CSV upload failed: {exc}")
            try:
                page.goto(BASE + "/tax-assistant-demo.html", wait_until="domcontentloaded", timeout=45000)
                page.wait_for_function("!!window.pdfjsLib", timeout=15000)
                page.locator("#file").set_input_files({
                    "name": "odevi-qa-uber-sample.pdf",
                    "mimeType": "application/pdf",
                    "buffer": make_uber_pdf_fixture(),
                })
                page.locator("#pdfResults").wait_for(state="visible", timeout=15000)
                row = page.locator("#pdfRows").inner_text()
                checks += 1
                for expected in ("Uber", "01-31 Outubro 2026", "£1,825.65", "£73.47"):
                    if expected not in row:
                        findings.append(f"Free Tax Assistant demo: PDF extraction missing expected value: {expected}; got: {row}")
            except Exception as exc:
                findings.append(f"Free Tax Assistant demo PDF upload failed: {exc}")
    browser.close()

report = ["# ODEVI+ browser QA", "", f"- Checks: {checks}", f"- Findings: {len(findings)}", ""]
report += [f"- [ ] {item}" for item in findings] if findings else ["- [x] All browser checks passed."]
Path("odevi-browser-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
print("\n".join(report))
raise SystemExit(1 if findings else 0)
