from ui.app import PasswordManagerTUI


def test_session_timeout_closes_active_session(monkeypatch):
    app = PasswordManagerTUI(auth_service=None, vault_service_factory=lambda *_: None)
    app.current_vault_service = object()
    app._last_activity = 100.0

    logout_calls: list[str] = []

    monkeypatch.setattr("ui.app.time.time", lambda: 1_100.0)
    monkeypatch.setattr(
        app, "_handle_timeout_logout", lambda: logout_calls.append("logout")
    )

    app._check_session_timeout()

    assert logout_calls == ["logout"]
