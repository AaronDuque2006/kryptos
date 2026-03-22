from core.crypto import VaultCrypto
from core.logging_config import configure_logging
from db.repository import CredentialRepository

logger = configure_logging()


class VaultService:
    TITLE_PLACEHOLDER = "[encrypted-title]"

    def __init__(
        self,
        crypto_engine: VaultCrypto,
        cred_repo: CredentialRepository,
        current_user_id: int,
    ):
        self.crypto_engine = crypto_engine
        self.cred_repo = cred_repo
        self.current_user_id = current_user_id

    def add_entry(
        self,
        title: str,
        username_used: str,
        password_used: str,
        url: str = "",
        notes: str = "",
    ) -> None:
        # Se empaqueta los datos en un JSON, los encripta y los guarda en la base de datos.
        payload = {
            "username": username_used,
            "password": password_used,
            "url": url,
            "notes": notes,
        }

        # Devuelve el Nonce y el Payload Encriptado
        nonce, encrypted_payload = self.crypto_engine.encrypt_credential(payload)
        title_nonce, encrypted_title = self.crypto_engine.encrypt_credential(
            {"title": title}
        )

        # Se guarda en la base de datos
        self.cred_repo.create_credential(
            user_id=self.current_user_id,
            title=self.TITLE_PLACEHOLDER,
            nonce=nonce,
            encrypted_payload=encrypted_payload,
            title_nonce=title_nonce,
            encrypted_title=encrypted_title,
        )

    def get_all_entries_decrypted(self) -> list[dict[str, object]]:
        """
        Se obtiene las credenciales del usuario, las desencripta en memoria
        y las devuelve como una lista de diccionarios para mostrar en la TUI.
        """
        credentials = self.cred_repo.get_credentials_by_user(self.current_user_id)
        decrypted_list = []

        for cred in credentials:
            try:
                # Se desemcripta el payload de cada entrada
                decrypted_payload = self.crypto_engine.decrypt_credential(
                    cred.nonce, cred.encrypted_payload
                )

                decrypted_title = cred.title
                if cred.title_nonce and cred.encrypted_title:
                    try:
                        title_payload = self.crypto_engine.decrypt_credential(
                            cred.title_nonce, cred.encrypted_title
                        )
                        decrypted_title_value = title_payload.get("title")
                        if isinstance(decrypted_title_value, str):
                            decrypted_title = decrypted_title_value
                    except ValueError:
                        pass
                else:
                    try:
                        cred_id = cred.id
                        if cred_id is None:
                            raise ValueError("Credential sin ID")

                        migrated_title_nonce, migrated_encrypted_title = (
                            self.crypto_engine.encrypt_credential({"title": cred.title})
                        )
                        self.cred_repo.update_title_encryption(
                            credential_id=cred_id,
                            user_id=self.current_user_id,
                            placeholder_title=self.TITLE_PLACEHOLDER,
                            title_nonce=migrated_title_nonce,
                            encrypted_title=migrated_encrypted_title,
                        )
                    except Exception:
                        pass

                # Le inyectamos el ID y el título para que la TUI sepa cómo manejarlos
                decrypted_payload["id"] = cred.id
                decrypted_payload["title"] = decrypted_title

                decrypted_list.append(decrypted_payload)
            except ValueError:
                logger.warning(
                    "vault_integrity_error user_id=%s credential_id=%s",
                    self.current_user_id,
                    cred.id,
                )

        return decrypted_list

    def update_entry(
        self,
        credential_id: int,
        title: str,
        username_used: str,
        password_used: str,
        url: str = "",
        notes: str = "",
    ) -> bool:
        # Se actualiza una entrada existente: re-encripta todo el payload y el título.
        credentials = self.cred_repo.get_credentials_by_user(self.current_user_id)
        credential = next((c for c in credentials if c.id == credential_id), None)

        if not credential:
            return False

        payload = {
            "username": username_used,
            "password": password_used,
            "url": url,
            "notes": notes,
        }

        nonce, encrypted_payload = self.crypto_engine.encrypt_credential(payload)
        title_nonce, encrypted_title = self.crypto_engine.encrypt_credential(
            {"title": title}
        )

        credential.nonce = nonce
        credential.encrypted_payload = encrypted_payload
        credential.title = self.TITLE_PLACEHOLDER
        credential.title_nonce = title_nonce
        credential.encrypted_title = encrypted_title

        self.cred_repo.update_credential(credential)
        return True

    def delete_entry(self, credential_id: int) -> bool:
        # Se elimina una entrada de la bóveda.
        return self.cred_repo.delete_credential(credential_id, self.current_user_id)
