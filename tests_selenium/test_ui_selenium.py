"""End-to-end UI automation with Selenium WebDriver (headless Chrome).

Same four user flows as tests_ui/test_ui_playwright.py, so the task-list
requirement "automate a few test cases with Selenium" is met directly.
Starts the Flask app on a temp SQLite DB; screenshots go to evidence/selenium_*.png.
"""
import os
import socket
import subprocess
import sys
import tempfile
import time

import pytest
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "evidence")


@pytest.fixture(scope="session")
def base_url():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    db = os.path.join(tempfile.mkdtemp(), "selenium.db")
    code = ("import app; app.DB_PATH=%r; app.init_db(); "
            "app.app.run(port=%d, debug=False)" % (db, port))
    proc = subprocess.Popen([sys.executable, "-c", code], cwd=ROOT,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(75):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close()
            break
        except OSError:
            time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    proc.terminate()


def _driver(width=1280, height=900):
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--window-size={width},{height}")
    drv = webdriver.Chrome(options=opts)
    drv.implicitly_wait(5)
    return drv


@pytest.fixture()
def driver():
    drv = _driver()
    yield drv
    drv.quit()


def _click(drv, el):
    """Scroll the element to the centre of the viewport before clicking, so
    fixed headers/footers cannot intercept the click."""
    drv.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
    try:
        el.click()
    except ElementClickInterceptedException:
        drv.execute_script("arguments[0].click();", el)


def _type(drv, name, value):
    el = drv.find_element(By.NAME, name)
    el.clear()
    el.send_keys(value)


def _shot(drv, name):
    os.makedirs(SHOTS, exist_ok=True)
    drv.save_screenshot(os.path.join(SHOTS, name))


def test_selenium_search_and_filter(driver, base_url):
    driver.get(base_url + "/?q=mug")
    body = driver.find_element(By.TAG_NAME, "body").text
    assert "Ceramic Mug" in body
    assert "Smart Watch" not in body
    driver.execute_script(
        "document.documentElement.style.scrollBehavior='auto';"
        "window.scrollTo({top: document.getElementById('products').offsetTop - 90,"
        " behavior: 'instant'});")
    time.sleep(0.8)
    _shot(driver, "selenium_search.png")


def test_selenium_add_to_cart_and_checkout(driver, base_url):
    driver.get(base_url + "/product/4")
    qty = driver.find_element(By.NAME, "quantity")
    qty.clear()
    qty.send_keys("2")
    _click(driver, driver.find_element(By.XPATH, "//button[contains(., 'Add to cart')]"))
    driver.get(base_url + "/cart")
    assert "Ceramic Mug" in driver.page_source
    _shot(driver, "selenium_cart.png")

    driver.get(base_url + "/checkout")
    driver.find_element(By.NAME, "customer_name").send_keys("Selenium User")
    driver.find_element(By.NAME, "email").send_keys("selenium@example.com")
    driver.find_element(By.NAME, "address").send_keys("Galle")
    _click(driver, driver.find_element(By.CSS_SELECTOR, "button.checkout-submit"))
    WebDriverWait(driver, 10).until(
        lambda d: "ORDER CONFIRMED" in d.page_source.upper())
    _shot(driver, "selenium_order_success.png")


def test_selenium_admin_create_product(driver, base_url):
    driver.get(base_url + "/admin/products/new")
    _type(driver, "name", "Selenium Lamp")
    _type(driver, "category", "Home")
    _type(driver, "price", "1500")
    _type(driver, "stock", "3")
    _click(driver, driver.find_element(By.XPATH, "//button[contains(., 'Save product')]"))
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Selenium Lamp"))
    row = driver.find_element(By.XPATH, "//tr[contains(., 'Selenium Lamp')]")
    cells = row.text.split()
    assert "1500.00" in cells and "3" in cells
    _shot(driver, "selenium_admin_product.png")


def test_selenium_mobile_viewport_no_horizontal_scroll(base_url):
    drv = _driver(375, 800)
    try:
        drv.set_window_size(375, 800)
        drv.get(base_url + "/")
        overflow = drv.execute_script(
            "return document.documentElement.scrollWidth > window.innerWidth")
        _shot(drv, "selenium_mobile.png")
    finally:
        drv.quit()
    assert not overflow
