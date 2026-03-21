from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from db.repository import UserRepository
from core.crypto import VaultCrypto
from models.user import User

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        # Configuramos Argon2 con parámetros seguros por defecto
        self.ph = PasswordHasher()

    def register(self, username: str, master_password: str) -> User:
        if self.user_repo.get_user_by_username(username):
            raise ValueError("El nombre de usuario ya está en uso.")

        auth_hash = self.ph.hash(master_password)
        encryption_salt = VaultCrypto.generate_salt()

        new_user = User(
            username=username,
            auth_hash=auth_hash,
            encryption_salt=encryption_salt
        )
        return self.user_repo.create_user(new_user)

    def login(self, username: str, master_password: str) -> VaultCrypto:
        user = self.user_repo.get_user_by_username(username)
        if not user:
            raise ValueError("Usuario o contraseña incorrectos.")

        try:
            # Verificamos si la contraseña coincide con el hash almacenado
            self.ph.verify(user.auth_hash, master_password)
            
            # Si Argon2 necesita actualizar sus parámetros de seguridad con el tiempo:
            if self.ph.check_needs_rehash(user.auth_hash):
                # (Opcional) Aquí podrías actualizar el hash en la DB
                pass
                
        except VerifyMismatchError:
            raise ValueError("Usuario o contraseña incorrectos.")

        # ¡Login exitoso! Instanciamos el motor criptográfico.
        # Esto deriva la clave AES de 256 bits y la mantiene en memoria.
        return VaultCrypto(master_password, user.encryption_salt)