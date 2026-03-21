from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Label, Header, Footer
from textual.containers import Vertical
from textual.reactive import reactive


class AuthScreen(Screen):
    """
    Pantalla unificada para Login y Registro.
    Utiliza una variable reactiva para cambiar la interfaz dinámicamente.
    """

    BINDINGS = [
        ("ctrl+enter", "submit", "Iniciar/Registrar"),
        ("ctrl+r", "toggle_mode", "Cambiar Modo"),
        ("f2", "toggle_mode", "Modo Registro/Login"),
        ("ctrl+n", "toggle_mode", "Modo Registro/Login"),
        ("escape", "app.quit", "Salir"),
        ("tab", "focus_next_field", "Siguiente"),
        ("shift+tab", "focus_previous_field", "Anterior"),
        ("up", "focus_previous_field", "Arriba"),
        ("down", "focus_next_field", "Abajo"),
    ]

    FIELD_ORDER = ["input-username", "input-password"]

    is_login_mode = reactive(True)

    def __init__(self, auth_service, on_success_callback, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = auth_service
        self.on_success_callback = on_success_callback

    def compose(self) -> ComposeResult:
        """Construye el DOM de la pantalla."""
        yield Header()

        with Vertical(id="auth-container"):
            yield Label("Iniciar Sesión", id="auth-title")

            yield Input(placeholder="Nombre de usuario", id="input-username")
            yield Input(
                placeholder="Contraseña Maestra", id="input-password", password=True
            )
            yield Label(
                "F2/Ctrl+N cambia Login↔Registro | Enter en password envía | Arriba/Abajo/Tab navega",
                id="auth-help",
            )

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#input-username", Input).focus()

    def watch_is_login_mode(self, login_mode: bool) -> None:
        """
        Este método se dispara automáticamente cuando 'is_login_mode' cambia.
        Actualiza los textos de la interfaz sin tener que recargar la pantalla.
        """
        title = self.query_one("#auth-title", Label)

        if login_mode:
            title.update("Iniciar Sesión en la Bóveda")
            self.notify("Modo: Login", severity="information", timeout=1.5)
        else:
            title.update("Registrar Nueva Bóveda")
            self.notify("Modo: Registro", severity="information", timeout=1.5)

    def _current_field_index(self) -> int:
        focused = self.focused
        if focused is None:
            return 0
        focused_id = focused.id if hasattr(focused, "id") else None
        if focused_id in self.FIELD_ORDER:
            return self.FIELD_ORDER.index(focused_id)
        return 0

    def action_focus_next_field(self) -> None:
        idx = self._current_field_index()
        next_idx = (idx + 1) % len(self.FIELD_ORDER)
        self.query_one(f"#{self.FIELD_ORDER[next_idx]}", Input).focus()

    def action_focus_previous_field(self) -> None:
        idx = self._current_field_index()
        prev_idx = (idx - 1) % len(self.FIELD_ORDER)
        self.query_one(f"#{self.FIELD_ORDER[prev_idx]}", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        current_id = event.input.id
        if current_id not in self.FIELD_ORDER:
            return

        if current_id == "input-username":
            self.query_one("#input-password", Input).focus()
            return

        username = self.query_one("#input-username", Input).value.strip()
        password = self.query_one("#input-password", Input).value

        if username and password:
            self.handle_submit()
        else:
            self.notify(
                "Completa usuario y contraseña (usa ↑/↓ para navegar).",
                severity="warning",
            )

    def action_toggle_mode(self) -> None:
        self.is_login_mode = not self.is_login_mode
        self.clear_inputs()
        self.query_one("#input-username", Input).focus()

    def action_submit(self) -> None:
        self.handle_submit()

    def handle_submit(self) -> None:
        """Procesa el formulario de login o registro."""
        username = self.query_one("#input-username", Input).value.strip()
        password = self.query_one("#input-password", Input).value

        if not username or not password:
            self.notify("Por favor, completa todos los campos.", severity="warning")
            return

        try:
            if self.is_login_mode:
                crypto_engine = self.auth_service.login(username, password)
                user = self.auth_service.user_repo.get_user_by_username(username)

                self.notify("Autenticación exitosa", severity="information")
                self.clear_inputs()

                self.on_success_callback(crypto_engine, user.id)

            else:
                self.auth_service.register(username, password)
                self.notify(
                    "Cuenta creada exitosamente. Ahora puedes iniciar sesión.",
                    severity="information",
                )
                self.is_login_mode = True
                self.clear_inputs()
                self.query_one("#input-username", Input).focus()

        except ValueError as e:
            self.notify(str(e), severity="error")
            self.query_one("#input-password", Input).value = ""
            self.query_one("#input-password", Input).focus()
            if self.is_login_mode:
                self.notify(
                    "Si no tienes cuenta, presiona F2 o Ctrl+N para registrarte.",
                    severity="warning",
                    timeout=4,
                )

    def clear_inputs(self):
        """Limpia los campos por seguridad tras un intento o cambio de pantalla."""
        self.query_one("#input-username", Input).value = ""
        self.query_one("#input-password", Input).value = ""
