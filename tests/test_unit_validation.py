"""Unit tests - validate_product(): Equivalence Partitioning + Boundary Value Analysis."""
import pytest
from conftest import valid_form


def run(app_module, **over):
    return app_module.validate_product(valid_form(**over))


# ---- Equivalence partitioning: price ------------------------------------
@pytest.mark.parametrize("price,ok", [
    ("100", True),        # valid partition: positive
    ("0", True),          # boundary
    ("-0.01", False),     # invalid: negative
    ("abc", False),       # invalid: non-numeric
    ("", False),          # invalid: empty
    ("nan", False),       # invalid: NaN
    ("inf", False),       # invalid: infinity
])
def test_price_partitions(app_module, price, ok):
    _, errors = run(app_module, price=price)
    assert (errors == []) is ok


# ---- Boundary value analysis: stock (min = 0) ---------------------------
@pytest.mark.parametrize("stock,ok", [
    ("-1", False), ("0", True), ("1", True), ("2.5", False), ("x", False),
])
def test_stock_bva(app_module, stock, ok):
    _, errors = run(app_module, stock=stock)
    assert (errors == []) is ok


# ---- Boundary value analysis: name length (max = 100) -------------------
@pytest.mark.parametrize("length,ok", [(0, False), (1, True), (99, True),
                                       (100, True), (101, False)])
def test_name_length_bva(app_module, length, ok):
    _, errors = run(app_module, name="a" * length)
    assert (errors == []) is ok


# ---- Boundary value analysis: category length (max = 50) ----------------
@pytest.mark.parametrize("length,ok", [(0, False), (1, True), (50, True), (51, False)])
def test_category_length_bva(app_module, length, ok):
    _, errors = run(app_module, category="c" * length)
    assert (errors == []) is ok


# ---- Boundary value analysis: description length (max = 1000) -----------
@pytest.mark.parametrize("length,ok", [(0, True), (1000, True), (1001, False)])
def test_description_length_bva(app_module, length, ok):
    _, errors = run(app_module, description="d" * length)
    assert (errors == []) is ok


# ---- Image URL partitions -----------------------------------------------
@pytest.mark.parametrize("url,ok", [
    ("", True), ("http://x.io/a.png", True), ("HTTPS://x.io/a.png", True),
    ("javascript:alert(1)", False), ("ftp://x.io/a", False), ("x.io/a.png", False),
])
def test_image_url_partitions(app_module, url, ok):
    _, errors = run(app_module, image_url=url)
    assert (errors == []) is ok


def test_whitespace_only_name_rejected(app_module):
    _, errors = run(app_module, name="    ")
    assert "Product name is required." in errors


def test_multiple_errors_reported_together(app_module):
    _, errors = run(app_module, name="", category="", price="x", stock="y")
    assert len(errors) == 4
