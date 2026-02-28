import runpy

def test_main_calls_run_gui(monkeypatch):
    """ST_SR_01_02
    main() must call run_gui().
    """
    import face_app.main as m

    called = {"v": False}

    def fake_run_gui(*args, **kwargs):
        called["v"] = True

    monkeypatch.setattr(m, "run_gui", fake_run_gui)
    m.main()
    assert called["v"] is True

def test_main_module_runs_dunder_main(monkeypatch):
    """ST_SR_01_03
    Pokriva if __name__ == '__main__' blok u face_app.main
    """
    # spriječi da se otvori pravi GUI
    import face_app.gui as g
    monkeypatch.setattr(g, "run_gui", lambda *a, **k: None)

    runpy.run_module("face_app.main", run_name="__main__")