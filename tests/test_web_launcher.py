"""Local launch experience (S070): localhost-only bind, debug off, no daemon."""

from __future__ import annotations

from app.web import launcher


def test_default_bind_is_localhost_only():
    assert launcher.HOST == "127.0.0.1"


def test_main_binds_via_make_server_and_serves_in_the_foreground(monkeypatch):
    calls = {}

    class FakeHttpd:
        def serve_forever(self):
            calls["served"] = True

    def fake_make_server(host, port, app, **kwargs):
        calls["host"] = host
        calls["port"] = port
        calls["kwargs"] = kwargs
        return FakeHttpd()

    class FakeTimer:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            pass

    monkeypatch.setattr(launcher, "create_app", lambda: object())
    monkeypatch.setattr(launcher, "make_server", fake_make_server)
    monkeypatch.setattr(launcher.threading, "Timer", FakeTimer)
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: None)

    result = launcher.main()

    assert result == 0
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8765
    assert calls["served"] is True
    assert calls["kwargs"].get("threaded") is True


def test_server_is_threaded_so_one_open_browser_connection_never_blocks_another_request():
    """Regression cho S070 Independent Review: ``make_server`` mặc định là
    single-threaded — một kết nối keep-alive (vd: tab trình duyệt launcher tự
    mở) sẽ treo vô thời hạn mọi request khác nếu thiếu ``threaded=True``.
    Đã verify trực tiếp bằng repro: giữ một HTTP/1.1 keep-alive connection mở,
    request độc lập thứ hai timeout 100% cho tới khi connection đầu đóng.
    """
    import inspect

    source = inspect.getsource(launcher.main)
    assert "threaded=True" in source


def test_main_reuses_an_already_running_server_instead_of_starting_a_second_one(monkeypatch):
    opened = {}

    def fake_make_server(host, port, app, **kwargs):
        raise OSError("Address already in use")

    monkeypatch.setattr(launcher, "create_app", lambda: object())
    monkeypatch.setattr(launcher, "make_server", fake_make_server)
    monkeypatch.setattr(launcher.webbrowser, "open", lambda url: opened.setdefault("url", url))

    result = launcher.main()

    assert result == 0
    assert opened["url"] == "http://127.0.0.1:8765/"


def test_debug_never_enabled_because_make_server_carries_no_debugger_or_reloader():
    import inspect

    source = inspect.getsource(launcher)
    assert "debug=True" not in source
    assert "use_reloader=True" not in source
