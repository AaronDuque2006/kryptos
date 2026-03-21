from textual.app import App
from ui.screens.auth_screen import AuthScreen
from ui.screens.dashboard_screen import DashboardScreen


class PasswordManagerTUI(App):
    TITLE = "Kryptos Password Manager"

    CSS = """
    Screen {
        background: #1e1e2e;
        color: #cdd6f4;
    }

    Header {
        background: #313244;
        color: #f5e0dc;
    }

    Footer {
        background: #181825;
        color: #a6adc8;
    }

    Label {
        color: #cdd6f4;
    }

    #auth-container {
        width: 72;
        height: auto;
        padding: 2 3;
        border: round #89b4fa;
        background: #11111b;
        align: center middle;
        margin: 1 2;
    }

    #auth-title {
        text-style: bold;
        padding-bottom: 1;
        text-align: center;
        width: 100%;
        color: #f9e2af;
    }

    #auth-help {
        color: #a6adc8;
        text-align: center;
        padding-top: 1;
    }

    #main-container {
        padding: 1 2;
        background: #11111b;
        border: round #74c7ec;
        margin: 1 2;
    }

    #vault-title {
        text-style: bold;
        color: #a6e3a1;
        padding-bottom: 1;
    }

    #vault-help {
        color: #bac2de;
        padding-bottom: 1;
    }

    #command-input {
        margin-bottom: 1;
    }

    #entry-container {
        width: 72;
        height: auto;
        padding: 2 3;
        border: round #f9e2af;
        background: #11111b;
        align: center middle;
        margin: 1 2;
    }

    #entry-title {
        text-style: bold;
        color: #f5c2e7;
        text-align: center;
        padding-bottom: 1;
    }

    #entry-help {
        color: #a6adc8;
        padding-top: 1;
    }

    Input {
        background: #313244;
        color: #cdd6f4;
        border: round #b4befe;
    }

    Input:focus {
        border: round #f38ba8;
    }

    DataTable {
        background: #1e1e2e;
        color: #cdd6f4;
    }
    """

    def __init__(self, auth_service, vault_service_factory):
        super().__init__()
        self.auth_service = auth_service
        self.vault_service_factory = vault_service_factory
        self.current_vault_service = None

    def on_mount(self) -> None:
        """
        Arranca la aplicación montando la pantalla de autenticación.
        Le pasamos nuestro método 'handle_login_success' como callback.
        """
        auth_screen = AuthScreen(
            auth_service=self.auth_service,
            on_success_callback=self.handle_login_success,
        )
        self.push_screen(auth_screen)

    def handle_login_success(self, crypto_engine, user_id: int) -> None:
        """
        Se ejecuta cuando el AuthScreen verifica correctamente la contraseña.
        Instancia el servicio de la bóveda y cambia la pantalla al Dashboard.
        """
        # Fabricamos el servicio de la bóveda específico para este usuario y sesión
        self.current_vault_service = self.vault_service_factory(crypto_engine, user_id)

        # Desplegamos el Dashboard (y quitamos la pantalla de login del stack si queremos)
        dashboard = DashboardScreen(
            vault_service=self.current_vault_service,
            on_logout_callback=self.handle_logout,
        )
        self.push_screen(dashboard)

    def _clear_active_session(self) -> None:
        if self.current_vault_service is None:
            return

        try:
            self.current_vault_service.crypto_engine.clear_memory()
        except Exception:
            pass

        self.current_vault_service = None

    def handle_logout(self) -> None:
        self._clear_active_session()

        auth_screen = AuthScreen(
            auth_service=self.auth_service,
            on_success_callback=self.handle_login_success,
        )
        self.push_screen(auth_screen)

    def on_shutdown(self) -> None:
        self._clear_active_session()
