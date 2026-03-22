from dataclasses import dataclass

import pytest

from services.auth_service import AuthService


@dataclass
class UserStub:
    username: str
    auth_hash: str
    encryption_salt: bytes
    id: int | None = None


class UserRepositoryStub:
    def __init__(self) -> None:
        self._users: dict[str, UserStub] = {}
        self._id_sequence = 1

    def create_user(self, user: UserStub) -> UserStub:
        if user.username in self._users:
            raise ValueError("El usuario ya existe")

        user.id = self._id_sequence
        self._id_sequence += 1
        self._users[user.username] = user
        return user

    def get_user_by_username(self, username: str) -> UserStub | None:
        return self._users.get(username)


def test_register_rejects_invalid_username() -> None:
    auth = AuthService(UserRepositoryStub())

    with pytest.raises(ValueError, match="al menos 3 caracteres"):
        auth.register("ab", "StrongPassword123!")


def test_register_rejects_weak_password() -> None:
    auth = AuthService(UserRepositoryStub())

    with pytest.raises(ValueError, match="al menos 12 caracteres"):
        auth.register("usuario_valido", "Weak1!")


def test_login_rate_limits_after_max_failed_attempts() -> None:
    repo = UserRepositoryStub()
    auth = AuthService(repo)
    auth.register("usuario_seguro", "StrongPassword123!")

    for _ in range(auth.MAX_FAILED_ATTEMPTS):
        with pytest.raises(ValueError, match="Usuario o contraseña incorrectos"):
            auth.login("usuario_seguro", "WrongPassword123!")

    with pytest.raises(ValueError, match="Demasiados intentos fallidos"):
        auth.login("usuario_seguro", "WrongPassword123!")


def test_login_rate_limit_expires_after_block_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = UserRepositoryStub()
    auth = AuthService(repo)
    auth.register("usuario_tiempo", "StrongPassword123!")

    fake_time = 10_000.0

    def _time_now() -> float:
        return fake_time

    monkeypatch.setattr("services.auth_service.time.time", _time_now)

    for _ in range(auth.MAX_FAILED_ATTEMPTS):
        with pytest.raises(ValueError, match="Usuario o contraseña incorrectos"):
            auth.login("usuario_tiempo", "WrongPassword123!")

    with pytest.raises(ValueError, match="Demasiados intentos fallidos"):
        auth.login("usuario_tiempo", "StrongPassword123!")

    fake_time += auth.BLOCK_DURATION_SECONDS + 1

    crypto = auth.login("usuario_tiempo", "StrongPassword123!")
    assert crypto is not None
