import importlib, os, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def before_scenario(context, scenario):
    import app as app_mod
    importlib.reload(app_mod)
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app_mod.DB_PATH = path
    app_mod.app.config["TESTING"] = True
    app_mod.init_db()
    context.app = app_mod
    context.client = app_mod.app.test_client()
    context.response = None
    context.db_path = path


def after_scenario(context, scenario):
    import gc
    gc.collect()  # release SQLite handles (Windows locks open files)
    try:
        os.remove(context.db_path)
    except PermissionError:
        pass  # temp file; the OS cleans it up later
