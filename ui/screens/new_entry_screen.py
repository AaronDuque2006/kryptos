from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label


class NewEntryScreen(Screen[dict | None]):
    BINDINGS = [
        ("ctrl+s", "save", "Guardar"),
        ("enter", "save", "Guardar"),
        ("escape", "cancel", "Cancelar"),
        ("tab", "focus_next", "Siguiente"),
        ("shift+tab", "focus_previous", "Anterior"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="entry-container"):
            yield Label("Nueva Credencial", id="entry-title")
            yield Input(placeholder="Título *", id="entry-input-title")
            yield Input(placeholder="Usuario *", id="entry-input-username")
            yield Input(
                placeholder="Contraseña *", id="entry-input-password", password=True
            )
            yield Input(placeholder="URL (opcional)", id="entry-input-url")
            yield Input(placeholder="Notas (opcional)", id="entry-input-notes")
            yield Label(
                "Tab/Shift+Tab navega | Enter/Ctrl+S guarda | Esc cancela",
                id="entry-help",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#entry-input-title", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        order = [
            "entry-input-title",
            "entry-input-username",
            "entry-input-password",
            "entry-input-url",
            "entry-input-notes",
        ]
        current_id = event.input.id
        if current_id not in order:
            return

        idx = order.index(current_id)
        if idx < len(order) - 1:
            self.query_one(f"#{order[idx + 1]}", Input).focus()
        else:
            self.action_save()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        title = self.query_one("#entry-input-title", Input).value.strip()
        username = self.query_one("#entry-input-username", Input).value.strip()
        password = self.query_one("#entry-input-password", Input).value
        url = self.query_one("#entry-input-url", Input).value.strip()
        notes = self.query_one("#entry-input-notes", Input).value.strip()

        if not title or not username or not password:
            self.notify(
                "Título, usuario y contraseña son obligatorios", severity="warning"
            )
            return

        self.dismiss(
            {
                "title": title,
                "username_used": username,
                "password_used": password,
                "url": url,
                "notes": notes,
            }
        )
