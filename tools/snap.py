"""Evidence screenshot helper (Playwright, headless Chromium, 1440x900).

Usage:
    python tools/snap.py shot  <url> <out.png> [--full] [--wait-for CSS]
    python tools/snap.py sonar <url> <out.png> [--full] [--wait-for CSS]

`sonar` first logs into the local SonarQube (http://localhost:9000) with the
credentials in ~/.novacart_auth/sonar.txt (line 1 = user, line 2 = password).
Credentials are never stored inside the project.
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1440, "height": 900}
SONAR_BASE = "http://localhost:9000"
AUTH_FILE = os.path.join(os.path.expanduser("~"), ".novacart_auth", "sonar.txt")


def _read_sonar_creds():
    with open(AUTH_FILE, encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh.read().splitlines() if ln.strip()]
    return lines[0], lines[1]


def _sonar_login(page):
    user, pwd = _read_sonar_creds()
    page.goto(SONAR_BASE + "/sessions/new", wait_until="networkidle")
    page.fill("input#login", user)
    page.fill("input#password", pwd)
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    # Dismiss "what's new"/tour pop-ups if present.
    for sel in ("button:has-text('Got it')", "button:has-text('Dismiss')",
                "button[aria-label='Close']"):
        try:
            if page.locator(sel).first.is_visible(timeout=500):
                page.locator(sel).first.click()
        except Exception:
            pass


def capture(url, out, full=False, wait_for=None, sonar=False):
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        page = ctx.new_page()
        if sonar:
            _sonar_login(page)
        page.goto(url, wait_until="networkidle", timeout=60000)
        if wait_for:
            page.wait_for_selector(wait_for, timeout=30000)
        page.wait_for_timeout(1500)  # let charts/animations settle
        page.screenshot(path=out, full_page=full)
        browser.close()
    print(f"saved {out}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["shot", "sonar"])
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--full", action="store_true", help="full-page screenshot")
    ap.add_argument("--wait-for", default=None, help="CSS selector to wait for")
    a = ap.parse_args(argv)
    capture(a.url, a.out, full=a.full, wait_for=a.wait_for, sonar=(a.mode == "sonar"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
