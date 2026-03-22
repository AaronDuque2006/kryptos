import re
import threading
import time
from collections import defaultdict

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from core.crypto import VaultCrypto
from db.repository import UserRepository
from models.user import User


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida que la contraseña sea segura.

    Args:
        password: La contraseña a validar.

    Returns:
        Una tupla (es_valida, mensaje_error).
        Si es_valida es True, mensaje_error es una cadena vacía.
        Si es_valida es False, mensaje_error contiene la razón.
    """
    if len(password) < 12:
        return (False, "La contraseña debe tener al menos 12 caracteres.")

    if not re.search(r"[A-Z]", password):
        return (False, "La contraseña debe contener al menos una letra mayúscula.")

    if not re.search(r"[a-z]", password):
        return (False, "La contraseña debe contener al menos una letra minúscula.")

    if not re.search(r"\d", password):
        return (False, "La contraseña debe contener al menos un número.")

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~\\]", password):
        return (False, "La contraseña debe contener al menos un carácter especial.")

    return (True, "")


def validate_username(username: str) -> tuple[bool, str]:
    """
    Valida que el username sea válido.

    Args:
        username: El nombre de usuario a validar.

    Returns:
        Una tupla (es_valido, mensaje_error).
        Si es_valido es True, mensaje_error es una cadena vacía.
        Si es_valido es False, mensaje_error contiene la razón.
    """
    if len(username) < 3:
        return (False, "El nombre de usuario debe tener al menos 3 caracteres.")

    if len(username) > 50:
        return (False, "El nombre de usuario no puede tener más de 50 caracteres.")

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", username):
        return (
            False,
            "El nombre de usuario solo puede contener letras, números y guión bajo, y no puede empezar con un número.",
        )

    return (True, "")


class AuthService:
    """Servicio para manejar la autenticación de usuarios con protección de límite de intentos."""

    # Constantes de límite de intentos
    MAX_FAILED_ATTEMPTS: int = 5
    BLOCK_DURATION_SECONDS: int = 300  # 5 minutes

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        # Argon2 con parámetros seguros por defecto
        self.ph = PasswordHasher()

        # Rate limiting: username -> list of failed attempt timestamps
        self._failed_attempts: dict[str, list[float]] = defaultdict(list)
        self._rate_limit_lock = threading.Lock()

    def _is_rate_limited(self, username: str) -> bool:
        """
        Comprueba si un usuario está actualmente limitado debido a demasiados intentos fallidos.

        Args:
            username: El nombre de usuario a comprobar.

        Returns:
            True si el usuario está limitado, False en caso contrario.
        """
        current_time = time.time()

        with self._rate_limit_lock:
            # Filtrar intentos expirados
            self._failed_attempts[username] = [
                timestamp
                for timestamp in self._failed_attempts[username]
                if current_time - timestamp < self.BLOCK_DURATION_SECONDS
            ]

            # Comprobar si el usuario ha superado el máximo de intentos
            return len(self._failed_attempts[username]) >= self.MAX_FAILED_ATTEMPTS

    def _record_failed_attempt(self, username: str) -> None:
        """
        Registra un intento fallido de autenticación para un usuario.

        Args:
            username: El nombre de usuario que falló la autenticación.
        """
        with self._rate_limit_lock:
            self._failed_attempts[username].append(time.time())

    def _clear_failed_attempts(self, username: str) -> None:
        """
        Limpia todos los intentos fallidos de un usuario tras una autenticación exitosa.

        Args:
            username: El nombre de usuario para limpiar los intentos.
        """
        with self._rate_limit_lock:
            self._failed_attempts[username] = []

    def register(self, username: str, master_password: str) -> User:
        """
        Registra un nuevo usuario con validación y protección de límite de intentos.

        Args:
            username: El nombre de usuario deseado.
            master_password: La contraseña maestra para el usuario.

        Returns:
            El objeto de Usuario recién creado.

        Raises:
            ValueError: Si falla la validación, el nombre de usuario está en uso o está limitado.
        """
        # Validar el nombre de usuario antes de cualquier procesamiento
        username_valid, username_error = validate_username(username)
        if not username_valid:
            raise ValueError(username_error)

        # Validar la fuerza de la contraseña antes de cualquier procesamiento
        password_valid, password_error = validate_password_strength(master_password)
        if not password_valid:
            raise ValueError(password_error)

        # Comprobar el límite de intentos después de la validación
        if self._is_rate_limited(username):
            raise ValueError(
                f"Demasiados intentos fallidos. Intente nuevamente en "
                f"{self.BLOCK_DURATION_SECONDS // 60} minutos."
            )

        if self.user_repo.get_user_by_username(username):
            # Registrar intento fallido (nombre de usuario ya en uso)
            self._record_failed_attempt(username)
            raise ValueError("El nombre de usuario ya está en uso.")

        auth_hash = self.ph.hash(master_password)
        encryption_salt = VaultCrypto.generate_salt()

        new_user = User(
            username=username, auth_hash=auth_hash, encryption_salt=encryption_salt
        )
        created_user = self.user_repo.create_user(new_user)

        # Limpiar cualquier intento fallido anterior en un registro exitoso
        self._clear_failed_attempts(username)

        return created_user

    def login(self, username: str, master_password: str) -> VaultCrypto:
        """
        Autentica un usuario con validación y protección de límite de intentos.

        Args:
            username: El nombre de usuario a autenticar.
            master_password: La contraseña maestra a verificar.

        Returns:
            Una instancia de VaultCrypto inicializada con las credenciales del usuario.

        Raises:
            ValueError: Si falla la validación, las credenciales son incorrectas o están limitadas.
        """
        # Validar el nombre de usuario antes de cualquier procesamiento
        username_valid, username_error = validate_username(username)
        if not username_valid:
            raise ValueError(username_error)

        # Comprobar el límite de intentos después de la validación
        if self._is_rate_limited(username):
            raise ValueError(
                f"Demasiados intentos fallidos. Intente nuevamente en "
                f"{self.BLOCK_DURATION_SECONDS // 60} minutos."
            )

        user = self.user_repo.get_user_by_username(username)
        if not user:
            # Registrar intento fallido para un usuario inexistente
            self._record_failed_attempt(username)
            raise ValueError("Usuario o contraseña incorrectos.")

        try:
            # Se verifica si la contraseña coincide con el hash almacenado
            self.ph.verify(user.auth_hash, master_password)

            # Si Argon2 necesita actualizar sus parámetros de seguridad con el tiempo:
            if self.ph.check_needs_rehash(user.auth_hash):
                # (Opcional) Aquí se podría actualizar el hash en la DB
                pass

        except VerifyMismatchError:
            # Registrar intento fallido por contraseña incorrecta
            self._record_failed_attempt(username)
            raise ValueError("Usuario o contraseña incorrectos.") from None

        # Limpiar intentos fallidos tras inicio de sesión exitoso
        self._clear_failed_attempts(username)

        # Se instancia el motor criptográfico.
        # Esto deriva la clave AES de 256 bits y la mantiene en memoria.
        return VaultCrypto(master_password, user.encryption_salt)
