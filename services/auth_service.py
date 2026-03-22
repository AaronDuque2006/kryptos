import threading
import time
from collections import defaultdict
from typing import Dict, List

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from db.repository import UserRepository
from core.crypto import VaultCrypto
from models.user import User


class AuthService:
    """Service for handling user authentication with rate limiting protection."""

    # Rate limiting constants
    MAX_FAILED_ATTEMPTS: int = 5
    BLOCK_DURATION_SECONDS: int = 300  # 5 minutes

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        # Argon2 con parámetros seguros por defecto
        self.ph = PasswordHasher()

        # Rate limiting: username -> list of failed attempt timestamps
        self._failed_attempts: Dict[str, List[float]] = defaultdict(list)
        self._rate_limit_lock = threading.Lock()

    def _is_rate_limited(self, username: str) -> bool:
        """
        Check if a user is currently rate limited due to too many failed attempts.

        Args:
            username: The username to check.

        Returns:
            True if the user is rate limited, False otherwise.
        """
        current_time = time.time()

        with self._rate_limit_lock:
            # Filter out expired attempts
            self._failed_attempts[username] = [
                timestamp
                for timestamp in self._failed_attempts[username]
                if current_time - timestamp < self.BLOCK_DURATION_SECONDS
            ]

            # Check if user has exceeded max attempts
            return len(self._failed_attempts[username]) >= self.MAX_FAILED_ATTEMPTS

    def _record_failed_attempt(self, username: str) -> None:
        """
        Record a failed authentication attempt for a user.

        Args:
            username: The username that failed authentication.
        """
        with self._rate_limit_lock:
            self._failed_attempts[username].append(time.time())

    def _clear_failed_attempts(self, username: str) -> None:
        """
        Clear all failed attempts for a user after successful authentication.

        Args:
            username: The username to clear attempts for.
        """
        with self._rate_limit_lock:
            self._failed_attempts[username] = []

    def register(self, username: str, master_password: str) -> User:
        """Register a new user with rate limiting protection."""
        # Check rate limiting first
        if self._is_rate_limited(username):
            raise ValueError(
                f"Demasiados intentos fallidos. Intente nuevamente en "
                f"{self.BLOCK_DURATION_SECONDS // 60} minutos."
            )

        if self.user_repo.get_user_by_username(username):
            # Record failed attempt (username already taken)
            self._record_failed_attempt(username)
            raise ValueError("El nombre de usuario ya está en uso.")

        auth_hash = self.ph.hash(master_password)
        encryption_salt = VaultCrypto.generate_salt()

        new_user = User(
            username=username, auth_hash=auth_hash, encryption_salt=encryption_salt
        )
        created_user = self.user_repo.create_user(new_user)

        # Clear any previous failed attempts on successful registration
        self._clear_failed_attempts(username)

        return created_user

    def login(self, username: str, master_password: str) -> VaultCrypto:
        """Authenticate a user with rate limiting protection."""
        # Check rate limiting first - before any credential verification
        if self._is_rate_limited(username):
            raise ValueError(
                f"Demasiados intentos fallidos. Intente nuevamente en "
                f"{self.BLOCK_DURATION_SECONDS // 60} minutos."
            )

        user = self.user_repo.get_user_by_username(username)
        if not user:
            # Record failed attempt for non-existent user
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
            # Record failed attempt for wrong password
            self._record_failed_attempt(username)
            raise ValueError("Usuario o contraseña incorrectos.")

        # Clear failed attempts on successful login
        self._clear_failed_attempts(username)

        # Se instancia el motor criptográfico.
        # Esto deriva la clave AES de 256 bits y la mantiene en memoria.
        return VaultCrypto(master_password, user.encryption_salt)
