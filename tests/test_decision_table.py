"""Decision-table tests for the checkout validation rule (rules R1-R8).

Conditions: C1 name valid, C2 email valid, C3 address valid.
Action: order accepted only when all three are true.
"""
import itertools
import pytest


def _submit(client, name, email, address):
    with client.session_transaction() as s:
        s["cart"] = {"1": 1}
    return client.post("/checkout", data={
        "customer_name": name, "email": email, "address": address})


@pytest.mark.parametrize("c1,c2,c3", list(itertools.product([True, False], repeat=3)))
def test_checkout_decision_table(client, c1, c2, c3):
    resp = _submit(client,
                   "Nimal" if c1 else "",
                   "nimal@example.com" if c2 else "not-an-email",
                   "12 Galle Rd" if c3 else "")
    accepted = resp.status_code == 200 and b"ORDER CONFIRMED" in resp.data
    assert accepted is (c1 and c2 and c3)
