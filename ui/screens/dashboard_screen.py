# ui/screens/dashboard_screen.py

from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Label, Input
from textual.containers import Vertical
from typing import cast
import pyperclip
from ui.screens.entry_form_screen import EntryFormScreen
from ui.screens.confirm_delete_screen import ConfirmDeleteScreen

EntryResult = dict[str, object]


class DashboardScreen(Screen):
    """
    Pantalla principal donde el usuario ve sus bóvedas.
    """

    BINDINGS = [
        ("n", "new_entry", "Nueva"),
        ("e", "edit_selected", "Editar"),
        ("c", "copy_password", "Copiar"),
        ("o", "open_selected", "Ver"),
        ("d", "delete_selected", "Borrar"),
        ("r", "refresh_table", "Actualizar"),
        ("ctrl+l", "secure_logout", "Cerrar Sesión"),
        ("shift+tab", "focus_command", "Comando"),
        ("question_mark", "show_help", "Ayuda"),
        ("q", "secure_quit", "Salir"),
    ]

    def __init__(self, vault_service, on_logout_callback, **kwargs):
        super().__init__(**kwargs)
        self.vault_service = vault_service
        self.on_logout_callback = on_logout_callback
        self.current_entries = []
        self._clipboard_timer = None
        self._showing_help = False

    def compose(self):
        """Construye el layout de la pantalla."""
        yield Header(show_clock=True)
        with Vertical(id="main-container"):
            yield Label("Mi Bóveda Segura", id="vault-title")
            yield Label(
                "n=nueva | e=editar | c=copia | o=ve | d=borra | r=refresca | ctrl+l=logout | q=sale | ?=ayuda",
                id="vault-help",
            )
            yield Input(placeholder=":comando", id="command-input")
            yield DataTable(id="passwords-table")
        yield Footer()

    def on_mount(self):
        """Se ejecuta al cargar la pantalla. Configuramos la tabla."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("#", "Título", "Usuario", "URL", "Notas")
        self.load_vault_data()
        table.focus()

    def load_vault_data(self):
        """Carga y desencripta los datos usando el servicio."""
        table = self.query_one(DataTable)
        table.clear()

        self.current_entries = self.vault_service.get_all_entries_decrypted()

        for idx, entry in enumerate(self.current_entries):
            table.add_row(
                str(idx + 1),
                entry.get("title", "Sin título"),
                entry.get("username", ""),
                entry.get("url", ""),
                entry.get("notes", ""),
                key=str(idx),
            )

    def _focus_table(self) -> None:
        self.query_one(DataTable).focus()

    def _resolve_selected_index(self) -> int:
        table = self.query_one(DataTable)
        selected_row_key = table.coordinate_to_cell_key(table.cursor_coordinate)
        row_value = selected_row_key.row_key.value
        if row_value is None:
            raise ValueError("No hay fila seleccionada")
        return int(cast(str, row_value))

    def _resolve_index_arg(self, index_arg: str) -> int:
        if not index_arg.isdigit():
            raise ValueError("El índice debe ser un número positivo")

        requested = int(index_arg)
        idx = requested - 1
        if idx < 0 or idx >= len(self.current_entries):
            raise ValueError("Índice fuera de rango")

        return idx

    def _copy_entry_password(self, idx: int) -> None:
        password_to_copy = self.current_entries[idx].get("password", "")
        if not password_to_copy:
            self.notify("La entrada no contiene contraseña", severity="warning")
            return

        pyperclip.copy(password_to_copy)

        self.notify(
            "Contraseña copiada. Se borrará del portapapeles en 15 segundos.",
            timeout=3,
        )

        if self._clipboard_timer is not None:
            self._clipboard_timer.stop()

        self._clipboard_timer = self.set_timer(15.0, self.clear_clipboard)

    def action_copy_password(self):
        try:
            idx = self._resolve_selected_index()
            self._copy_entry_password(idx)
        except Exception:
            self.notify(
                "Selecciona una fila primero con las flechas", severity="warning"
            )

    def action_refresh_table(self) -> None:
        self.load_vault_data()
        self.notify("Bóveda actualizada", severity="information")
        self._focus_table()

    def _command_copy(self, index_arg: str) -> None:
        idx = self._resolve_index_arg(index_arg)
        self._copy_entry_password(idx)

    def _command_open(self, index_arg: str) -> None:
        idx = self._resolve_index_arg(index_arg)
        entry = self.current_entries[idx]
        title = entry.get("title", "Sin título")
        username = entry.get("username", "")
        url = entry.get("url", "")
        notes = entry.get("notes", "")
        self.notify(
            f"[{idx + 1}] {title}\nUsuario: {username or '-'}\nURL: {url or '-'}\nNotas: {notes or '-'}",
            severity="information",
            timeout=8,
        )

    def _command_delete(self, index_arg: str) -> None:
        idx = self._resolve_index_arg(index_arg)
        self._open_delete_confirmation(idx)

    def _open_delete_confirmation(self, idx: int) -> None:
        entry = self.current_entries[idx]
        title = str(entry.get("title", "Sin título"))
        username = str(entry.get("username", ""))
        label = f"[{idx + 1}] {title} ({username or '-'})"

        self.app.push_screen(
            ConfirmDeleteScreen(entry_label=label),
            lambda confirmed: self._handle_delete_confirmation(confirmed, idx),
        )

    def _handle_delete_confirmation(self, confirmed: bool, idx: int) -> None:
        if not confirmed:
            self.notify("Eliminación cancelada", severity="warning")
            self._focus_table()
            return

        if idx < 0 or idx >= len(self.current_entries):
            self.notify(
                "La selección ya no existe. Refrescando tabla.", severity="warning"
            )
            self.load_vault_data()
            self._focus_table()
            return

        entry = self.current_entries[idx]
        credential_id = entry.get("id")
        if not isinstance(credential_id, int):
            self.notify("No se pudo eliminar: ID inválido", severity="error")
            self._focus_table()
            return

        deleted = self.vault_service.delete_entry(credential_id)
        if deleted:
            self.load_vault_data()
            self.notify(f"Entrada {idx + 1} eliminada", severity="information")
            self._focus_table()
        else:
            self.notify("No se pudo eliminar la entrada", severity="error")

    def action_open_selected(self) -> None:
        try:
            idx = self._resolve_selected_index()
            self._command_open(str(idx + 1))
        except Exception:
            self.notify(
                "Selecciona una fila primero con las flechas", severity="warning"
            )

    def action_delete_selected(self) -> None:
        try:
            idx = self._resolve_selected_index()
            self._open_delete_confirmation(idx)
        except Exception:
            self.notify(
                "Selecciona una fila primero con las flechas", severity="warning"
            )

    def action_show_help(self) -> None:
        if self._showing_help:
            return
        self._showing_help = True
        self.notify(
            "Atajos: n=nueva | e=editar | c=copia | o=ver | d=borrar | r=refresca | ctrl+l=logout | q=salir\n"
            "Comandos: :new | :edit N | :copy N | :open N | :del N | :refresh | :logout | :help\n"
            "Navegación: Flechas mueven selección | Enter abre detalle",
            severity="information",
            timeout=10,
        )
        self.set_timer(10.0, self._clear_help_flag)

    def _clear_help_flag(self) -> None:
        self._showing_help = False

    def _handle_entry_result(self, result) -> None:
        if not result:
            self.notify("Operación cancelada", severity="warning")
            self._focus_table()
            return

        credential_id = result.get("id")

        if isinstance(credential_id, int):
            success = self.vault_service.update_entry(
                credential_id=credential_id,
                title=str(result["title"]),
                username_used=str(result["username_used"]),
                password_used=str(result["password_used"]),
                url=str(result["url"]),
                notes=str(result["notes"]),
            )
            if success:
                self.notify("Credencial actualizada", severity="information")
            else:
                self.notify("No se pudo actualizar", severity="error")
        else:
            self.vault_service.add_entry(
                title=str(result["title"]),
                username_used=str(result["username_used"]),
                password_used=str(result["password_used"]),
                url=str(result["url"]),
                notes=str(result["notes"]),
            )
            self.notify("Credencial guardada", severity="information")

        self.load_vault_data()
        self._focus_table()

    def action_new_entry(self) -> None:
        self.app.push_screen(EntryFormScreen(), self._handle_entry_result)

    def action_edit_selected(self) -> None:
        try:
            idx = self._resolve_selected_index()
            entry = self.current_entries[idx]
            self.app.push_screen(
                EntryFormScreen(existing_entry=entry), self._handle_entry_result
            )
        except Exception:
            self.notify(
                "Selecciona una fila primero con las flechas", severity="warning"
            )

    def action_focus_command(self) -> None:
        command_input = self.query_one("#command-input", Input)
        command_input.focus()
        command_input.value = ""

    def clear_clipboard(self):
        """Limpia el portapapeles sobrescribiéndolo con una cadena vacía."""
        pyperclip.copy("")
        self._clipboard_timer = None
        self.notify("Portapapeles limpiado por seguridad.", severity="information")

    def _secure_logout(self):
        self.clear_clipboard()
        self.current_entries.clear()
        self.dismiss()
        self.on_logout_callback()

    def action_secure_logout(self):
        self._secure_logout()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "command-input":
            return

        command = event.value.strip().lower().lstrip(":")
        event.input.value = ""

        if not command:
            self._focus_table()
            return

        parts = command.split()
        cmd = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "copy" and not arg:
            self.action_copy_password()
        elif cmd == "copy" and arg:
            self._command_copy(arg)
        elif cmd == "del" and arg:
            self._command_delete(arg)
        elif cmd == "open" and arg:
            self._command_open(arg)
        elif cmd == "edit" and arg:
            self._command_edit(arg)
        elif cmd == "edit" and not arg:
            self.action_edit_selected()
        elif cmd == "new":
            self.action_new_entry()
        elif cmd == "logout":
            self.action_secure_logout()
        elif cmd == "refresh":
            self.action_refresh_table()
        elif cmd == "help":
            self.action_show_help()
        else:
            self.notify(
                f"Comando no reconocido: {command}. Escribe :help para ver comandos.",
                severity="warning",
            )

        self._focus_table()

    def _command_edit(self, index_arg: str) -> None:
        idx = self._resolve_index_arg(index_arg)
        entry = self.current_entries[idx]
        self.app.push_screen(
            EntryFormScreen(existing_entry=entry), self._handle_entry_result
        )

    def on_key(self, event) -> None:
        if event.key == ":":
            command_input = self.query_one("#command-input", Input)
            command_input.focus()
            command_input.value = ""
            event.stop()
        elif event.key == "enter":
            focused = self.focused
            if focused is None or isinstance(focused, DataTable):
                try:
                    self._resolve_selected_index()
                    self.action_edit_selected()
                    event.stop()
                except Exception:
                    pass

    def action_secure_quit(self):
        self.clear_clipboard()
        self.current_entries.clear()
        self.app.exit()

    def on_unmount(self) -> None:
        self.current_entries.clear()
