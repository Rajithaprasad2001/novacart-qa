from behave import given, when, then, use_step_matcher


def _product_id(context, name):
    with context.app.db() as con:
        return con.execute("SELECT id FROM products WHERE name=?", (name,)).fetchone()[0]


@given('the store has "{name}" in stock')
def step_in_stock(context, name):
    with context.app.db() as con:
        assert con.execute("SELECT stock FROM products WHERE name=?", (name,)).fetchone()[0] > 0


@when('I add {qty:d} units of "{name}" to my cart')
def step_add(context, qty, name):
    context.client.post(f"/cart/add/{_product_id(context, name)}", data={"quantity": str(qty)})


use_step_matcher("re")


@when(u'I check out as "(?P<name>.*)" with email "(?P<email>.*)" and address "(?P<address>.*)"')
def step_checkout(context, name, email, address):
    context.response = context.client.post("/checkout", data={
        "customer_name": name, "email": email, "address": address})


use_step_matcher("parse")


@then("I should see an order confirmation")
def step_confirm(context):
    assert b"ORDER CONFIRMED" in context.response.data


@then("I should not see an order confirmation")
def step_no_confirm(context):
    assert b"ORDER CONFIRMED" not in context.response.data


@then('the stock of "{name}" should be {n:d}')
def step_stock(context, name, n):
    with context.app.db() as con:
        assert con.execute("SELECT stock FROM products WHERE name=?", (name,)).fetchone()[0] == n


@then("my cart should be empty")
def step_cart_empty(context):
    with context.client.session_transaction() as s:
        assert not s.get("cart")
