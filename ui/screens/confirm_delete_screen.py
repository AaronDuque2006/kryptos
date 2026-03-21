from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label
from textual.containers import Vertical


class ConfirmDeleteScreen(Screen[bool]):
    BINDINGS = [
        ("y", "confirm", "Confirmar"),
        ("enter", "confirm", "Confirmar"),
        ("n", "cancel", "Cancelar"),
        ("escape", "cancel", "Cancelar"),
    ]

    def __init__(self, entry_label: str, **kwargs):
        super().__init__(**kwargs)
        self.entry_label = entry_label

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="entry-container"):
            yield Label("Confirmar eliminación", id="entry-title")
            yield Label(
                f"Vas a eliminar: {self.entry_label}",
                id="confirm-delete-label",
            )
            yield Label(
                "Enter/Y confirma | N/Esc cancela",
                id="entry-help",
            )
        yield Footer()

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
