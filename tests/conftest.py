import importlib
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    """Fresh app + isolated SQLite DB for every test."""
    import app as app_mod
    importlib.reload(app_mod)
    monkeypatch.setattr(app_mod, "DB_PATH", str(tmp_path / "test.db"))
    app_mod.app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)
    app_mod.init_db()
    return app_mod


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


@pytest.fixture()
def db(app_module):
    return app_module.db


def valid_form(**over):
    form = {"name": "Test Item", "category": "Toys", "description": "d",
            "price": "100", "stock": "5", "image_url": ""}
    form.update(over)
    return form
