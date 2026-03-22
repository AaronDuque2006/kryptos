from typing import TypedDict

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Label

from core.password_generator import PasswordGenerator


class EntryFormResult(TypedDict, total=False):
    title: str
    username_used: str
    password_used: str
    url: str
    notes: str


class EntryFormEditResult(EntryFormResult, total=False):
    id: int


class EntryFormScreen(Screen[EntryFormResult | EntryFormEditResult | None]):
    """
    Pantalla base para crear y editar credenciales.
    Soporta generación de contraseñas con Ctrl+G.
    """

    BINDINGS = [
        ("ctrl+s", "save", "Guardar"),
        ("ctrl+enter", "save", "Guardar"),
        ("ctrl+g", "generate_password", "Generar Password"),
        ("enter", "focus_next_field", "Siguiente"),
        ("escape", "cancel", "Cancelar"),
        ("up", "focus_previous_field", "Arriba"),
        ("down", "focus_next_field", "Abajo"),
        ("tab", "focus_next_field", "Siguiente"),
        ("shift+tab", "focus_previous_field", "Anterior"),
    ]

    FIELD_ORDER = [
        "entry-input-title",
        "entry-input-username",
        "entry-input-password",
        "entry-input-url",
        "entry-input-notes",
    ]

    def __init__(self, existing_entry: dict | None = None, **kwargs):
        super().__init__(**kwargs)
        self.existing_entry = existing_entry

    def compose(self) -> ComposeResult:
        title_text = "Editar Credencial" if self.existing_entry else "Nueva Credencial"

        yield Header()
        with Vertical(id="entry-container"):
            yield Label(title_text, id="entry-title")
            yield Input(
                placeholder="Título *" if not self.existing_entry else "Título",
                id="entry-input-title",
            )
            yield Input(
                placeholder="Usuario *" if not self.existing_entry else "Usuario",
                id="entry-input-username",
            )
            yield Input(
                placeholder="Contraseña * (Ctrl+G genera)",
                id="entry-input-password",
                password=True,
            )
            yield Input(placeholder="URL (opcional)", id="entry-input-url")
            yield Input(placeholder="Notas (opcional)", id="entry-input-notes")
            yield Label(
                "Arriba/Abajo/Tab navega | Enter avanza | Ctrl+G genera password | Ctrl+S/Ctrl+Enter guarda | Esc cancela",
                id="entry-help",
            )
        yield Footer()

    def on_mount(self) -> None:
        if self.existing_entry:
            self.query_one("#entry-input-title", Input).value = str(
                self.existing_entry.get("title", "")
            )
            self.query_one("#entry-input-username", Input).value = str(
                self.existing_entry.get("username", "")
            )
            self.query_one("#entry-input-password", Input).value = str(
                self.existing_entry.get("password", "")
            )
            self.query_one("#entry-input-url", Input).value = str(
                self.existing_entry.get("url", "")
            )
            self.query_one("#entry-input-notes", Input).value = str(
                self.existing_entry.get("notes", "")
            )

        self.query_one("#entry-input-title", Input).focus()

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

    def action_generate_password(self) -> None:
        try:
            password = PasswordGenerator.generate(length=20)
            password_input = self.query_one("#entry-input-password", Input)
            password_input.value = password
            self.notify("Contraseña generada (20 caracteres)", severity="information")
        except ValueError as e:
            self.notify(str(e), severity="error")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        current_id = event.input.id
        if current_id not in self.FIELD_ORDER:
            return

        self.action_focus_next_field()

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

        result: EntryFormResult | EntryFormEditResult = {
            "title": title,
            "username_used": username,
            "password_used": password,
            "url": url,
            "notes": notes,
        }

        if self.existing_entry:
            existing_id = self.existing_entry.get("id")
            if isinstance(existing_id, int):
                result["id"] = existing_id

        self.dismiss(result)
