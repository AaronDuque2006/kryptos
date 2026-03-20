from typing import List, Dict
from db.repositories import CredentialRepository
from core.crypto import VaultCrypto

class VaultService:
    def __init__(self, crypto_engine: VaultCrypto, cred_repo: CredentialRepository, current_user_id: int):
        self.crypto_engine = crypto_engine
        self.cred_repo = cred_repo
        self.current_user_id = current_user_id

    def add_entry(self, title: str, username_used: str, password_used: str, url: str = "", notes: str = ""):
        """
        Empaqueta los datos en un JSON, los encripta y los guarda en la base de datos.
        """
        payload = {
            "username": username_used,
            "password": password_used,
            "url": url,
            "notes": notes
        }
        
        # El motor criptográfico nos devuelve el Nonce y el Payload Encriptado
        nonce, encrypted_payload = self.crypto_engine.encrypt_credential(payload)
        
        # Guardamos en la base de datos usando el repositorio
        self.cred_repo.add_credential(
            user_id=self.current_user_id,
            title=title,
            nonce=nonce,
            encrypted_payload=encrypted_payload
        )

    def get_all_entries_decrypted(self) -> List[Dict]:
        """
        Obtiene todas las credenciales del usuario, las desencripta en memoria 
        y las devuelve como una lista de diccionarios listos para mostrar en la TUI.
        """
        credentials = self.cred_repo.get_credentials_by_user(self.current_user_id)
        decrypted_list = []

        for cred in credentials:
            try:
                # Desencriptamos el payload de cada entrada
                decrypted_payload = self.crypto_engine.decrypt_credential(cred.nonce, cred.encrypted_payload)
                
                # Le inyectamos el ID y el título para que la TUI sepa cómo manejarlos
                decrypted_payload['id'] = cred.id
                decrypted_payload['title'] = cred.title
                
                decrypted_list.append(decrypted_payload)
            except ValueError as e:
                # Si una credencial está corrupta o fue alterada, la saltamos y dejamos un log
                # En un entorno real, notificarías al usuario que esa entrada está comprometida.
                print(f"Error de integridad en credencial ID {cred.id}: {e}")
                
        return decrypted_list

    def delete_entry(self, credential_id: int) -> bool:
        """
        Elimina una entrada de la bóveda.
        """
        return self.cred_repo.delete_credential(credential_id, self.current_user_id)