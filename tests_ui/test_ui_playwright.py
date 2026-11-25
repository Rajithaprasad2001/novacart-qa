"""End-to-end UI automation (Playwright, Chromium). Starts the Flask app on a temp DB."""
import os, subprocess, sys, time, socket, tempfile
import pytest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "evidence")


@pytest.fixture(scope="session")
def base_url():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    db = tempfile.mktemp(suffix=".db")
    code = ("import app; app.DB_PATH=%r; app.init_db(); "
            "app.app.run(port=%d, debug=False)" % (db, port))
    p = subprocess.Popen([sys.executable, "-c", code], cwd=ROOT,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close(); break
        except OSError:
            time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    p.terminate()


@pytest.fixture()
def page(base_url):
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 900})
        yield pg
        b.close()


def test_ui_search_and_filter(page, base_url):
    page.goto(base_url + "/?q=mug")
    assert "Ceramic Mug" in page.content() and "Smart Watch" not in page.content()
    page.screenshot(path=os.path.join(SHOTS, "ui_search.png"))


def test_ui_add_to_cart_and_checkout(page, base_url):
    page.goto(base_url + "/product/4")
    page.fill("input[name=quantity]", "2")
    page.click("button:has-text('Add to cart')")
    page.goto(base_url + "/cart")
    assert "Ceramic Mug" in page.content()
    page.screenshot(path=os.path.join(SHOTS, "ui_cart.png"))
    page.goto(base_url + "/checkout")
    page.fill("input[name=customer_name]", "Test User")
    page.fill("input[name=email]", "test@example.com")
    page.fill("textarea[name=address]", "Matara")
    page.click("button[type=submit]")
    assert "ORDER CONFIRMED" in page.content().upper()
    page.screenshot(path=os.path.join(SHOTS, "ui_order_success.png"))


def test_ui_admin_create_product(page, base_url):
    page.goto(base_url + "/admin/products/new")
    page.fill("input[name=name]", "UI Lamp"); page.fill("input[name=category]", "Home")
    page.fill("input[name=price]", "1500"); page.fill("input[name=stock]", "3")
    page.click("button:has-text('Save product')")
    assert "UI Lamp" in page.content()


def test_ui_mobile_viewport_no_horizontal_scroll(base_url):
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 375, "height": 800})
        pg.goto(base_url + "/")
        overflow = pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        pg.screenshot(path=os.path.join(SHOTS, "ui_mobile.png"))
        b.close()
    assert not overflow
