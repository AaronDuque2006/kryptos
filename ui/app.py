import logging
import time

from textual.app import App

from models.user import User
from ui.screens.auth_screen import AuthScreen
from ui.screens.dashboard_screen import DashboardScreen

# Temas soportados por Textual para el MVP.
AVAILABLE_THEMES = (
    "textual-dark",
    "textual-light",
    "nord",
    "gruvbox",
)
AVAILABLE_THEME_SET = frozenset(AVAILABLE_THEMES)
DEFAULT_THEME = "textual-dark"


class PasswordManagerTUI(App):
    """
    Aplicación TUI principal del gestor de contraseñas Kryptos.

    Implementa un sistema de timeout de sesión por inactividad para
    mejorar la seguridad. Tras 15 minutos de inactividad, la sesión
    se cierra automáticamente y se redirige al usuario a la pantalla
    de login.
    """

    TITLE = "Kryptos Password Manager"

    # Constantes configurables para timeout de sesión
    SESSION_TIMEOUT_SECONDS = 900  # 15 minutos de inactividad máxima
    SESSION_WARNING_SECONDS = 60  # Advertir 1 minuto antes del cierre

    # Exponemos temas para que DashboardScreen pueda listarlos/ciclarlos.
    AVAILABLE_THEMES = AVAILABLE_THEMES
    DEFAULT_THEME = DEFAULT_THEME

    CSS = """
    Screen {
        background: $surface;
        color: $text;
    }

    Header {
        background: $panel;
        color: $primary;
    }

    Footer {
        background: $surface;
        color: $text;
    }

    Label {
        color: $text;
    }

    #auth-container {
        width: 72;
        height: auto;
        padding: 2 3;
        border: round $secondary;
        background: $surface;
        align: center middle;
        margin: 1 2;
    }

    #auth-title {
        text-style: bold;
        padding-bottom: 1;
        text-align: center;
        width: 100%;
        color: $warning;
    }

    #auth-help {
        color: $text;
        text-align: center;
        padding-top: 1;
    }

    #main-container {
        padding: 1 2;
        background: $surface;
        border: round $secondary;
        margin: 1 2;
    }

    #vault-title {
        text-style: bold;
        color: $success;
        padding-bottom: 1;
    }

    #vault-help {
        color: $text;
        padding-bottom: 1;
    }

    #command-input {
        margin-bottom: 1;
    }

    #entry-container {
        width: 72;
        height: auto;
        padding: 2 3;
        border: round $warning;
        background: $surface;
        align: center middle;
        margin: 1 2;
    }

    #entry-title {
        text-style: bold;
        color: $primary;
        text-align: center;
        padding-bottom: 1;
    }

    #entry-help {
        color: $text;
        padding-top: 1;
    }

    Input {
        background: $panel;
        color: $text;
        border: round $secondary;
    }

    Input:focus {
        border: round $error;
    }

    DataTable {
        background: $surface;
        color: $text;
    }
    """

    def __init__(self, auth_service, vault_service_factory):
        super().__init__()
        self.auth_service = auth_service
        self.vault_service_factory = vault_service_factory
        self.current_vault_service = None
        self._current_user_id: int | None = None
        self._user_repo = auth_service.user_repo if auth_service is not None else None

        # Tema base seguro al iniciar la app.
        self.theme = DEFAULT_THEME

        # Sistema de timeout por inactividad
        self._last_activity: float = 0.0
        self._session_timeout_interval = None
        self._warning_shown: bool = False

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

    def handle_login_success(self, crypto_engine, user: User) -> None:
        """
        Se ejecuta cuando el AuthScreen verifica correctamente la contraseña.
        Instancia el servicio de la bóveda y cambia la pantalla al Dashboard.
        También inicia el sistema de timeout por inactividad.
        """
        if user.id is None:
            self.notify(
                "No se pudo iniciar sesión: usuario inválido.", severity="error"
            )
            return

        self._current_user_id = user.id

        # Fabricamos el servicio de la bóveda específico para este usuario y sesión.
        self.current_vault_service = self.vault_service_factory(crypto_engine, user.id)

        # Aplicamos tema del usuario con fallback seguro.
        self._apply_user_theme(user)

        # Desplegamos el Dashboard (y quitamos la pantalla de login del stack si queremos)
        dashboard = DashboardScreen(
            vault_service=self.current_vault_service,
            on_logout_callback=self.handle_logout,
        )
        self.push_screen(dashboard)

        # Iniciamos el sistema de timeout por inactividad
        self._start_session_timeout()

    def _clear_active_session(self) -> None:
        """Limpia la sesión activa y detiene el timer de inactividad."""
        self._stop_session_timeout()

        if self.current_vault_service is None:
            return

        try:
            self.current_vault_service.crypto_engine.clear_memory()
        except Exception:
            pass

        self.current_vault_service = None
        self._current_user_id = None

    def set_theme(self, theme: str) -> bool:
        """Valida, aplica y persiste el tema elegido por el usuario."""
        if theme not in AVAILABLE_THEME_SET:
            self.notify(f"Tema no válido: {theme}", severity="error")
            return False

        self.theme = theme

        if self._current_user_id is not None and self._user_repo is not None:
            updated = self._user_repo.update_user_theme(self._current_user_id, theme)
            if not updated:
                self.notify(
                    "No se pudo persistir el tema del usuario.",
                    severity="warning",
                )

        self.notify(f"Tema cambiado a: {theme}", severity="information")
        return True

    def _apply_user_theme(self, user: User) -> None:
        """Aplica el tema persistido del usuario con fallback al tema por defecto."""
        saved_theme = user.theme or DEFAULT_THEME
        if saved_theme not in AVAILABLE_THEME_SET:
            logging.warning(
                "Tema inválido en DB para user_id=%s: %s. Fallback a %s.",
                user.id,
                saved_theme,
                DEFAULT_THEME,
            )
            saved_theme = DEFAULT_THEME

        self.theme = saved_theme

    def handle_logout(self) -> None:
        """Cierra la sesión actual y vuelve a la pantalla de login."""
        self._clear_active_session()

        auth_screen = AuthScreen(
            auth_service=self.auth_service,
            on_success_callback=self.handle_login_success,
        )
        self.push_screen(auth_screen)

    def _start_session_timeout(self) -> None:
        """
        Inicia el sistema de timeout por inactividad.

        Registra el timestamp actual y establece un intervalo de verificación
        que se ejecuta cada cierto tiempo para comprobar la inactividad.
        """
        self._last_activity = time.time()
        self._warning_shown = False

        # Verificar inactividad cada 30 segundos
        self._session_timeout_interval = self.set_interval(
            30.0, self._check_session_timeout
        )

    def _stop_session_timeout(self) -> None:
        """Detiene el intervalo de verificación de timeout."""
        if self._session_timeout_interval is not None:
            self._session_timeout_interval.stop()
            self._session_timeout_interval = None

        self._last_activity = 0.0
        self._warning_shown = False

    def _record_activity(self) -> None:
        """
        Registra una actividad del usuario, reiniciando el timer de inactividad.

        Este método debe llamarse en cada interacción del usuario (teclado, mouse).
        """
        if self.current_vault_service is not None:
            self._last_activity = time.time()
            self._warning_shown = False

    def _check_session_timeout(self) -> None:
        """
        Verifica si ha pasado el tiempo máximo de inactividad.

        Si queda poco tiempo, muestra una advertencia.
        Si se agota el tiempo, cierra la sesión automáticamente.
        """
        if self.current_vault_service is None:
            return

        elapsed = time.time() - self._last_activity
        remaining = self.SESSION_TIMEOUT_SECONDS - elapsed

        # Si queda menos del tiempo de advertencia, mostrar notificación
        if 0 < remaining <= self.SESSION_WARNING_SECONDS and not self._warning_shown:
            self._warning_shown = True
            seconds_left = int(remaining)
            self.notify(
                f"⚠️ La sesión se cerrará en {seconds_left} segundos por inactividad.",
                title="Advertencia de Sesión",
                severity="warning",
                timeout=min(remaining - 1, 10),
            )

        # Si se agotó el tiempo, cerrar sesión
        if elapsed >= self.SESSION_TIMEOUT_SECONDS:
            self._handle_timeout_logout()

    def _handle_timeout_logout(self) -> None:
        """
        Maneja el cierre de sesión por timeout de inactividad.

        Muestra una notificación y redirige al login.
        """
        self._stop_session_timeout()

        if self.current_vault_service is not None:
            self.notify(
                "Sesión cerrada por inactividad. Por favor, inicia sesión nuevamente.",
                title="Sesión Expirada",
                severity="error",
                timeout=5,
            )
            self.handle_logout()

    def on_key(self, event) -> None:
        """
        Captura todos los eventos de teclado para registrar actividad.

        Textual llama a este método para cada pulsación de tecla,
        permitiéndonos rastrear la actividad del usuario.
        """
        self._record_activity()

    def on_mouse_down(self, event) -> None:
        """Captura eventos de mouse para registrar actividad."""
        self._record_activity()

    def on_shutdown(self) -> None:
        """Limpieza al cerrar la aplicación."""
        self._stop_session_timeout()
        self._clear_active_session()
