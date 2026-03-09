def test_main_calls_run_gui(monkeypatch):
    """ST_SR_01_02
    main() mora pozvati GUI entrypoint.
    """
    import face_app.main as m
    import face_app.gui as g

    called = {"v": False}

    def fake_run_gui(*args, **kwargs):
        called["v"] = True

    monkeypatch.setattr(g, "run_gui", fake_run_gui)

    m.main()

    assert called["v"] is True


def test_main_module_runs_dunder_main(monkeypatch):
    """ST_SR_01_03
    Pokriva if __name__ == '__main__' blok u face_app.main.
    """
    import runpy
    import sys
    import face_app.gui as g

    monkeypatch.setattr(g, "run_gui", lambda *a, **k: None)

    # izbjegni warning / nepredvidivo ponašanje
    sys.modules.pop("face_app.main", None)

    runpy.run_module("face_app.main", run_name="__main__")