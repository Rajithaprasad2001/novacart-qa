"""Manual-style OWASP Top 10 checks, automated. Defect-revealing tests are xfail with the bug id."""
import pytest
from conftest import valid_form


# A03 Injection - passing checks
def test_xss_in_product_name_is_escaped(client):
    client.post("/admin/products/new", data=valid_form(name="<script>alert(1)</script>"))
    for url in ("/", "/admin/products", "/product/5"):
        assert b"<script>alert(1)</script>" not in client.get(url).data


def test_xss_in_order_fields_is_escaped(client):
    client.post("/cart/add/1", data={"quantity": "1"})
    client.post("/checkout", data={"customer_name": "<img src=x onerror=alert(1)>",
                                   "email": "a@b.co", "address": "x"})
    assert b"<img src=x onerror" not in client.get("/admin/orders/1").data


def test_javascript_url_rejected_as_image(client):
    r = client.post("/admin/products/new", data=valid_form(image_url="javascript:alert(1)"))
    assert r.status_code == 200  # form re-rendered with error


# A01 Broken access control
@pytest.mark.xfail(reason="BUG-01: admin pages have no authentication", strict=True)
@pytest.mark.parametrize("url", ["/admin/products", "/admin/orders", "/admin/products/new"])
def test_admin_requires_login(client, url):
    assert client.get(url).status_code in (302, 401, 403)


@pytest.mark.xfail(reason="BUG-02: no CSRF protection on state-changing POSTs", strict=True)
def test_post_without_csrf_token_rejected(client):
    r = client.post("/admin/products/1/delete")  # no token, no auth
    assert r.status_code in (400, 403)


# A05 / A02 misconfiguration
@pytest.mark.xfail(reason="BUG-03: Flask debug=True hard-coded in app.run()", strict=True)
def test_debug_mode_not_hardcoded():
    src = open("app.py").read()
    assert "debug=True" not in src


@pytest.mark.xfail(reason="BUG-04: default hard-coded SECRET_KEY allows session forgery", strict=True)
def test_secret_key_is_not_default(app_module):
    assert "novacart-demo-secret-key" not in app_module.app.secret_key


@pytest.mark.xfail(reason="BUG-05: no security headers (CSP, X-Frame-Options, nosniff)", strict=True)
def test_security_headers_present(client):
    h = client.get("/").headers
    assert "Content-Security-Policy" in h and "X-Frame-Options" in h and "X-Content-Type-Options" in h


def test_session_cookie_flags(client):
    client.post("/cart/add/1", data={"quantity": "1"})
    cookie = client.get_cookie("session")
    assert cookie is not None and cookie.http_only
