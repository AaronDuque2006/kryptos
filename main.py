import sys
from pathlib import Path

from core.logging_config import configure_logging

# Aseguramos que Python reconozca nuestros módulos locales independientemente
# de desde dónde se ejecute el script en la terminal.
sys.path.append(str(Path(__file__).parent))

from db.database import get_session, init_db
from db.repository import CredentialRepository, UserRepository
from services.auth_service import AuthService
from services.vault_service import VaultService
from ui.app import PasswordManagerTUI

logger = configure_logging()


def build_vault_service_factory(cred_repo: CredentialRepository):
    """
    Closure/Patrón Factory: Necesitamos instanciar VaultService DESPUÉS
    del login, pero necesitamos inyectarle el cred_repo DESDE el inicio.
    Esta función empaqueta el repositorio y devuelve la fábrica que la TUI usará.
    """

    def factory(crypto_engine, user_id: int) -> VaultService:
        return VaultService(crypto_engine, cred_repo, user_id)

    return factory


def main():
    session = None
    try:
        # 1. Capa de Infraestructura: Inicializar SQLite y asegurar permisos
        init_db()

        # 2. Capa de Acceso a Datos: Crear sesión y Repositorios
        session = get_session()
        user_repo = UserRepository(session)
        cred_repo = CredentialRepository(session)

        # 3. Capa de Lógica de Negocio: Instanciar Servicios
        auth_service = AuthService(user_repo)
        vault_factory = build_vault_service_factory(cred_repo)

        # 4. Capa de Presentación: Instanciar la TUI inyectando dependencias
        app = PasswordManagerTUI(
            auth_service=auth_service, vault_service_factory=vault_factory
        )

        # 5. Arrancar el bucle de eventos (Event Loop) de Textual
        app.run()

    except Exception:
        logger.exception("fatal_startup_error")
    finally:
        # Buena práctica: Asegurarnos de cerrar la conexión a la base de datos al salir
        if session is not None:
            session.close()


if __name__ == "__main__":
    main()
