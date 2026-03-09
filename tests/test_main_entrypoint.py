import runpy
import sys
import types


def test_main_calls_run_gui(monkeypatch):
    """ST_SR_01_02
    main() must call run_gui().
    """
    called = {"v": False}

    fake_gui = types.ModuleType("face_app.gui")

    def fake_run_gui(*args, **kwargs):
        called["v"] = True

    fake_gui.run_gui = fake_run_gui
    monkeypatch.setitem(sys.modules, "face_app.gui", fake_gui)

    import face_app.main as m
    m.main()

    assert called["v"] is True


def test_main_module_runs_dunder_main(monkeypatch):
    """ST_SR_01_03
    Pokriva if __name__ == '__main__' blok u face_app.main.
    """
    called = {"v": False}

    fake_gui = types.ModuleType("face_app.gui")

    def fake_run_gui(*args, **kwargs):
        called["v"] = True

    fake_gui.run_gui = fake_run_gui
    monkeypatch.setitem(sys.modules, "face_app.gui", fake_gui)

    sys.modules.pop("face_app.main", None)
    runpy.run_module("face_app.main", run_name="__main__")

    assert called["v"] is True