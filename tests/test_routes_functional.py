"""Functional / integration tests across the Flask routes (black-box via HTTP)."""
import re
from conftest import valid_form


def stock_of(db, pid):
    with db() as con:
        return con.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()[0]


# ---------------- Storefront ----------------
def test_home_lists_seed_products(client):
    r = client.get("/")
    assert r.status_code == 200
    for name in ("Wireless Headphones", "Classic Backpack", "Smart Watch", "Ceramic Mug"):
        assert name.encode() in r.data


def test_search_by_name_case_insensitive(client):
    r = client.get("/?q=mug")
    assert b"Ceramic Mug" in r.data and b"Smart Watch" not in r.data


def test_search_no_result(client):
    r = client.get("/?q=zzzzzz")
    assert b"Ceramic Mug" not in r.data and r.status_code == 200


def test_filter_by_category(client):
    r = client.get("/?category=Home")
    assert b"Ceramic Mug" in r.data and b"Smart Watch" not in r.data


def test_sort_price_ascending(client):
    r = client.get("/?sort=price_asc").data.decode()
    pos = [r.index(n) for n in ("Ceramic Mug", "Classic Backpack", "Wireless Headphones", "Smart Watch")]
    assert pos == sorted(pos)


def test_sort_price_descending(client):
    r = client.get("/?sort=price_desc").data.decode()
    assert r.index("Smart Watch") < r.index("Ceramic Mug")


def test_invalid_sort_falls_back_safely(client):
    assert client.get("/?sort=name;DROP TABLE products").status_code == 200


def test_sql_injection_in_search_is_harmless(client):
    r = client.get("/?q=' OR 1=1 --")
    assert r.status_code == 200 and b"Ceramic Mug" not in r.data


def test_product_detail_and_404(client):
    assert client.get("/product/1").status_code == 200
    r = client.get("/product/9999")
    assert r.status_code == 404 and b"Page not found" in r.data


# ---------------- Cart ----------------
def test_add_to_cart_and_count(client):
    client.post("/cart/add/1", data={"quantity": "2"})
    assert b"Wireless Headphones" in client.get("/cart").data
    with client.session_transaction() as s:
        assert s["cart"] == {"1": 2}


def test_add_same_product_accumulates(client):
    client.post("/cart/add/1", data={"quantity": "2"})
    client.post("/cart/add/1", data={"quantity": "3"})
    with client.session_transaction() as s:
        assert s["cart"]["1"] == 5


def test_add_quantity_above_stock_rejected(client):
    client.post("/cart/add/3", data={"quantity": "8"})  # stock = 7
    with client.session_transaction() as s:
        assert not s.get("cart")


def test_add_cumulative_above_stock_rejected(client):
    client.post("/cart/add/3", data={"quantity": "5"})
    client.post("/cart/add/3", data={"quantity": "5"})
    with client.session_transaction() as s:
        assert s["cart"]["3"] == 5


def test_add_quantity_boundaries(client):
    for q in ("0", "-1", "abc", ""):
        client.post("/cart/add/3", data={"quantity": q})
    with client.session_transaction() as s:
        assert not s.get("cart")
    client.post("/cart/add/3", data={"quantity": "7"})  # exactly stock
    with client.session_transaction() as s:
        assert s["cart"]["3"] == 7


def test_add_unknown_product_404(client):
    assert client.post("/cart/add/999", data={"quantity": "1"}).status_code == 404


def test_cart_update_and_remove(client):
    client.post("/cart/add/1", data={"quantity": "2"})
    client.post("/cart/update", data={"qty_1": "4"})
    with client.session_transaction() as s:
        assert s["cart"]["1"] == 4
    client.post("/cart/update", data={"qty_1": "0"})
    with client.session_transaction() as s:
        assert "1" not in s["cart"]


def test_cart_update_above_stock_keeps_old_quantity(client):
    client.post("/cart/add/3", data={"quantity": "2"})
    client.post("/cart/update", data={"qty_3": "50"})
    with client.session_transaction() as s:
        assert s["cart"]["3"] == 2


def test_cart_total(client):
    client.post("/cart/add/1", data={"quantity": "2"})   # 8500 x2
    client.post("/cart/add/4", data={"quantity": "1"})   # 950
    assert b"17950" in client.get("/cart").data


# ---------------- Checkout ----------------
def test_checkout_empty_cart_redirects(client):
    r = client.get("/checkout")
    assert r.status_code == 302


def test_checkout_success_reduces_stock_and_clears_cart(client, db):
    client.post("/cart/add/1", data={"quantity": "3"})
    r = client.post("/checkout", data={"customer_name": "Kasun", "email": "k@x.lk", "address": "Colombo"})
    assert r.status_code == 200 and b"ORDER CONFIRMED" in r.data
    assert stock_of(db, 1) == 9
    with client.session_transaction() as s:
        assert s["cart"] == {}
    with db() as con:
        assert con.execute("SELECT total FROM orders").fetchone()[0] == 25500
        assert con.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 1


def test_checkout_invalid_customer_data_creates_no_order(client, db):
    client.post("/cart/add/1", data={"quantity": "1"})
    r = client.post("/checkout", data={"customer_name": "", "email": "bad", "address": ""})
    assert r.status_code == 302
    with db() as con:
        assert con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
    assert stock_of(db, 1) == 12


def test_checkout_fails_when_stock_changed(client, db):
    client.post("/cart/add/3", data={"quantity": "5"})
    with db() as con:
        con.execute("UPDATE products SET stock=2 WHERE id=3"); con.commit()
    client.post("/checkout", data={"customer_name": "A", "email": "a@b.co", "address": "x"})
    with db() as con:
        assert con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
    assert stock_of(db, 3) == 2


def test_checkout_name_length_boundary(client):
    for n, ok in ((100, True), (101, False)):
        client.post("/cart/add/1", data={"quantity": "1"})
        r = client.post("/checkout", data={"customer_name": "a" * n, "email": "a@b.co", "address": "x"})
        assert (r.status_code == 200) is ok


# ---------------- Product CRUD ----------------
def test_create_read_update_delete_product(client, db):
    r = client.post("/admin/products/new", data=valid_form(name="Lamp"))
    assert r.status_code == 302
    assert b"Lamp" in client.get("/admin/products").data
    with db() as con:
        pid = con.execute("SELECT id FROM products WHERE name='Lamp'").fetchone()[0]
    client.post(f"/admin/products/{pid}/edit", data=valid_form(name="Lamp2", price="250"))
    assert b"Lamp2" in client.get(f"/product/{pid}").data
    client.post(f"/admin/products/{pid}/delete")
    assert client.get(f"/product/{pid}").status_code == 404


def test_create_invalid_product_shows_errors_and_saves_nothing(client, db):
    r = client.post("/admin/products/new", data=valid_form(price="-5", stock="x", name=""))
    assert r.status_code == 200
    with db() as con:
        assert con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 4


def test_delete_via_get_not_allowed(client):
    assert client.get("/admin/products/1/delete").status_code == 405


def test_delete_product_keeps_order_history(client, db):
    client.post("/cart/add/4", data={"quantity": "1"})
    client.post("/checkout", data={"customer_name": "A", "email": "a@b.co", "address": "x"})
    client.post("/admin/products/4/delete")
    r = client.get("/admin/orders/1")
    assert r.status_code == 200 and b"Ceramic Mug" in r.data


def test_orders_pages(client):
    assert client.get("/admin/orders").status_code == 200
    assert client.get("/admin/orders/999").status_code == 404


# ---------------- Extra coverage (white-box: branch coverage) ----------------
def test_checkout_get_renders_form_when_cart_not_empty(client):
    client.post("/cart/add/1", data={"quantity": "1"})
    assert client.get("/checkout").status_code == 200


def test_checkout_db_error_rolls_back(client, db, monkeypatch):
    import sqlite3
    client.post("/cart/add/1", data={"quantity": "1"})
    real = client.application.view_functions["checkout"].__globals__["db"]

    class Boom:
        def __init__(self, con): self.con = con
        def execute(self, sql, *a):
            if "INSERT INTO orders" in sql:
                raise sqlite3.Error("boom")
            return self.con.execute(sql, *a)
        def commit(self): self.con.commit()
        def rollback(self): self.con.rollback()
        def close(self): self.con.close()

    monkeypatch.setitem(client.application.view_functions["checkout"].__globals__, "db",
                        lambda: Boom(real()))
    r = client.post("/checkout", data={"customer_name": "A", "email": "a@b.co", "address": "x"})
    assert r.status_code == 302


def test_cart_update_ignores_missing_field(client):
    client.post("/cart/add/1", data={"quantity": "2"})
    client.post("/cart/update", data={})
    with client.session_transaction() as s:
        assert s["cart"]["1"] == 2


def test_edit_product_get_prefills_form(client):
    r = client.get("/admin/products/1/edit")
    assert r.status_code == 200 and b"Wireless Headphones" in r.data


def test_edit_product_invalid_shows_errors_and_keeps_data(client, db):
    r = client.post("/admin/products/1/edit", data=valid_form(price="-1"))
    assert r.status_code == 200
    with db() as con:
        assert con.execute("SELECT price FROM products WHERE id=1").fetchone()[0] == 8500


def test_edit_and_delete_unknown_product_404(client):
    assert client.get("/admin/products/999/edit").status_code == 404
    assert client.post("/admin/products/999/delete").status_code == 404
