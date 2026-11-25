"""Regression tests for functional defects found during QA. Each is xfail(strict) until fixed;
once the developer fixes the bug the test XPASSes (strict -> fails the build) so the marker is removed."""
import re

import pytest
from conftest import valid_form


# BUG-06 fixed (issue #6): this is now a normal regression test.
def test_huge_stock_value_is_validated(client):
    r = client.post("/admin/products/new", data=valid_form(stock=str(10 ** 30)))
    assert r.status_code == 200 and b"Stock" in r.data


@pytest.mark.xfail(reason="BUG-07: corrupt/non-numeric cart in session breaks EVERY page (500)", strict=True)
def test_corrupt_cart_session_does_not_crash_site(client):
    with client.session_transaction() as s:
        s["cart"] = {"abc": "x"}
    assert client.get("/").status_code == 200
    assert client.get("/cart").status_code == 200


@pytest.mark.xfail(reason="BUG-08: cart badge counts items of products that were deleted", strict=True)
def test_cart_count_ignores_deleted_products(client):
    client.post("/cart/add/4", data={"quantity": "2"})
    client.post("/admin/products/4/delete")
    html = client.get("/cart").data.decode()
    badge = re.search(r'luxury-cart-count">(\d+)<', html).group(1)
    assert badge == "0"


@pytest.mark.xfail(reason="BUG-09: no upper bound on price (1e308 accepted)", strict=True)
def test_price_has_upper_bound(client):
    r = client.post("/admin/products/new", data=valid_form(price="1e308"))
    assert r.status_code == 200  # should be re-rendered with an error


@pytest.mark.xfail(reason="BUG-10: price with >2 decimals accepted then displayed rounded", strict=True)
def test_price_two_decimals_only(client):
    r = client.post("/admin/products/new", data=valid_form(price="10.999"))
    assert r.status_code == 200


@pytest.mark.xfail(reason="BUG-11: invalid text in cart quantity silently deletes the item", strict=True)
def test_invalid_cart_update_does_not_remove_item(client):
    client.post("/cart/add/1", data={"quantity": "2"})
    client.post("/cart/update", data={"qty_1": "abc"})
    with client.session_transaction() as s:
        assert s["cart"].get("1") == 2


@pytest.mark.xfail(reason="BUG-12: email regex accepts 'a@b..com' and 'a@-b.com'", strict=True)
@pytest.mark.parametrize("email", ["a@b..com", "a@-b.com"])
def test_email_validation_strict(client, email):
    client.post("/cart/add/1", data={"quantity": "1"})
    r = client.post("/checkout", data={"customer_name": "A", "email": email, "address": "x"})
    assert b"ORDER CONFIRMED" not in r.data


@pytest.mark.xfail(reason="BUG-13: HTML maxlength (120/80) disagrees with server limits (100/50)", strict=True)
def test_form_maxlength_matches_server_limits(client):
    html = client.get("/admin/products/new").data.decode()
    assert 'name="name" value="" required maxlength="100"' in html.replace("  ", " ")
    assert 'maxlength="50"' in html
