import json
import os
from collections.abc import Mapping
from typing import cast

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class VaultCrypto:
    def __init__(self, master_password: str, salt: bytes):
        """
        Deriva la clave de encriptación simétrica en el momento en que se instancia.
        La contraseña maestra nunca se guarda como atributo de la clase.
        """
        self._key: bytes | None = self._derive_key(master_password, salt)
        self._aesgcm: AESGCM | None = AESGCM(self._key)

    @staticmethod
    def generate_salt() -> bytes:
        """Genera una sal criptográficamente segura de 16 bytes."""
        return os.urandom(16)

    def _derive_key(self, master_password: str, salt: bytes) -> bytes:
        """
        Deriva una clave AES de 256 bits (32 bytes) usando PBKDF2 con SHA256.
        Se recomiendan al menos 600,000 iteraciones según los estándares actuales de OWASP.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600_000,
        )
        # Se codifica la contraseña a bytes antes de derivar
        return kdf.derive(master_password.encode("utf-8"))

    def encrypt_credential(
        self, payload_dict: Mapping[str, object]
    ) -> tuple[bytes, bytes]:
        """
        Toma un diccionario con las credenciales, lo pasa a JSON y lo encripta.
        Retorna el nonce (vector de inicialización) y el payload encriptado.
        """
        payload_bytes = json.dumps(dict(payload_dict)).encode("utf-8")

        # AES-GCM requiere un Nonce único de 12 bytes por cada encriptación
        nonce = os.urandom(12)

        # El método encrypt añade automáticamente el Tag de autenticación al final del ciphertext
        if self._aesgcm is None:
            raise RuntimeError("Motor criptográfico no inicializado.")

        encrypted_payload = self._aesgcm.encrypt(
            nonce, payload_bytes, associated_data=None
        )

        return nonce, encrypted_payload

    def decrypt_credential(
        self, nonce: bytes, encrypted_payload: bytes
    ) -> dict[str, object]:
        """
        Desencripta el payload y verifica su integridad.
        """
        try:
            if self._aesgcm is None:
                raise RuntimeError("Motor criptográfico no inicializado.")

            decrypted_bytes = self._aesgcm.decrypt(
                nonce, encrypted_payload, associated_data=None
            )
            return cast(dict[str, object], json.loads(decrypted_bytes.decode("utf-8")))
        except InvalidTag:
            # Si el ciphertext fue modificado o la clave es incorrecta, AES-GCM falla aquí.
            raise ValueError(
                "Integridad comprometida o clave incorrecta. No se pudo desencriptar."
            ) from None

    def clear_memory(self) -> None:
        """
        Intenta eliminar las referencias a la clave en memoria.
        Útil para llamar cuando la sesión se bloquea.
        """
        self._key = None
        self._aesgcm = None
